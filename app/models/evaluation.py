from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EvaluationRunDB(Base):
    """
    ORM Model for evaluation experiment runs.
    """

    __tablename__ = "evaluation_runs"

    run_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    dataset_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    prompt_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True
    )
    model_config_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("model_configurations.id", ondelete="SET NULL"), nullable=True
    )
    dataset_version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    configuration: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    passed_cases: Mapped[int] = mapped_column(Integer, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    dataset: Mapped[Optional["DatasetDB"]] = relationship("DatasetDB", back_populates="runs")
    prompt: Mapped[Optional["PromptDB"]] = relationship("PromptDB", back_populates="runs")
    model_config: Mapped[Optional["ModelConfigDB"]] = relationship("ModelConfigDB", back_populates="runs")
    results: Mapped[List["EvaluationResultDB"]] = relationship(
        "EvaluationResultDB", back_populates="run", cascade="all, delete-orphan"
    )


class EvaluationResultDB(Base):
    """
    ORM Model for single test case outcomes in an evaluation run.
    """

    __tablename__ = "evaluation_results"

    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    run: Mapped["EvaluationRunDB"] = relationship("EvaluationRunDB", back_populates="results")
    metric_results: Mapped[List["MetricResultDB"]] = relationship(
        "MetricResultDB", back_populates="result", cascade="all, delete-orphan"
    )


class MetricResultDB(Base):
    """
    ORM Model for metric evaluations computed on an evaluation result.
    """

    __tablename__ = "metric_results"

    result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_version: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    judge_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    # Relationships
    result: Mapped["EvaluationResultDB"] = relationship("EvaluationResultDB", back_populates="metric_results")
