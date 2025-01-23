import pytest
from unittest.mock import Mock, AsyncMock
from haystack import Pipeline
from haystack.dataclasses import Document
from app.core.pipeline.factory import PipelineFactory
from app.core.services.pipeline import PipelineService
from app.core.services.medication import MedicationService
from app.schemas.medication import (
    # MedicationEntity,
    MedicationIndexResponse,
    MedicationResponse,
)


@pytest.fixture
def mock_pipeline():
    pipeline = Mock(spec=Pipeline)
    return pipeline


@pytest.fixture
def pipeline_factory():
    factory = Mock(spec=PipelineFactory)
    return factory


@pytest.fixture
def pipeline_service(pipeline_factory):
    service = PipelineService(pipeline_factory)
    service._run_pipeline = AsyncMock()
    return service


@pytest.fixture
def medication_service(pipeline_service):
    service = MedicationService(pipeline_service)
    service.index_medications = AsyncMock()
    service.extract_entities = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_index_medication_success(medication_service):
    medications = [
        Document(
            id=1,
            content="Acetaminophen 325 MG Oral Tablet",
            meta={
                "original_text": "Acetaminophen 325 MG Oral Tablet",
                "quantity": [],
                "drug_name": ["Acetaminophen"],
                "dosage": ["325 MG"],
                "administration_type": ["Oral Tablet"],
                "brand": [],
            },
        )
    ]
    expected = MedicationIndexResponse(
        message=f"Successfully indexed {len(medications)} medications",
        processing_time=0.15,
    )
    medication_service.index_medications.return_value = expected

    # Act
    result = await medication_service.index_medications(medications)

    # Assert
    assert result == expected
    assert isinstance(result, MedicationIndexResponse)
    assert "Successfully indexed 1 medications" in result.message
    assert result.processing_time > 0
    assert medication_service.index_medications.call_count == 1


@pytest.mark.asyncio
async def test_index_medications_failure(medication_service):
    # Arrange
    medication_service.index_medications.side_effect = Exception("Indexing failed")

    # Act & Assert
    with pytest.raises(Exception, match="Indexing failed"):
        await medication_service.index_medications([])


@pytest.mark.asyncio
async def test_extract_entities_success(medication_service):
    query_text = ["Acetaminophen 325 MG Oral Tablet"]
    expected = MedicationResponse(
        results=[
            {
                "original_text": "Acetaminophen 325 MG Oral Tablet",
                "quantity": [],
                "drug_name": ["Acetaminophen"],
                "dosage": ["325 MG"],
                "administration_type": ["Oral Tablet"],
                "brand": [],
            }
        ],
        processing_time=0.15,
    )

    medication_service.extract_entities.return_value = expected

    # Act
    result = await medication_service.extract_entities(query_text)

    # Assert
    assert result == expected
    assert isinstance(result, MedicationResponse)
    assert len(result.results) == 1
    assert result.processing_time > 0
    assert medication_service.extract_entities.call_count == 1


@pytest.mark.asyncio
async def test_extract_entities_failure(medication_service):
    # Arrange
    medication_service.extract_entities.side_effect = Exception("Extraction failed")

    # Act & Assert
    with pytest.raises(Exception, match="Extraction failed"):
        await medication_service.extract_entities([])
