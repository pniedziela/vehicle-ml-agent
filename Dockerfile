FROM python:3.12-slim AS base

WORKDIR /app

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# ── Stage 1: Build React frontend ──────────────────────────────
FROM node:20-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --production=false
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python application ────────────────────────────────
FROM base AS runtime

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy React build output
COPY --from=frontend-build /frontend/dist /app/frontend/dist

# Download sample images (uses Pillow placeholders if network unavailable)
RUN python scripts/download_images.py || true

# Expose port
EXPOSE 8000

# Railway sets PORT env variable; fall back to 8000 for local dev
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
