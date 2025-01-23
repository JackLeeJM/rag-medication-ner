import pytest
from unittest.mock import Mock, AsyncMock
from haystack import Pipeline
from haystack.dataclasses import Document
from app.core.services.pipeline import PipelineService
from app.core.pipeline.factory import PipelineFactory


@pytest.fixture
def pipeline_factory():
    factory = Mock(spec=PipelineFactory)
    factory.create_query_pipeline = AsyncMock(return_value=Mock(spec=Pipeline))
    factory.create_indexing_pipeline = AsyncMock(return_value=Mock(spec=Pipeline))
    return factory


@pytest.fixture
def pipeline_service(pipeline_factory):
    service = PipelineService(pipeline_factory)
    service._run_pipeline = AsyncMock()
    return service


@pytest.fixture
def mock_pipeline():
    pipeline = Mock(spec=Pipeline)
    return pipeline


@pytest.mark.asyncio
async def test_execute_query_pipeline_success(
    pipeline_service, pipeline_factory, mock_pipeline
):
    # Arrange
    query_text = "Acetaminophen 325 MG Oral Tablet"
    expected = {
        "original_text": "Acetaminophen 325 MG Oral Tablet",
        "quantity": [],
        "drug_name": ["Acetaminophen"],
        "dosage": ["325 MG"],
        "administration_type": ["Oral Tablet"],
        "brand": [],
    }
    pipeline_factory.create_query_pipeline.return_value = mock_pipeline
    pipeline_service._run_pipeline.return_value = expected

    # Act
    result = await pipeline_service.execute_query_pipeline(query_text)

    # Assert
    assert result == expected
    pipeline_factory.create_query_pipeline.assert_called_once()
    assert pipeline_service._run_pipeline.call_count == 1


@pytest.mark.asyncio
async def test_execute_index_pipeline_success(
    pipeline_service, pipeline_factory, mock_pipeline
):
    # Arrange
    documents = [
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
    pipeline_factory.create_indexing_pipeline.return_value = mock_pipeline
    pipeline_service._run_pipeline.return_value = None

    # Act
    await pipeline_service.execute_index_pipeline(documents)

    # Assert
    pipeline_factory.create_indexing_pipeline.assert_called_once()
    assert pipeline_service._run_pipeline.call_count == 1
