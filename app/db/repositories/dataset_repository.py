from typing import Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from app.models.dataset import DatasetCaseDB, DatasetDB
from app.schemas.dataset import BenchmarkDataset


class DatasetRepository:
    """
    Repository for persisting and querying benchmark datasets and cases.
    """

    def __init__(self, session: Union[AsyncSession, Session]):
        self.session = session

    def ingest_dataset_sync(self, benchmark_data: BenchmarkDataset) -> DatasetDB:
        """
        Synchronous ingestion of a BenchmarkDataset.
        """
        stmt = select(DatasetDB).where(DatasetDB.version == benchmark_data.metadata.version)
        existing = self.session.execute(stmt).scalar_one_or_none()
        if existing:
            return existing

        dataset_db = DatasetDB(
            name=benchmark_data.metadata.name,
            version=benchmark_data.metadata.version,
            description=benchmark_data.metadata.description,
        )
        self.session.add(dataset_db)
        self.session.flush()

        for rec in benchmark_data.records:
            case_db = DatasetCaseDB(
                dataset_id=dataset_db.id,
                case_id=rec.id,
                category=rec.category.value,
                input=rec.input,
                expected_behavior=rec.expected_behavior,
                reference_answer=rec.reference_answer,
                difficulty=rec.difficulty.value,
                tags=rec.tags,
            )
            self.session.add(case_db)

        self.session.commit()
        return dataset_db

    async def ingest_dataset(self, benchmark_data: BenchmarkDataset) -> DatasetDB:
        """
        Asynchronous ingestion of a BenchmarkDataset.
        """
        return self.ingest_dataset_sync(benchmark_data)

    async def get_by_version(self, version: str) -> Optional[DatasetDB]:
        stmt = (
            select(DatasetDB)
            .options(selectinload(DatasetDB.cases))
            .where(DatasetDB.version == version)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
