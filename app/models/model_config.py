from typing import Any, Dict, List, Optional
from sqlalchemy import Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ModelConfigDB(Base):
    """
    ORM Model for LLM provider generation hyperparameters.
    """

    __tablename__ = "model_configurations"

    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    top_p: Mapped[float] = mapped_column(Float, default=1.0)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    frequency_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    presence_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    extra_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    runs: Mapped[List["EvaluationRunDB"]] = relationship(
        "EvaluationRunDB", back_populates="model_config"
    )
