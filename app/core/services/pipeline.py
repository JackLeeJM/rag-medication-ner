import traceback
from time import perf_counter
from typing import List, Dict, Union, Any
from contextlib import asynccontextmanager
from pydantic import BaseModel
from haystack import Pipeline
from haystack.dataclasses import Document

from app.core.pipeline.factory import PipelineFactory
from app.config.logging import get_logger


logger = get_logger(__name__)


class PipelineMetrics(BaseModel):
    """Metrics for pipeline execution"""

    pipeline_creation_time: float
    execution_time: float
    total_time: float


class PipelineService:
    """Service for managing and executing pipelines"""

    def __init__(self, pipeline_factory: PipelineFactory):
        self._pipeline_factory = pipeline_factory

    @asynccontextmanager
    async def _pipeline_lifecycle(self, pipeline_type: str):
        """Manage pipeline lifecycle and measure performance"""
        start_time = perf_counter()
        pipeline = None
        try:
            if pipeline_type == "query":
                pipeline = await self._pipeline_factory.create_query_pipeline()
            elif pipeline_type == "index":
                pipeline = await self._pipeline_factory.create_indexing_pipeline()
            else:
                raise ValueError(f"Unknown pipeline type: {pipeline_type}")

            creation_time = perf_counter() - start_time
            logger.debug(
                f"{pipeline_type.capitalize()} pipeline created in {creation_time:.2f}s"
            )

            try:
                yield pipeline, creation_time, start_time
            finally:
                # Cleanup could go here if needed
                pass

        except Exception as e:
            logger.error(f"Pipeline lifecycle error: {str(e)}")
            raise

    async def execute_query_pipeline(self, text: str) -> Dict[str, Any]:
        """Execute query pipeline with fresh components"""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Query text must be a non-empty string")

        async with self._pipeline_lifecycle("query") as (
            pipeline,
            creation_time,
            start_time,
        ):
            try:
                pipeline_input = self._create_query_input(text)
                result = await self._run_pipeline(pipeline, pipeline_input)

                # Calculate and log metrics
                metrics = self._calculate_metrics(creation_time, start_time)
                logger.info(
                    "Query pipeline metrics: "
                    f"creation={metrics.pipeline_creation_time:.2f}s, "
                    f"execution={metrics.execution_time:.2f}s, "
                    f"total={metrics.total_time:.2f}s"
                )

                return result

            except Exception as e:
                logger.error(
                    f"Query pipeline execution failed: {str(e)}",
                    extra={"query_text": text[:100]},  # Log truncated query for context
                )
                raise

    async def execute_index_pipeline(
        self, documents: List[Union[Dict, Document]]
    ) -> None:
        """Execute indexing pipeline with fresh components"""
        if not documents:
            raise ValueError("Documents list cannot be empty")

        # Convert dict documents to Document objects if needed
        processed_docs = self._prepare_documents(documents)

        async with self._pipeline_lifecycle("index") as (
            pipeline,
            creation_time,
            start_time,
        ):
            try:
                pipeline_input = self._create_index_input(processed_docs)
                await self._run_pipeline(pipeline, pipeline_input)

                # Calculate and log metrics
                metrics = self._calculate_metrics(creation_time, start_time)
                logger.info(
                    f"Indexed {len(documents)} documents - "
                    f"creation={metrics.pipeline_creation_time:.2f}s, "
                    f"execution={metrics.execution_time:.2f}s, "
                    f"total={metrics.total_time:.2f}s"
                )

            except Exception as e:
                logger.error(
                    f"Index pipeline execution failed: {str(e)}",
                    extra={"document_count": len(documents)},
                )
                raise

    @staticmethod
    def _create_query_input(text: str) -> Dict[str, Dict[str, str]]:
        """Create formatted input for query pipeline"""
        return {
            "sparse_embedder": {"text": text},
            "dense_embedder": {"text": text},
            "reranker": {"query": text},
            "prompt_builder": {"query": text},
        }

    @staticmethod
    def _create_index_input(
        documents: List[Document],
    ) -> Dict[str, Dict[str, List[Document]]]:
        """Create formatted input for index pipeline"""
        return {"sparse_embedder": {"documents": documents}}

    async def _run_pipeline(
        self, pipeline: Pipeline, pipeline_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute pipeline with error handling"""
        try:
            return pipeline.run(pipeline_input)
        except Exception as e:
            logger.error(
                f"Pipeline run failed: {str(e)}.\n{traceback.format_exc()}",
                extra={
                    "pipeline_input": str(pipeline_input)[:200]
                },  # Log truncated input
            )
            raise

    @staticmethod
    def _prepare_documents(documents: List[Union[Dict, Document]]) -> List[Document]:
        """Convert dictionary documents to Document objects if needed"""
        processed_docs = []
        for doc in documents:
            if isinstance(doc, dict):
                processed_docs.append(Document(**doc))
            elif isinstance(doc, Document):
                processed_docs.append(doc)
            else:
                raise ValueError(
                    f"Invalid document type: {type(doc)}. "
                    "Must be either dict or Document"
                )
        return processed_docs

    @staticmethod
    def _calculate_metrics(creation_time: float, start_time: float) -> PipelineMetrics:
        """Calculate pipeline execution metrics"""
        current_time = perf_counter()
        return PipelineMetrics(
            pipeline_creation_time=creation_time,
            execution_time=current_time - start_time - creation_time,
            total_time=current_time - start_time,
        )
