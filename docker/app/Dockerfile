FROM python:3.12.5-slim-bookworm AS python-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Builder stage
FROM python-base AS builder

# Install system dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python -

# Copy project dependency files
WORKDIR $PYSETUP_PATH
COPY pyproject.toml poetry.lock ./

# Install runtime dependencies
RUN poetry install --without dev --no-root

# Final stage
FROM python-base AS final

# Copy virtual environment from builder
COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH

# Copy application code
WORKDIR /app
COPY ./app ./app

EXPOSE 8000

# Use ENTRYPOINT for fixed executable and CMD for configurable flags
ENTRYPOINT ["uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000"]