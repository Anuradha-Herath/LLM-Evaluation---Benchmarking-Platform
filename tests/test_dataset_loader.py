import json
import pytest
from pathlib import Path

from app.core.exceptions import (
    DatasetFileNotFoundError,
    DatasetValidationError,
    DuplicateDatasetIDError,
)
from app.schemas.dataset import BenchmarkDataset
from app.services.dataset_loader import DatasetLoader


@pytest.fixture
def dataset_dir() -> Path:
    """Returns absolute path to datasets directory."""
    return Path(__file__).resolve().parent.parent / "datasets"


def test_load_benchmark_v1_json(dataset_dir: Path):
    """Test loading the official benchmark_v1.json file."""
    json_path = dataset_dir / "benchmark_v1.json"
    dataset = DatasetLoader.load_from_json(json_path)

    assert isinstance(dataset, BenchmarkDataset)
    assert dataset.metadata.version == "v1"
    assert dataset.metadata.total_records == 50
    assert len(dataset.records) == 50

    # Verify deterministic sorting by ID
    record_ids = [r.id for r in dataset.records]
    assert record_ids == sorted(record_ids)


def test_load_benchmark_v1_csv(dataset_dir: Path):
    """Test loading the official benchmark_v1.csv file."""
    csv_path = dataset_dir / "benchmark_v1.csv"
    dataset = DatasetLoader.load_from_csv(csv_path, version="v1")

    assert isinstance(dataset, BenchmarkDataset)
    assert dataset.metadata.version == "v1"
    assert dataset.metadata.total_records == 50
    assert len(dataset.records) == 50

    # Verify deterministic sorting by ID
    record_ids = [r.id for r in dataset.records]
    assert record_ids == sorted(record_ids)


def test_missing_file_raises_exception():
    """Test loading non-existent file raises DatasetFileNotFoundError."""
    with pytest.raises(DatasetFileNotFoundError):
        DatasetLoader.load_from_json("non_existent_file.json")

    with pytest.raises(DatasetFileNotFoundError):
        DatasetLoader.load_from_csv("non_existent_file.csv")


def test_duplicate_ids_detected(tmp_path: Path):
    """Test duplicate IDs trigger DuplicateDatasetIDError."""
    bad_data = {
        "metadata": {"version": "v-dup", "name": "Dup Test", "description": "test", "total_records": 2},
        "records": [
            {
                "id": "CASE-001",
                "category": "factual question",
                "input": "Prompt 1",
                "expected_behavior": "Behavior 1",
            },
            {
                "id": "CASE-001",  # Duplicate ID
                "category": "summarization",
                "input": "Prompt 2",
                "expected_behavior": "Behavior 2",
            },
        ],
    }
    file_path = tmp_path / "dup_test.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(bad_data, f)

    with pytest.raises(DuplicateDatasetIDError) as exc_info:
        DatasetLoader.load_from_json(file_path)

    assert exc_info.value.duplicate_id == "CASE-001"


def test_missing_required_fields(tmp_path: Path):
    """Test missing required field 'expected_behavior' triggers DatasetValidationError."""
    bad_data = [
        {
            "id": "CASE-001",
            "category": "factual question",
            "input": "Prompt 1",
            # missing expected_behavior
        }
    ]
    file_path = tmp_path / "missing_field.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(bad_data, f)

    with pytest.raises(DatasetValidationError):
        DatasetLoader.load_from_json(file_path)


def test_invalid_category_enum(tmp_path: Path):
    """Test invalid category triggers DatasetValidationError."""
    bad_data = [
        {
            "id": "CASE-001",
            "category": "invalid_unknown_category",
            "input": "Prompt 1",
            "expected_behavior": "Behavior 1",
        }
    ]
    file_path = tmp_path / "invalid_cat.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(bad_data, f)

    with pytest.raises(DatasetValidationError):
        DatasetLoader.load_from_json(file_path)


def test_deterministic_ordering(tmp_path: Path):
    """Test records are deterministically sorted by ID regardless of input file order."""
    unsorted_data = [
        {"id": "ZETA-001", "category": "reasoning", "input": "P3", "expected_behavior": "B3"},
        {"id": "ALPHA-001", "category": "reasoning", "input": "P1", "expected_behavior": "B1"},
        {"id": "BETA-001", "category": "reasoning", "input": "P2", "expected_behavior": "B2"},
    ]
    file_path = tmp_path / "unsorted.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(unsorted_data, f)

    dataset = DatasetLoader.load_from_json(file_path)
    loaded_ids = [r.id for r in dataset.records]

    assert loaded_ids == ["ALPHA-001", "BETA-001", "ZETA-001"]
