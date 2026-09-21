from typing import List, Optional
from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DatasetDB(Base):
    """
    ORM Model for benchmark datasets.
    """

    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    cases: Mapped[List["DatasetCaseDB"]] = relationship(
        "DatasetCaseDB", back_populates="dataset", cascade="all, delete-orphan"
    )
    runs: Mapped[List["EvaluationRunDB"]] = relationship(
        "EvaluationRunDB", back_populates="dataset"
    )


class DatasetCaseDB(Base):
    """
    ORM Model for individual test cases in a dataset.
    """

    __tablename__ = "dataset_cases"

    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), default="medium")
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Relationships
    dataset: Mapped["DatasetDB"] = relationship("DatasetDB", back_populates="cases")
