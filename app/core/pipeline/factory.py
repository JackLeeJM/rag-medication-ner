import os
import asyncio
from typing import Tuple
from functools import partial
from concurrent.futures import ThreadPoolExecutor

from haystack import Pipeline
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack.components.builders.prompt_builder import PromptBuilder
from haystack.components.rankers import TransformersSimilarityRanker
from haystack_integrations.components.retrievers.qdrant import QdrantHybridRetriever
from haystack_integrations.components.generators.ollama import OllamaGenerator
from haystack_integrations.components.embedders.fastembed import (
    FastembedTextEmbedder,
    FastembedDocumentEmbedder,
    FastembedSparseTextEmbedder,
    FastembedSparseDocumentEmbedder,
)
from app.config.settings import settings
from app.prompts.template import MEDICATION_NER
from app.core.document_store.factory import DocumentStoreFactory
from app.config.logging import get_logger


logger = get_logger(__name__)


class PipelineFactory:
    def __init__(self):
        self._thread_pool = ThreadPoolExecutor(
            max_workers=max(1, os.cpu_count() * 3 // 4),
            thread_name_prefix="pipeline-init-",
        )

    async def create_indexing_pipeline(self) -> Pipeline:
        """Create indexing pipeline with concurrent component initialization"""
        logger.info("Creating indexing pipeline...")
        try:
            # Initialize document store and both document embedders concurrently
            doc_store, (dense_embedder, sparse_embedder) = await asyncio.gather(
                self._async_init(self._create_doc_store),
                self._async_init(self._create_document_embedders),
            )

            # Initialize document writer after we have the doc_store
            document_writer = await self._async_init(
                partial(self._create_document_writer, doc_store)
            )

            indexing = Pipeline()
            indexing.add_component("sparse_embedder", sparse_embedder)
            indexing.add_component("dense_embedder", dense_embedder)
            indexing.add_component("writer", document_writer)
            indexing.connect("sparse_embedder", "dense_embedder")
            indexing.connect("dense_embedder", "writer")

            logger.success("✨ Indexing pipeline created successfully")
            return indexing

        except Exception:
            logger.exception("Failed to create indexing pipeline")
            raise

    async def create_query_pipeline(self) -> Pipeline:
        """Create query pipeline with concurrent component initialization"""
        logger.info("Creating query pipeline...")
        try:
            # Initialize doc_store and text embedders concurrently
            doc_store, (dense_embedder, sparse_embedder) = await asyncio.gather(
                self._async_init(self._create_doc_store),
                self._async_init(self._create_text_embedders),
            )

            # Initialize remaining components concurrently
            retriever, reranker, generator, prompt_builder = await asyncio.gather(
                self._async_init(partial(self._create_retriever, doc_store)),
                self._async_init(self._create_reranker),
                self._async_init(self._create_generator),
                self._async_init(self._create_prompt_builder),
            )

            querying = Pipeline()
            querying.add_component("sparse_embedder", sparse_embedder)
            querying.add_component("dense_embedder", dense_embedder)
            querying.add_component("retriever", retriever)
            querying.add_component("reranker", reranker)
            querying.add_component("prompt_builder", prompt_builder)
            querying.add_component("llm", generator)

            querying.connect(
                "sparse_embedder.sparse_embedding", "retriever.query_sparse_embedding"
            )
            querying.connect("dense_embedder.embedding", "retriever.query_embedding")
            querying.connect("retriever.documents", "reranker.documents")
            querying.connect("reranker", "prompt_builder")
            querying.connect("prompt_builder", "llm")

            return querying

        except Exception:
            logger.exception("Failed to create query pipeline")
            raise

    async def _async_init(self, factory_func):
        """Run synchronous initialization in thread pool"""
        return await asyncio.get_event_loop().run_in_executor(
            self._thread_pool, factory_func
        )

    def _create_document_embedders(
        self,
    ) -> Tuple[FastembedDocumentEmbedder, FastembedSparseDocumentEmbedder]:
        """Create dense and sparse document embedders"""
        dense_embedder = FastembedDocumentEmbedder(model=settings.EMBEDDING_MODEL_DENSE)
        sparse_embedder = FastembedSparseDocumentEmbedder(
            model=settings.EMBEDDING_MODEL_SPARSE
        )
        return dense_embedder, sparse_embedder

    def _create_text_embedders(
        self,
    ) -> Tuple[FastembedTextEmbedder, FastembedSparseTextEmbedder]:
        """Create dense and sparse text embedders"""
        dense_embedder = FastembedTextEmbedder(model=settings.EMBEDDING_MODEL_DENSE)
        sparse_embedder = FastembedSparseTextEmbedder(
            model=settings.EMBEDDING_MODEL_SPARSE
        )
        return dense_embedder, sparse_embedder

    def _create_doc_store(self):
        doc_factory = DocumentStoreFactory()
        return doc_factory.create_document_store()

    def _create_retriever(self, doc_store):
        return QdrantHybridRetriever(
            document_store=doc_store, top_k=settings.RETRIEVER_TOP_K
        )

    def _create_reranker(self):
        reranker = TransformersSimilarityRanker(
            model=settings.RERANKER_MODEL, top_k=settings.RERANKER_TOP_K
        )
        reranker.warm_up()
        return reranker

    def _create_generator(self):
        return OllamaGenerator(
            model=settings.OLLAMA_MODEL,
            url=settings.OLLAMA_API_URL,
            generation_kwargs={
                "temperature": settings.OLLAMA_TEMPERATURE,
                "num_predict": settings.OLLAMA_MAX_TOKENS,
                "num_ctx": settings.OLLAMA_MAX_CONTEXT,
            },
        )

    def _create_prompt_builder(self):
        return PromptBuilder(template=MEDICATION_NER)

    def _create_document_writer(self, doc_store):
        return DocumentWriter(
            document_store=doc_store, policy=DuplicatePolicy.OVERWRITE
        )
