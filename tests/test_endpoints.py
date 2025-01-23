import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_medication_service
from app.schemas.medication import (
    MedicationResponse,
    MedicationIndexResponse,
    MedicationEntity,
)
from app.config.settings import settings


@pytest.fixture
def mock_medication_service():
    service = Mock()
    service.extract_entities = AsyncMock()
    service.index_medications = AsyncMock()
    service.index_medications.return_value = MedicationIndexResponse(
        message="Successfully indexed medications", processing_time=0.5
    )
    service.extract_entities.return_value = MedicationResponse(
        results=[], processing_time=0.5
    )
    return service


@pytest.fixture
def client(mock_medication_service):
    async def get_mock_medication_service():
        return mock_medication_service

    app.dependency_overrides[get_medication_service] = get_mock_medication_service
    return TestClient(app)


@pytest.mark.asyncio
async def test_extract_medications_success(client, mock_medication_service):
    # Arrange
    input_texts = ["Acetaminophen 325 MG Oral Tablet"]
    mock_response = MedicationResponse(
        results=[
            MedicationEntity(
                original_text="Acetaminophen 325 MG Oral Tablet",
                drug_name=["Acetaminophen"],
                dosage=["325 MG"],
                quantity=[],
                administration_type=["Oral Tablet"],
                brand=[],
            )
        ],
        processing_time=0.5,
    )
    mock_medication_service.extract_entities.return_value = mock_response

    # Act
    response = client.post(
        f"{settings.API_V1_STR}/extract", json={"texts": input_texts}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["processing_time"] == 0.5
    assert len(response.json()["results"]) == 1
    mock_medication_service.extract_entities.assert_called_once_with(input_texts)


@pytest.mark.asyncio
async def test_index_medications_success(client, mock_medication_service):
    # Arrange
    medications = [
        MedicationEntity(
            original_text="Acetaminophen 325 MG Oral Tablet",
            drug_name=["Acetaminophen"],
            dosage=["325 MG"],
            quantity=[],
            administration_type=["Oral Tablet"],
            brand=[],
        )
    ]
    mock_response = MedicationIndexResponse(
        message="Successfully indexed 1 medication", processing_time=0.5
    )
    mock_medication_service.index_medications.return_value = mock_response

    # Act
    response = client.post(
        f"{settings.API_V1_STR}/index",
        json={"medications": [med.model_dump() for med in medications]},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["processing_time"] == 0.5
    assert "Successfully indexed" in response.json()["message"]
    mock_medication_service.index_medications.assert_called_once()


@pytest.mark.asyncio
async def test_extract_medications_empty_request(client):
    # Arrange - empty request

    # Act
    response = client.post(f"{settings.API_V1_STR}/extract", json={"texts": []})

    # Assert
    assert response.status_code == 422  # FastAPI validation error


@pytest.mark.asyncio
async def test_index_medications_empty_request(client):
    # Arrange - empty request

    # Act
    response = client.post(f"{settings.API_V1_STR}/index", json={"medications": []})

    # Assert
    assert response.status_code == 422  # FastAPI validation error
