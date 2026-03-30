"""REST API endpoints for the vehicle ML agent."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.service import agent, AgentResponse
from app.auth.service import authenticate, create_access_token, require_auth
from app.classifier.service import classifier, ClassificationResult
from app.config import settings
from app.db.models import VehicleImage
from app.db.session import get_session
from app.limiter import limiter
from app import storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])


# ── Request / Response schemas 

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QuestionRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Pytanie nie może być puste.")
        return v.strip()

    model_config = {"json_schema_extra": {"examples": [{"question": "Znajdź wszystkie samochody, których właścicielem był Jan Kowalski."}]}}


class ClassifyResponse(BaseModel):
    predicted_class: str
    confidence: float
    imagenet_label: str


class AgentResponseSchema(BaseModel):
    question: str
    generated_sql: str
    results: list[dict]
    row_count: int
    error: str | None = None


# ── Helpers 

async def _enrich_with_classifications(
    rows: list[dict],
    session: AsyncSession,
) -> list[dict]:
    """Enrich query results with image classification for each vehicle."""
    enriched = []
    for row in rows:
        row_dict = dict(row)
        vehicle_id = row_dict.get("vehicle_id")

        if vehicle_id is not None:
            img_result = await session.execute(
                select(VehicleImage).where(VehicleImage.vehicle_id == vehicle_id)
            )
            images = img_result.scalars().all()

            if images:
                raw_url = images[0].image_url
                print(raw_url)
                tmp_path: Path | None = None

                try:
                    if raw_url.startswith("http://") or raw_url.startswith("https://"):
                        # S3 or any remote URL — download to a temp file first
                        tmp_path = storage.download_to_temp(raw_url)
                        image_path: Path = tmp_path
                    else:
                        image_path = Path(raw_url)
                        if not image_path.is_absolute():
                            image_path = settings.SAMPLE_IMAGES_DIR / raw_url

                    if image_path.exists():
                        cls_result = classifier.classify(image_path)
                        row_dict["klasyfikacja_obrazu"] = cls_result.predicted_class
                        row_dict["pewność_klasyfikacji"] = cls_result.confidence
                        row_dict["etykieta_imagenet"] = cls_result.imagenet_label
                    else:
                        row_dict["klasyfikacja_obrazu"] = "brak pliku obrazu"
                except Exception as e:
                    logger.warning("Classification failed for vehicle %s: %s", vehicle_id, e)
                    row_dict["klasyfikacja_obrazu"] = "błąd klasyfikacji"
                finally:
                    if tmp_path:
                        tmp_path.unlink(missing_ok=True)
            else:
                row_dict["klasyfikacja_obrazu"] = "brak obrazu w bazie"

        enriched.append(row_dict)
    return enriched


# ── Endpoints 


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Authenticate and receive a JWT bearer token."""
    if not authenticate(req.username, req.password):
        raise HTTPException(status_code=401, detail="Nieprawidłowa nazwa użytkownika lub hasło.")
    return LoginResponse(access_token=create_access_token())


@router.post("/classify", response_model=ClassifyResponse)
async def classify_image(
    file: UploadFile = File(...),
    _: str = Depends(require_auth),
):
    """Upload an image and get the vehicle classification result."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    content = await file.read()

    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result: ClassificationResult = classifier.classify(tmp_path)
    except Exception as e:
        logger.error("Classification error: %s", e)
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)

    # # Upload to S3 if configured
    # s3_url: str | None = None
    # if storage.s3_enabled():
    #     try:
    #         key = f"uploads/{file.filename or 'upload.jpg'}"
    #         s3_url = storage.upload(content, key, file.content_type or "image/jpeg")
    #         logger.info("Uploaded to S3: %s", s3_url)
    #     except Exception as e:
    #         logger.warning("S3 upload failed (continuing without it): %s", e)

    return ClassifyResponse(
        predicted_class=result.predicted_class,
        confidence=result.confidence,
        imagenet_label=result.imagenet_label,
    )


@router.post("/ask", response_model=AgentResponseSchema)
async def ask_question(
    request: Request,
    req: QuestionRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: str = Depends(require_auth),
):
    """Ask a natural language question about the vehicle database.

    Rate-limited per IP to keep OpenAI costs in check (configurable via RATE_LIMIT_ASK).
    """
    response: AgentResponse = await agent.execute(req.question, session)

    if response.error:
        return AgentResponseSchema(
            question=response.question,
            generated_sql=response.generated_sql,
            results=response.results,
            row_count=response.row_count,
            error=response.error,
        )

    enriched_results = await _enrich_with_classifications(response.results, session)

    return AgentResponseSchema(
        question=response.question,
        generated_sql=response.generated_sql,
        results=enriched_results,
        row_count=response.row_count,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
