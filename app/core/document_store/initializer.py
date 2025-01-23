from typing import Optional
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from app.core.document_store.factory import DocumentStoreFactory
from app.utils.retry import retry_with_logging
from app.config.logging import get_logger


logger = get_logger(__name__)


class DocumentStoreInitializer:
    """Handles initialization and testing of document store connection"""

    def __init__(self):
        self._test_store: Optional[QdrantDocumentStore] = None

    @retry_with_logging
    async def test_connection(self) -> None:
        """Test document store connection with retry logic"""
        try:
            factory = DocumentStoreFactory()
            test_store = factory.create_document_store()
            # Test the connection by performing a simple operation
            _ = test_store.count_documents()
            self._test_store = test_store
            logger.info("Successfully tested Qdrant document store connection")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Clean up test connection"""
        if self._test_store:
            try:
                await self._test_store.client.close()
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
