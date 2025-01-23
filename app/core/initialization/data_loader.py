import json
from pathlib import Path
from typing import List

from app.core.pipeline.factory import PipelineFactory
from app.schemas.medication import MedicationEntity
from app.utils.common import create_index_documents
from app.config.logging import get_logger


logger = get_logger(__name__)


class DataLoader:
    """Handles loading of initial data into document store"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.few_shot_path = self.data_dir / "few_shot_examples.json"
        self.eval_path = self.data_dir / "eval_dataset.json"

    async def load_initial_data(self) -> None:
        """Load initial data into document store"""
        pipeline_factory = PipelineFactory()
        try:
            medications = self._load_medication_data()
            documents = create_index_documents(medications)

            index_pipeline = await pipeline_factory.create_indexing_pipeline()
            logger.success("✨ Pipelines initialized successfully")

            index_pipeline.run({"sparse_embedder": {"documents": documents}})
            logger.success("✨ Initial medication data loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load data into document store. Error: {e}")
            raise

    def load_eval_data(self) -> None:
        """Load evaluation data."""
        try:
            if not self.eval_path.exists():
                logger.warning(f"Initial data file not found: {self.eval_path}")
                return []

            raw_data = self._load_json(self.eval_path)

            # Validate and convert to MedicationEntity objects
            medications = [MedicationEntity(**item) for item in raw_data]

            logger.info(f"Loaded {len(medications)} medications from {self.eval_path}")
            return medications
        except Exception as e:
            logger.error(f"Failed to load testing data. Error: {e}")

    def _load_json(self, path: Path) -> List[MedicationEntity]:
        """Load JSON data from a file"""
        try:
            with open(path, mode="r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON data. Error: {e}")
            raise

    def _load_medication_data(self) -> List[MedicationEntity]:
        """Load medication data from JSON file"""
        try:
            if not self.few_shot_path.exists():
                logger.warning(f"Initial data file not found: {self.few_shot_path}")
                return []

            raw_data = self._load_json(self.few_shot_path)

            # Validate and convert to MedicationEntity objects
            medications = [MedicationEntity(**item) for item in raw_data]

            logger.info(
                f"Loaded {len(medications)} medications from {self.few_shot_path}"
            )
            return medications

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in initial data file: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error loading initial data: {str(e)}")
            raise
