from fastapi import Depends
from app.core.pipeline.factory import PipelineFactory
from app.core.services.pipeline import PipelineService
from app.core.services.medication import MedicationService


def get_pipeline_factory() -> PipelineFactory:
    """Get pipeline factory."""
    return PipelineFactory()


async def get_pipeline_service(
    pipeline_factory: PipelineFactory = Depends(get_pipeline_factory),
) -> PipelineService:
    """Get pipeline service with all required dependencies."""
    return PipelineService(pipeline_factory=pipeline_factory)


async def get_medication_service(
    pipeline_service: PipelineService = Depends(get_pipeline_service),
) -> MedicationService:
    """Get medication service with pipeline service dependency"""
    return MedicationService(pipeline_service)
