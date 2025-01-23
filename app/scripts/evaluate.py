import asyncio
from app.core.initialization.data_loader import DataLoader
from app.core.evaluation.evaluator import Evaluator
from app.config.logging import get_logger


logger = get_logger(__name__)


async def main() -> None:
    # Load evaluation data
    data_loader = DataLoader()
    eval_data = data_loader.load_eval_data()

    # Initialize evaluator
    evaluator = Evaluator()

    # Evaluate the model
    result = await evaluator.run(eval_data[:10])

    logger.info(f"Evaluation Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
