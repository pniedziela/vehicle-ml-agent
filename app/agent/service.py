"""AI Agent: translates natural language questions into SQL queries using OpenAI GPT-4o-mini.

Architecture:
    1. User asks a question in natural language (Polish or English).
    2. The agent sends the question + DB schema to GPT-4o-mini.
    3. GPT-4o-mini returns a SQL SELECT query.
    4. The agent executes the query against the SQLite database.
    5. Results are returned as a list of dicts, optionally enriched with
       image classification results.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

# ── Database schema description for the LLM ────────────────────────────────

DB_SCHEMA = """
Database: vehicle dealership system (PostgreSQL / SQLite compatible)

Table: vehicles
  - vehicle_id    INTEGER PRIMARY KEY
  - brand         TEXT NOT NULL          -- e.g. "Toyota", "BMW", "MAN"
  - model         TEXT NOT NULL          -- e.g. "Corolla", "X5", "TGS"
  - year          INTEGER NOT NULL       -- production year
  - price         FLOAT NOT NULL         -- price in PLN
  - is_available  BOOLEAN DEFAULT TRUE   -- true = available, false = sold
  - vehicle_type  TEXT                   -- "car", "suv", "truck", "motorcycle"

Table: owners
  - owner_id      INTEGER PRIMARY KEY
  - first_name    TEXT NOT NULL
  - last_name     TEXT NOT NULL
  - city          TEXT
  - email         TEXT
  - phone         TEXT

Table: transaction_history
  - transaction_id   INTEGER PRIMARY KEY
  - vehicle_id       INTEGER REFERENCES vehicles(vehicle_id)
  - buyer_id         INTEGER REFERENCES owners(owner_id)
  - seller_id        INTEGER REFERENCES owners(owner_id)  -- NULL if first purchase
  - transaction_date DATE NOT NULL
  - price            FLOAT NOT NULL

Table: vehicle_images
  - image_id      INTEGER PRIMARY KEY
  - vehicle_id    INTEGER REFERENCES vehicles(vehicle_id)
  - image_url     TEXT NOT NULL          -- file path to image
""".strip()

SYSTEM_PROMPT = f"""You are a SQL query generator for a vehicle database.
Given a user's question in natural language (Polish or English), generate a single
valid standard SQL SELECT query that answers the question.

RULES:
- Output ONLY the SQL query – no explanations, no markdown fences, no comments.
- Use only SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, ALTER, etc.
- Use standard SQL compatible with both PostgreSQL and SQLite.
- Always include vehicle_id in the SELECT when querying vehicles (needed for image lookup).
- Use JOINs when the question involves owners, transactions, or images.
- For questions about vehicle owners, join through transaction_history:
  an owner "owns" a vehicle if they are the buyer in the most recent transaction for that vehicle.
- If the user asks about "samochody" / "pojazdy" / "auta", query the vehicles table.
- Prefer Polish-friendly column aliases (e.g. AS marka, AS model, AS cena).
- Do NOT add a trailing semicolon.

DATABASE SCHEMA:
{DB_SCHEMA}

EXAMPLE:
User: "Znajdź wszystkie samochody, których właścicielem był Jan Kowalski."
SQL: SELECT v.vehicle_id, v.brand AS marka, v.model AS model, v.year AS rok, v.price AS cena FROM vehicles v JOIN transaction_history t ON v.vehicle_id = t.vehicle_id JOIN owners o ON t.buyer_id = o.owner_id WHERE o.first_name = 'Jan' AND o.last_name = 'Kowalski'
"""


@dataclass
class AgentResponse:
    """Response from the AI agent."""

    question: str
    generated_sql: str
    results: list[dict]
    row_count: int
    error: str | None = None
    classifications: list[dict] = field(default_factory=list)


class SQLAgent:
    """Natural-language-to-SQL agent powered by OpenAI GPT-4o-mini."""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def generate_sql(self, question: str) -> str:
        """Send the question to GPT-4o-mini and get back a SQL query."""
        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=0,
            max_tokens=512,
            timeout=30,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
        )
        raw = response.choices[0].message.content or ""
        sql = self._clean_sql(raw)
        logger.info("Generated SQL: %s", sql)
        return sql

    async def execute(self, question: str, session: AsyncSession) -> AgentResponse:
        """Full pipeline: question → SQL → execute → results."""
        try:
            sql = await self.generate_sql(question)
        except Exception as e:
            logger.error("LLM error: %s", e)
            return AgentResponse(
                question=question,
                generated_sql="",
                results=[],
                row_count=0,
                error=f"Błąd generowania SQL: {e}",
            )

        # Safety check: only allow SELECT
        if not self._is_safe_query(sql):
            return AgentResponse(
                question=question,
                generated_sql=sql,
                results=[],
                row_count=0,
                error="Wygenerowane zapytanie nie jest bezpieczne (tylko SELECT jest dozwolony).",
            )

        try:
            result = await session.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            logger.error("SQL execution error: %s", e)
            return AgentResponse(
                question=question,
                generated_sql=sql,
                results=[],
                row_count=0,
                error=f"Błąd wykonania SQL: {e}",
            )

        return AgentResponse(
            question=question,
            generated_sql=sql,
            results=rows,
            row_count=len(rows),
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _clean_sql(raw: str) -> str:
        """Strip markdown fences, whitespace, and trailing semicolons from LLM output."""
        sql = raw.strip()
        # Remove ```sql ... ``` fences
        sql = re.sub(r"^```(?:sql)?\s*", "", sql)
        sql = re.sub(r"\s*```$", "", sql)
        sql = sql.strip()
        # Strip a single trailing semicolon, GPT often appends one and
        # the safety check rightly blocks multi-statement queries.
        sql = sql.rstrip(";").strip()
        return sql

    @staticmethod
    def _is_safe_query(sql: str) -> bool:
        """Safety check - only single SELECT queries allowed."""
        normalized = sql.strip().upper()
        if not normalized.startswith("SELECT"):
            return False
        # Block multi-statement injection (e.g. SELECT 1; DROP TABLE)
        if ";" in normalized:
            return False
        # Block SQL comments that could hide malicious payloads
        if "--" in normalized or "/*" in normalized:
            return False
        dangerous = {
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
            "TRUNCATE", "EXEC", "EXECUTE",
            "PRAGMA", "ATTACH", "DETACH",   # SQLite-specific attacks
            "REPLACE", "GRANT", "REVOKE",
        }
        tokens = set(re.findall(r"\b[A-Z]+\b", normalized))
        return not tokens.intersection(dangerous)


# Singleton
agent = SQLAgent()
