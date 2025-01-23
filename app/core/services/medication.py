import json
import time
import uuid
from typing import List, Dict, Any

from app.core.services.pipeline import PipelineService
from app.utils.common import create_index_documents
from app.schemas.medication import (
    MedicationEntity,
    MedicationResponse,
    MedicationIndexResponse,
)
from app.config.logging import get_logger


logger = get_logger(__name__)


class MedicationService:
    """Service for processing medication-related operations"""

    def __init__(self, pipeline_service: PipelineService):
        self._pipeline_service = pipeline_service

    async def index_medications(
        self, medications: List[MedicationEntity]
    ) -> MedicationIndexResponse:
        """
        Index medication entities into the vector database.

        Args:
            medications: List of medication entities to index

        Returns:
            IndexingResult containing indexing operation metadata

        Raises:
            IndexingError: If indexing operation fails
        """
        request_id = str(uuid.uuid4())
        logger.info(
            f"Starting indexing operation for request {request_id} "
            f"with {len(medications)} medications"
        )

        start_time = time.perf_counter()

        try:
            # Convert medication entities to indexable documents
            documents = create_index_documents(medications)

            # Execute indexing pipeline
            await self._pipeline_service.execute_index_pipeline(documents)

            processing_time = time.perf_counter() - start_time

            logger.info(
                f"Request {request_id}: Successfully indexed {len(medications)} "
                f"medications in {processing_time:.2f} seconds"
            )

            return MedicationIndexResponse(
                message=f"Successfully indexed {len(medications)} medications",
                processing_time=processing_time,
            )

        except Exception as e:
            logger.exception(f"Request {request_id}: Failed to index medications. {e}")
            raise

    async def extract_entities(self, texts: List[str]) -> MedicationResponse:
        """
        Extract medication entities from a list of texts.

        Args:
            texts: List of medication strings to process

        Returns:
            ProcessingResult containing extracted entities and metadata

        Raises:
            EntityExtractionError: If extraction fails
        """
        request_id = str(uuid.uuid4())
        logger.info(f"Starting entity extraction for request {request_id}")

        start_time = time.perf_counter()
        results: List[MedicationEntity] = []

        try:
            for idx, text in enumerate(texts, 1):
                logger.debug(
                    f"Request {request_id}: Processing text {idx}/{len(texts)}: {text}"
                )

                # Execute pipeline and extract entities
                entities = await self._process_single_text(text, request_id, idx)
                results.append(entities)

            processing_time = time.perf_counter() - start_time

            logger.info(
                f"Request {request_id}: Completed processing {len(texts)} texts "
                f"in {processing_time:.2f} seconds"
            )

            return MedicationResponse(results=results, processing_time=processing_time)

        except Exception as e:
            logger.exception(
                f"Request {request_id}: Error during entity extraction. {e}"
            )
            raise

    async def _process_single_text(
        self, text: str, request_id: str, idx: int
    ) -> MedicationEntity:
        """Process a single medication text and extract entities"""
        try:
            # Execute query pipeline
            response = await self._pipeline_service.execute_query_pipeline(text)

            # Parse LLM response
            extracted_data = self._parse_llm_response(response, text)

            logger.debug(
                f"Request {request_id}: Successfully extracted entities from text {idx}"
            )

            return MedicationEntity(**extracted_data)

        except Exception as e:
            logger.error(
                f"Request {request_id}: Failed to process text {idx}: {str(e)}"
            )
            # Return empty entity on failure
            return MedicationEntity(original_text=text)

    def _parse_llm_response(
        self, llm_response: str, original_text: str
    ) -> Dict[str, Any]:
        """Parse LLM response into structured data"""
        try:
            extracted = json.loads(llm_response["llm"]["replies"][0])
            extracted["original_text"] = original_text
            return extracted
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return {
                "original_text": original_text,
                "quantity": [],
                "drug_name": [],
                "dosage": [],
                "administration_type": [],
                "brand": [],
            }
