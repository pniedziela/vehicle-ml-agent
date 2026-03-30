"""Tests for the SQL agent service."""

import pytest
from app.agent.service import SQLAgent


class TestSQLAgent:
    """Tests for SQL safety and cleaning utilities."""

    def test_clean_sql_strips_fences(self):
        raw = "```sql\nSELECT * FROM vehicles;\n```"
        # _clean_sql now strips trailing semicolons too
        assert SQLAgent._clean_sql(raw) == "SELECT * FROM vehicles"

    def test_clean_sql_plain(self):
        raw = "  SELECT v.brand FROM vehicles v  "
        assert SQLAgent._clean_sql(raw) == "SELECT v.brand FROM vehicles v"

    def test_clean_sql_strips_trailing_semicolon(self):
        """GPT often appends a semicolon — _clean_sql should strip it."""
        raw = "SELECT * FROM vehicles;"
        assert SQLAgent._clean_sql(raw) == "SELECT * FROM vehicles"

    def test_clean_sql_no_fences(self):
        raw = "SELECT 1"
        assert SQLAgent._clean_sql(raw) == "SELECT 1"

    def test_is_safe_select(self):
        assert SQLAgent._is_safe_query("SELECT * FROM vehicles") is True

    def test_is_safe_select_with_join(self):
        sql = (
            "SELECT v.brand, o.first_name FROM vehicles v "
            "JOIN transaction_history t ON v.vehicle_id = t.vehicle_id "
            "JOIN owners o ON t.buyer_id = o.owner_id"
        )
        assert SQLAgent._is_safe_query(sql) is True

    def test_unsafe_drop(self):
        assert SQLAgent._is_safe_query("DROP TABLE vehicles") is False

    def test_unsafe_delete(self):
        assert SQLAgent._is_safe_query("DELETE FROM vehicles WHERE 1=1") is False

    def test_unsafe_insert(self):
        assert SQLAgent._is_safe_query("INSERT INTO vehicles VALUES (1,'a','b',2020,1000,1,'car')") is False

    def test_unsafe_update(self):
        assert SQLAgent._is_safe_query("UPDATE vehicles SET price=0") is False

    def test_unsafe_alter(self):
        assert SQLAgent._is_safe_query("ALTER TABLE vehicles ADD COLUMN hack TEXT") is False

    def test_not_select_start(self):
        assert SQLAgent._is_safe_query("EXPLAIN SELECT * FROM vehicles") is False

    # ── Semicolon injection tests ──────────────────────────────────────

    def test_unsafe_semicolon_injection(self):
        """Multi-statement injection should be blocked."""
        assert SQLAgent._is_safe_query("SELECT 1; DROP TABLE vehicles") is False

    def test_unsafe_semicolon_at_end(self):
        """Even a trailing semicolon is blocked to prevent edge cases."""
        assert SQLAgent._is_safe_query("SELECT * FROM vehicles;") is False

    def test_unsafe_semicolon_with_delete(self):
        """Compound statement with DELETE after SELECT should be blocked."""
        assert SQLAgent._is_safe_query("SELECT * FROM vehicles; DELETE FROM vehicles") is False

    # ── SQLite-specific attack vectors ─────────────────────────────────

    def test_unsafe_pragma(self):
        """PRAGMA can leak or modify SQLite internals."""
        assert SQLAgent._is_safe_query("SELECT 1") is True  # sanity
        assert SQLAgent._is_safe_query("PRAGMA table_info(vehicles)") is False

    def test_unsafe_attach(self):
        """ATTACH can mount external databases."""
        assert SQLAgent._is_safe_query("ATTACH DATABASE ':memory:' AS hack") is False

    def test_unsafe_sql_comment_dash(self):
        """SQL comments can hide payloads."""
        assert SQLAgent._is_safe_query("SELECT * FROM vehicles -- DROP TABLE vehicles") is False

    def test_unsafe_sql_comment_block(self):
        """Block comments can hide payloads."""
        assert SQLAgent._is_safe_query("SELECT * FROM vehicles /* DROP TABLE */") is False
