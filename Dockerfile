# Multi-stage lightweight Python Dockerfile for Silver Analisis Engine & API
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production runtime stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Copy installed python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application source code and web assets
COPY src/ ./src/
COPY api/ ./api/
COPY web/ ./web/
COPY outputs/ ./outputs/
COPY scripts/ ./scripts/

# Expose FastAPI default port
EXPOSE 8000

# Healthcheck for orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/live || exit 1

# Start FastAPI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
