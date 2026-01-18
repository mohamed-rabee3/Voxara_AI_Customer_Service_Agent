# ============================================
# Voara Voice Agent Backend - Production Dockerfile
# OPTIMIZED FOR CORE2DUO E8400 (No SSE4/AVX support)
# ============================================
FROM python:3.11-slim

# Set environment variables for Python and Poetry
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# CRITICAL: Force NumPy to build for old CPUs (SSE2 only, no SSE4/AVX)
# Core2Duo E8400 only supports SSE2/SSE3/SSSE3
ENV NPY_DISABLE_CPU_FEATURES="AVX AVX2 AVX512F AVX512CD AVX512_SKX AVX512_CLX AVX512_CNL AVX512_ICL SSE41 SSE42 POPCNT"
ENV CFLAGS="-march=core2 -mno-sse4.1 -mno-sse4.2 -mno-avx -mno-avx2"

# Add poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies including OpenBLAS for NumPy
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev dependencies for production)
RUN poetry install --only main --no-root

# CRITICAL: AFTER poetry install, force reinstall NumPy from source
# This ensures NumPy is built for Core2Duo without SSE4/AVX
RUN pip uninstall -y numpy && \
    pip install --no-cache-dir --no-binary :all: "numpy<2.0" --force-reinstall

# Verify NumPy works (will fail fast if CPU incompatible)
RUN python -c "import numpy; print(f'NumPy {numpy.__version__} loaded successfully')"

# Copy application code
COPY . .

# Install the project itself
RUN poetry install --only main

# Expose port
EXPOSE 8000

# Health check with longer startup time for slower servers
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default command - API server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
