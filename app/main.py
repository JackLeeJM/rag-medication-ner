from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.endpoints import medication
from app.config.logging import get_logger
from app.config.settings import settings

from app.core.document_store.initializer import DocumentStoreInitializer
from app.core.initialization.data_loader import DataLoader


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application"""
    logger.info("Initializing application components...")

    initializer = DocumentStoreInitializer()
    data_loader = DataLoader()

    try:
        # Test connection to document store
        await initializer.test_connection()

        if initializer._test_store is not None:
            # Loads initial data
            await data_loader.load_initial_data()

            yield
    except Exception:
        logger.exception("Failed to initialize pipelines")
        raise
    finally:
        logger.info("Shutting down application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Include routers
app.include_router(medication.router, prefix=settings.API_V1_STR, tags=["Medication"])


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}
