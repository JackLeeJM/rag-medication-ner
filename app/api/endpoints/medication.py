import traceback

from fastapi import APIRouter, Depends
from app.core.services.medication import MedicationService
from app.api.dependencies import get_medication_service
from app.config.logging import get_logger
from app.schemas.medication import (
    MedicationRequest,
    MedicationResponse,
    MedicationIndexRequest,
    MedicationIndexResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/extract", response_model=MedicationResponse)
async def extract_medications(
    request: MedicationRequest,
    medication_service: MedicationService = Depends(get_medication_service),
):
    try:
        result = await medication_service.extract_entities(request.texts)
        return MedicationResponse(
            results=result.results, processing_time=result.processing_time
        )
    except Exception as e:
        logger.error(
            f"An error was encountered while extracting entities: {e}.\n{traceback.format_exc()}"
        )
        raise


@router.post("/index", response_model=MedicationIndexResponse)
async def index_medications(
    request: MedicationIndexRequest,
    medication_service: MedicationService = Depends(get_medication_service),
):
    """
    Index medication entities into the vector database for future retrieval.
    """
    try:
        result = await medication_service.index_medications(request.medications)
        return MedicationIndexResponse(
            message=result.message, processing_time=result.processing_time
        )
    except Exception as e:
        logger.error(
            f"An error was encountered while indexing medications: {e}.\n{traceback.format_exc()}"
        )
        raise
