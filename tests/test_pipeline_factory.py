import pytest
from unittest.mock import Mock, AsyncMock, patch
from haystack import Pipeline
from haystack.components.writers import DocumentWriter
from haystack.components.builders.prompt_builder import PromptBuilder
from haystack.components.rankers import TransformersSimilarityRanker
from haystack.document_stores.types import DuplicatePolicy
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantHybridRetriever
from haystack_integrations.components.generators.ollama import OllamaGenerator
from haystack_integrations.components.embedders.fastembed import (
    FastembedTextEmbedder,
    FastembedDocumentEmbedder,
    FastembedSparseTextEmbedder,
    FastembedSparseDocumentEmbedder,
)
from app.core.pipeline.factory import PipelineFactory


@pytest.fixture
def mock_logger():
    with patch("app.core.pipeline.factory.logger") as mock:
        yield mock


@pytest.fixture
def mock_document_store():
    mock = Mock(spec=QdrantDocumentStore)
    mock.count_documents = Mock(return_value=0)
    mock.client = AsyncMock()
    return mock


@pytest.fixture
def mock_document_store_factory(mock_document_store):
    with patch("app.core.pipeline.factory.DocumentStoreFactory") as mock:
        instance = mock.return_value
        instance.create_document_store.return_value = mock_document_store
        yield mock


@pytest.fixture
def mock_settings():
    with patch("app.core.pipeline.factory.settings") as mock:
        mock.EMBEDDING_MODEL_DENSE = "BAAI/bge-small-en-v1.5"
        mock.EMBEDDING_MODEL_SPARSE = "Qdrant/bm42-all-minilm-l6-v2-attentions"
        mock.RETRIEVER_TOP_K = 4
        mock.RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        mock.RERANKER_TOP_K = 2
        mock.OLLAMA_MODEL = "llama3.2:latest"
        mock.OLLAMA_API_URL = "http://localhost:11434"
        mock.OLLAMA_TEMPERATURE = 0.0
        mock.OLLAMA_MAX_TOKENS = 150
        mock.OLLAMA_MAX_CONTEXT = 2048
        yield mock


@pytest.fixture
def factory(mock_settings):
    return PipelineFactory()


def get_pipeline_components(pipeline: Pipeline):
    """Helper function to extract components detail from pipeline."""
    return [*pipeline.to_dict().get("components")]


def get_pipeline_connections(pipeline: Pipeline):
    """Helper function to extract connections detail from pipeline."""
    return [
        (conn["sender"], conn["receiver"])
        for conn in pipeline.to_dict().get("connections")
    ]


@pytest.mark.asyncio
async def test_create_indexing_pipeline_success(
    factory, mock_document_store_factory, mock_logger
):
    """Test successful creation of indexing pipeline"""
    # Act
    pipeline = await factory.create_indexing_pipeline()
    components = get_pipeline_components(pipeline)

    # Assert
    assert isinstance(pipeline, Pipeline)
    assert "sparse_embedder" in components
    assert "dense_embedder" in components
    assert "writer" in components

    # Verify component connections
    connections = get_pipeline_connections(pipeline)
    assert ("sparse_embedder.documents", "dense_embedder.documents") in connections
    assert ("dense_embedder.documents", "writer.documents") in connections

    mock_logger.success.assert_called_once_with(
        "✨ Indexing pipeline created successfully"
    )


@pytest.mark.asyncio
async def test_create_query_pipeline_success(
    factory, mock_document_store_factory, mock_logger
):
    """Test successful creation of query pipeline"""
    # Act
    pipeline = await factory.create_query_pipeline()
    components = get_pipeline_components(pipeline)

    # Assert
    assert isinstance(pipeline, Pipeline)
    assert "sparse_embedder" in components
    assert "dense_embedder" in components
    assert "retriever" in components
    assert "reranker" in components
    assert "prompt_builder" in components
    assert "llm" in components

    # Verify component connections
    connections = get_pipeline_connections(pipeline)
    assert (
        "sparse_embedder.sparse_embedding",
        "retriever.query_sparse_embedding",
    ) in connections
    assert ("dense_embedder.embedding", "retriever.query_embedding") in connections
    assert ("retriever.documents", "reranker.documents") in connections
    assert ("reranker.documents", "prompt_builder.documents") in connections
    assert ("prompt_builder.prompt", "llm.prompt") in connections


@pytest.mark.asyncio
async def test_indexing_pipeline_creation_failure(
    factory, mock_document_store_factory, mock_logger
):
    """Test handling of indexing pipeline creation failure"""
    # Arrange
    mock_document_store_factory.return_value.create_document_store.side_effect = (
        Exception("Connection failed")
    )

    # Act & Assert
    with pytest.raises(Exception):
        await factory.create_indexing_pipeline()

    mock_logger.exception.assert_called_once_with("Failed to create indexing pipeline")


@pytest.mark.asyncio
async def test_query_pipeline_creation_failure(
    factory, mock_document_store_factory, mock_logger
):
    """Test handling of query pipeline creation failure"""
    # Arrange
    mock_document_store_factory.return_value.create_document_store.side_effect = (
        Exception("Connection failed")
    )

    # Act & Assert
    with pytest.raises(Exception):
        await factory.create_query_pipeline()

    mock_logger.exception.assert_called_once_with("Failed to create query pipeline")


def test_create_document_embedders(factory):
    """Test creation of document embedders"""
    # Act
    dense_embedder, sparse_embedder = factory._create_document_embedders()

    # Assert
    assert isinstance(dense_embedder, FastembedDocumentEmbedder)
    assert isinstance(sparse_embedder, FastembedSparseDocumentEmbedder)
    assert dense_embedder.model_name == "BAAI/bge-small-en-v1.5"
    assert sparse_embedder.model_name == "Qdrant/bm42-all-minilm-l6-v2-attentions"


def test_create_text_embedders(factory):
    """Test creation of text embedders"""
    # Act
    dense_embedder, sparse_embedder = factory._create_text_embedders()

    # Assert
    assert isinstance(dense_embedder, FastembedTextEmbedder)
    assert isinstance(sparse_embedder, FastembedSparseTextEmbedder)
    assert dense_embedder.model_name == "BAAI/bge-small-en-v1.5"
    assert sparse_embedder.model_name == "Qdrant/bm42-all-minilm-l6-v2-attentions"


def test_create_retriever(factory, mock_document_store):
    """Test creation of retriever"""
    # Act
    retriever = factory._create_retriever(mock_document_store)

    # Assert
    assert isinstance(retriever, QdrantHybridRetriever)
    assert retriever._document_store is mock_document_store
    assert retriever._top_k == 4


def test_create_reranker(factory):
    """Test creation of reranker"""
    # Act
    reranker = factory._create_reranker()

    # Assert
    assert isinstance(reranker, TransformersSimilarityRanker)
    assert reranker.top_k == 2


def test_create_generator(factory):
    """Test creation of generator"""
    # Act
    generator = factory._create_generator()

    # Assert
    assert isinstance(generator, OllamaGenerator)
    assert generator.model == "llama3.2:latest"
    assert generator.url == "http://localhost:11434"


def test_create_prompt_builder(factory):
    """Test creation of prompt builder"""
    # Act
    builder = factory._create_prompt_builder()

    # Assert
    assert isinstance(builder, PromptBuilder)


def test_create_document_writer(factory, mock_document_store):
    """Test creation of document writer"""
    # Act
    writer = factory._create_document_writer(mock_document_store)

    # Assert
    assert isinstance(writer, DocumentWriter)
    assert writer.document_store is mock_document_store
    assert writer.policy is DuplicatePolicy.OVERWRITE
