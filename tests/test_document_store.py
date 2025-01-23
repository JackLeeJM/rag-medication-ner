from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from app.config.settings import settings
from app.core.document_store.factory import DocumentStoreFactory


def test_init_document_store():
    # Call the function to get the document store instance
    doc_factory = DocumentStoreFactory()
    doc_store = doc_factory.create_document_store()

    # Assert that the returned object is an instance of QdrantDocumentStore
    assert isinstance(doc_store, QdrantDocumentStore)

    # Assert specific attributes or configurations if necessary
    assert doc_store.host is settings.QDRANT_HOST
    assert doc_store.port is settings.QDRANT_PORT
    assert (
        doc_store.recreate_index is False
    )  # Assuming recreate_index is a boolean attribute
    assert doc_store.return_embedding is True
    assert doc_store.use_sparse_embeddings is True
    assert doc_store.wait_result_from_api is True
    assert doc_store.sparse_idf is True
    assert doc_store.embedding_dim is settings.QDRANT_EMBEDDING_DIM
