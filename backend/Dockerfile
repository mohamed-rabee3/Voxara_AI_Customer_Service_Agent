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

# Add poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# CRITICAL: Install NumPy 1.24.4 FIRST - this is the last version with SSE2 baseline
# NumPy 1.25+ requires SSE4.1/SSE4.2 which Core2Duo doesn't have
RUN pip install "numpy==1.24.4"

# Install dependencies (no dev dependencies for production)
# Poetry will see numpy is already installed and use it
RUN poetry install --only main --no-root

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
