import pytest
from unittest.mock import Mock
from app.api.dependencies import (
    get_pipeline_factory,
    get_pipeline_service,
    get_medication_service,
)
from app.core.pipeline.factory import PipelineFactory
from app.core.services.pipeline import PipelineService
from app.core.services.medication import MedicationService


def test_get_pipeline_factory():
    factory = get_pipeline_factory()
    assert isinstance(factory, PipelineFactory)


@pytest.mark.asyncio
async def test_get_pipeline_service():
    # Arrange
    pipeline_factory = Mock(spec=PipelineFactory)

    # Act
    service = await get_pipeline_service(pipeline_factory)

    # Assert
    assert isinstance(service, PipelineService)
    assert service._pipeline_factory == pipeline_factory


@pytest.mark.asyncio
async def test_get_medication_service():
    # Arrange
    pipeline_service = Mock(spec=PipelineService)

    # Act
    service = await get_medication_service(pipeline_service)

    # Assert
    assert isinstance(service, MedicationService)
    assert service._pipeline_service == pipeline_service
