# Show available recipes
default:
    @just --list

# Install all dependencies with poetry
install:
    poetry install
    poetry run pre-commit install

# Copy environment variables for local development
env-local:
    cp .env.local .env

# Copy environment variables for standard development
env:
    cp .env.sample .env

# Update dependencies
update:
    poetry update

# Add a new dependency
add pkg:
    poetry add {{pkg}}

# Add a new development dependency
add-dev pkg:
    poetry add --group dev {{pkg}}

# Format code with ruff
fmt:
    poetry run ruff format .
    poetry run ruff check . --fix

# Check code without fixing
check:
    poetry run ruff format --check .
    poetry run ruff check .

# Run evaluations with standard metrics
eval:
    poetry run python -m app.scripts.evaluate

# Run tests with pytest
test:
    poetry run pytest

# Run tests with coverage
test-cov:
    poetry run pytest --cov=app --cache-clear --cov-report=term-missing --cov-report=html

# Run the FastAPI application locally
run:
    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run docker compose services for local development
up-local:
    docker-compose -f docker-compose.local.yml up -d

# Build and run docker compose services with Ollama running on CPU
up-cpu:
    docker-compose -f docker-compose.cpu.yml up --build -d

# Build and run docker compose services
up:
    docker-compose up --build -d

# Stop docker compose services
down:
    docker compose down

# Export dependencies to requirements.txt (useful for Docker)
export-requirements:
    poetry export -f requirements.txt --output requirements.txt --without-hashes
    poetry export -f requirements.txt --output requirements-dev.txt --without-hashes --with dev

# Clean up python cache files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type f -name ".coverage" -delete
    find . -type f -name "coverage.xml" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    find . -type d -name "*.egg" -exec rm -rf {} +
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name ".ruff_cache" -exec rm -rf {} +

# Run all quality checks (format, lint, test)
check-all: fmt check test

# Create a new Python virtual environment
venv:
    poetry env use python3.11
    poetry install
