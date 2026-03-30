"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file.

    On Railway, set DATABASE_URL to use a mounted volume:
        sqlite+aiosqlite:////data/vehicle_database.db
    Or for PostgreSQL:
        postgresql+asyncpg://user:pass@host:5432/dbname
    """

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Database – default is local SQLite; set DATABASE_URL env var for PostgreSQL.
    # Railway provides: postgres://user:pass@host:5432/railway
    # (auto-converted to postgresql+asyncpg:// at runtime)
    DATABASE_URL: str = "sqlite+aiosqlite:///./vehicle_database.db"

    # Server port – Railway sets PORT automatically
    PORT: int = 8000

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    SAMPLE_IMAGES_DIR: Path = BASE_DIR / "sample_images"

    # Classifier
    CLASSIFIER_MODEL: str = "mobilenet_v2"
    CLASSIFIER_CONFIDENCE_THRESHOLD: float = 0.1

    # Auth – single recruiter account
    AUTH_USERNAME: str = "recruiter"
    AUTH_PASSWORD: str = "changeme"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    # Rate limiting (slowapi format: "N/period", e.g. "30/hour")
    RATE_LIMIT_ASK: str = "30/hour"

    # S3-compatible storage (RunPod, AWS S3, Cloudflare R2, etc.)
    # Leave blank to use local file storage instead.
    S3_ENDPOINT_URL: str = ""   # e.g. https://your-pod.runpod.net:9000
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
