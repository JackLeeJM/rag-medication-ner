import pytest
from unittest.mock import Mock, AsyncMock, patch
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from app.core.document_store.initializer import DocumentStoreInitializer


@pytest.fixture
def mock_logger():
    with patch("app.core.document_store.initializer.logger") as mock:
        yield mock


@pytest.fixture
def mock_factory():
    with patch("app.core.document_store.initializer.DocumentStoreFactory") as mock:
        yield mock


@pytest.fixture
def mock_document_store():
    mock = Mock(spec=QdrantDocumentStore)
    mock.count_documents = Mock(return_value=0)
    mock.client = AsyncMock()
    return mock


@pytest.fixture
async def initializer():
    init = DocumentStoreInitializer()
    yield init
    await init.cleanup()


@pytest.mark.asyncio
async def test_successful_connection(
    initializer, mock_factory, mock_document_store, mock_logger
):
    """Test successful connection to document store"""
    # Arrange
    mock_factory.return_value.create_document_store.return_value = mock_document_store

    # Act
    await initializer.test_connection()

    # Assert
    mock_factory.return_value.create_document_store.assert_called_once()
    mock_document_store.count_documents.assert_called_once()
    mock_logger.info.assert_called_once_with(
        "Successfully tested Qdrant document store connection"
    )
    assert initializer._test_store == mock_document_store


@pytest.mark.asyncio
async def test_connection_failure(initializer, mock_factory, mock_logger):
    """Test handling of connection failure"""
    # Arrange
    error_msg = "Connection refused"
    mock_factory.return_value.create_document_store.side_effect = Exception(error_msg)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await initializer.test_connection()

    assert str(exc_info.value) == error_msg
    mock_logger.error.assert_called_once_with(
        f"Failed to connect to Qdrant: {error_msg}"
    )


@pytest.mark.asyncio
async def test_cleanup_success(initializer, mock_document_store, mock_logger):
    """Test successful cleanup of document store connection"""
    # Arrange
    initializer._test_store = mock_document_store

    # Act
    await initializer.cleanup()

    # Assert
    mock_document_store.client.close.assert_called_once()
    assert not mock_logger.error.called


@pytest.mark.asyncio
async def test_cleanup_failure(initializer, mock_document_store, mock_logger):
    """Test handling of cleanup failure"""
    # Arrange
    error_msg = "Cleanup failed"
    initializer._test_store = mock_document_store
    mock_document_store.client.close.side_effect = Exception(error_msg)

    # Act
    await initializer.cleanup()

    # Assert
    mock_document_store.client.close.assert_called_once()
    mock_logger.error.assert_called_once_with(f"Error during cleanup: {error_msg}")


@pytest.mark.asyncio
async def test_cleanup_no_store(initializer, mock_logger):
    """Test cleanup when no store exists"""
    # Arrange
    initializer._test_store = None

    # Act
    await initializer.cleanup()

    # Assert
    assert not mock_logger.error.called
