import json
from time import perf_counter
from pydantic import BaseModel
from typing import Dict, Any, List, Tuple
from app.core.pipeline.factory import PipelineFactory
from app.schemas.medication import MedicationEntity
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from app.config.logging import get_logger


logger = get_logger(__name__)


class EvaluationOutput(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float


class Evaluator:
    def __init__(self):
        self._factory = PipelineFactory()

    def _format_llm_response(self, response: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Format the LLM response into usable format for evaluation."""
        try:
            answer = json.loads(response["llm"]["replies"][0])
            _contexts = [doc.meta for doc in response["reranker"]["documents"]]
            contexts = [
                f"Query: {ctx["original_text"]}\nAnswer: {ctx}" for ctx in _contexts
            ]
            return answer, contexts
        except Exception as e:
            logger.error(f"Error formatting LLM response: {e}")
            raise

    def _compute_metrics(self, dataset: Dict[str, float]) -> EvaluationOutput:
        """Compute standard ML evaluation metrics for the test dataset."""
        try:
            generated_answer = dataset["answer"]
            ground_truth = dataset["ground_truth"]

            # Compare JSON objects and output True/False
            boolean_comparisons = [
                gen == gt for gen, gt in zip(generated_answer, ground_truth)
            ]

            # Convert boolean comparisons to binary labels (True -> 1, False -> 0)
            y_pred = [int(b) for b in boolean_comparisons]
            y_true = [1] * len(
                generated_answer
            )  # Since ground truth is considered "correct", it is all 1s

            # Compute metrics
            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            return EvaluationOutput(
                accuracy=accuracy, precision=precision, recall=recall, f1_score=f1
            )
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            return EvaluationOutput(
                accuracy=None, precision=None, recall=None, f1_score=None
            )

    async def run(self, test_data: List[MedicationEntity]) -> EvaluationOutput:
        """Run the evaluation on the provided test dataset."""
        eval_dataset = {"question": [], "answer": [], "context": [], "ground_truth": []}
        try:
            start = perf_counter()
            for _input in test_data:
                query = _input.original_text
                query_pipeline = await self._factory.create_query_pipeline()
                llm_response = query_pipeline.run(
                    data={
                        "sparse_embedder": {"text": query},
                        "dense_embedder": {"text": query},
                        "reranker": {"query": query},
                        "prompt_builder": {"query": query},
                    },
                    include_outputs_from={"reranker"},
                )
                answers, contexts = self._format_llm_response(llm_response)
                eval_dataset["question"].append(query)
                eval_dataset["answer"].append(answers)
                eval_dataset["context"].extend(contexts)
                eval_dataset["ground_truth"].append(_input.model_dump())
            elapsed = perf_counter() - start
            logger.info("Evaluation completed successfully.")
            logger.info(
                f"Evaluation took {elapsed:.2f} seconds for processing {len(test_data)} medication text."
            )

            return self._compute_metrics(eval_dataset)
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            raise
