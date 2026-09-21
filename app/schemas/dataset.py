from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class DatasetCategory(str, Enum):
    FACTUAL_QUESTION = "factual question"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    INSTRUCTION_FOLLOWING = "instruction following"
    REASONING = "reasoning"
    CUSTOMER_SUPPORT = "customer support"
    SAFETY_SENSITIVE = "safety-sensitive response"


class DatasetRecord(BaseModel):
    """
    Schema representing a single benchmark evaluation case.
    """

    id: str = Field(..., description="Unique case identifier (e.g. 'CASE-001').")
    category: DatasetCategory = Field(
        ..., description="Category classification for the evaluation case."
    )
    input: str = Field(..., description="The prompt or input text provided to the LLM.")
    expected_behavior: str = Field(
        ..., description="Description of expected LLM behavior or evaluation criteria."
    )
    reference_answer: Optional[str] = Field(
        default=None, description="Gold standard or ideal reference output."
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM, description="Task difficulty rating."
    )
    tags: List[str] = Field(
        default_factory=list, description="Searchable tags or sub-domain labels."
    )

    @field_validator("id", "input", "expected_behavior")
    @classmethod
    def string_must_not_be_empty(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"Field '{info.field_name}' must not be empty or whitespace.")
        return value.strip()


class DatasetMetadata(BaseModel):
    """
    Metadata information for a benchmark dataset release.
    """

    version: str = Field(..., description="Semantic version string (e.g. 'v1' or '1.0.0').")
    name: str = Field(..., description="Dataset name.")
    description: str = Field(..., description="Description of the dataset contents.")
    total_records: int = Field(..., ge=0, description="Total count of evaluation cases.")


class BenchmarkDataset(BaseModel):
    """
    Complete benchmark dataset model including metadata and record payload.
    """

    metadata: DatasetMetadata
    records: List[DatasetRecord]
