from typing import List, Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PromptDB(Base):
    """
    ORM Model for system prompts and template versions.
    """

    __tablename__ = "prompts"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    runs: Mapped[List["EvaluationRunDB"]] = relationship(
        "EvaluationRunDB", back_populates="prompt"
    )
