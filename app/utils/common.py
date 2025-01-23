from typing import List
from haystack.dataclasses import Document
from app.schemas.medication import MedicationEntity
from app.config.logging import get_logger


logger = get_logger(__name__)


def create_index_documents(medications: List[MedicationEntity]) -> List[Document]:
    """Creates Haystack Document-formatted medication data for indexing."""
    try:
        return [
            Document(id=str(index), content=med.original_text, meta=med)
            for index, med in enumerate(medications)
        ]
    except Exception as e:
        logger.error(f"Error converting medications to Documents: {str(e)}")
        raise
