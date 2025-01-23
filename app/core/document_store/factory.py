from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from app.config.settings import settings
from app.config.logging import get_logger


logger = get_logger(__name__)


class DocumentStoreFactory:
    """Factory for creating fresh document store instances"""

    def create_document_store(self) -> QdrantDocumentStore:
        """Create a new instance of QdrantDocumentStore with configured parameters"""
        logger.info("Creating new QdrantDocumentStore instance")
        return QdrantDocumentStore(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            recreate_index=False,  # Set to True only for development
            return_embedding=True,
            use_sparse_embeddings=True,
            wait_result_from_api=True,
            sparse_idf=True,
            embedding_dim=settings.QDRANT_EMBEDDING_DIM,
        )
