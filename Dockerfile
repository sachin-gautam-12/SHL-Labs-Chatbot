# ==============================================================================
# Conversational SHL Assessment Recommender - Multi-stage Production Dockerfile
# ==============================================================================

# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system utilities required for compiling native wheels (e.g., FAISS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install dependencies into a separate wheels directory
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final runtime container
FROM python:3.12-slim AS runner

WORKDIR /workspace

# Install runtime dependencies (libgomp for FAISS openmp execution)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

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
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run FastAPI using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
