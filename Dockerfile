# ==============================================================================
# Conversational SHL Assessment Recommender - Multi-stage Production Dockerfile
# ==============================================================================

# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install dependencies into a separate wheels directory
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final runtime container
FROM python:3.12-slim AS runner

WORKDIR /workspace

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy project source folders
COPY app/ ./app/
COPY data/ ./data/
COPY frontend/ ./frontend/
COPY tests/ ./tests/
COPY README.md .

# Set Environment Variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
# We don't hardcode PORT to 8000 here to allow Render to inject it, but set a default
ENV PORT=8000

# Expose port (Optional, Render routes dynamically)
EXPOSE 8000

# Run FastAPI using uvicorn. Note we use sh -c to evaluate $PORT at runtime.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
