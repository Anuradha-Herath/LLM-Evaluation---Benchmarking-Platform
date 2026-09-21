import logging
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.db.repositories.dataset_repository import DatasetRepository
from app.db.session import SyncSessionLocal, sync_engine
from app.models.base import Base
from app.models.model_config import ModelConfigDB
from app.models.prompt import PromptDB
from app.services.dataset_loader import DatasetLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scripts.seed_db")


def seed() -> None:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=sync_engine)

    dataset_path = root_dir / "datasets" / "benchmark_v1.json"
    logger.info(f"Loading benchmark dataset from {dataset_path}...")
    benchmark_dataset = DatasetLoader.load_from_json(dataset_path)

    with SyncSessionLocal() as session:
        repo = DatasetRepository(session)
        dataset_db = repo.ingest_dataset_sync(benchmark_dataset)
        logger.info(f"Successfully seeded dataset '{dataset_db.name}' (v{dataset_db.version}) into database.")

        # Seed default prompt template if missing
        from sqlalchemy import select
        res = session.execute(select(PromptDB).where(PromptDB.name == "Default System Prompt"))
        if not res.scalar_one_or_none():
            prompt_db = PromptDB(
                name="Default System Prompt",
                version="v1.0.0",
                system_prompt="You are a helpful, precise, and accurate AI assistant.",
            )
            session.add(prompt_db)
            logger.info("Seeded default system prompt.")

        # Seed default model configurations if missing
        res = session.execute(
            select(ModelConfigDB).where(ModelConfigDB.provider == "mock", ModelConfigDB.model == "mock-model-v1")
        )
        if not res.scalar_one_or_none():
            config_db = ModelConfigDB(
                provider="mock",
                model="mock-model-v1",
                temperature=0.7,
                top_p=1.0,
                max_tokens=1024,
            )
            session.add(config_db)
            logger.info("Seeded default model configuration for mock provider.")

        session.commit()
    logger.info("Database seeding complete!")


if __name__ == "__main__":
    seed()
