import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

from pydantic import ValidationError

from app.core.exceptions import (
    DatasetFileNotFoundError,
    DatasetValidationError,
    DuplicateDatasetIDError,
)
from app.schemas.dataset import BenchmarkDataset, DatasetMetadata, DatasetRecord

logger = logging.getLogger("app.services.dataset_loader")


class DatasetLoader:
    """
    Service responsible for loading, validating, and serving evaluation datasets.
    Guarantees schema compliance, unique ID validation, and deterministic ordering.
    """

    @classmethod
    def load_from_json(cls, file_path: Union[str, Path]) -> BenchmarkDataset:
        """
        Loads and validates a benchmark dataset from a JSON file.

        :param file_path: Path to the JSON file.
        :return: BenchmarkDataset instance containing metadata and sorted records.
        """
        path = Path(file_path)
        if not path.is_file():
            raise DatasetFileNotFoundError(f"Dataset file not found at path: '{path}'")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            raise DatasetValidationError(f"Failed to parse JSON file '{path}': {exc}") from exc

        if isinstance(data, dict) and "records" in data:
            metadata_dict = data.get("metadata", {})
            version = metadata_dict.get("version", path.stem.replace("benchmark_", ""))
            name = metadata_dict.get("name", f"Benchmark Dataset {version}")
            description = metadata_dict.get(
                "description", "General Business & Customer Support Benchmark"
            )
            raw_records = data["records"]
        elif isinstance(data, list):
            version = path.stem.replace("benchmark_", "")
            name = f"Benchmark Dataset {version}"
            description = "General Business & Customer Support Benchmark"
            raw_records = data
        else:
            raise DatasetValidationError(
                f"Invalid JSON format in '{path}'. Expected a list of records or dict with 'records' key."
            )

        validated_records = cls._validate_and_sort_records(raw_records, str(path))

        metadata = DatasetMetadata(
            version=version,
            name=name,
            description=description,
            total_records=len(validated_records),
        )

        return BenchmarkDataset(metadata=metadata, records=validated_records)

    @classmethod
    def load_from_csv(
        cls, file_path: Union[str, Path], version: str = "v1"
    ) -> BenchmarkDataset:
        """
        Loads and validates a benchmark dataset from a CSV file.

        :param file_path: Path to the CSV file.
        :param version: Optional dataset version identifier.
        :return: BenchmarkDataset instance containing metadata and sorted records.
        """
        path = Path(file_path)
        if not path.is_file():
            raise DatasetFileNotFoundError(f"Dataset CSV file not found at path: '{path}'")

        raw_records: List[Dict[str, Any]] = []
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    record_dict = dict(row)
                    # Parse tags from comma-separated string or JSON string
                    tags_raw = record_dict.get("tags", "")
                    if isinstance(tags_raw, str):
                        tags_raw_str = tags_raw.strip()
                        if tags_raw_str.startswith("[") and tags_raw_str.endswith("]"):
                            try:
                                record_dict["tags"] = json.loads(tags_raw_str)
                            except Exception:
                                record_dict["tags"] = [
                                    t.strip() for t in tags_raw_str.strip("[]").split(",") if t.strip()
                                ]
                        else:
                            record_dict["tags"] = [
                                t.strip() for t in tags_raw_str.split(",") if t.strip()
                            ]

                    # Normalize empty reference answers
                    ref_ans = record_dict.get("reference_answer")
                    if ref_ans == "" or (isinstance(ref_ans, str) and not ref_ans.strip()):
                        record_dict["reference_answer"] = None

                    raw_records.append(record_dict)
        except Exception as exc:
            raise DatasetValidationError(f"Failed to read CSV file '{path}': {exc}") from exc

        validated_records = cls._validate_and_sort_records(raw_records, str(path))

        metadata = DatasetMetadata(
            version=version,
            name=f"Benchmark Dataset {version}",
            description="General Business & Customer Support Benchmark (CSV loaded)",
            total_records=len(validated_records),
        )

        return BenchmarkDataset(metadata=metadata, records=validated_records)

    @classmethod
    def _validate_and_sort_records(
        cls, raw_records: List[Dict[str, Any]], source_info: str
    ) -> List[DatasetRecord]:
        """
        Validates a list of raw dictionaries against DatasetRecord, checks for duplicates,
        and returns deterministically sorted records.
        """
        seen_ids = set()
        validated_records: List[DatasetRecord] = []

        for idx, item in enumerate(raw_records):
            if not isinstance(item, dict):
                raise DatasetValidationError(
                    f"Record at index {idx} in '{source_info}' is not a valid dictionary object."
                )

            record_id = item.get("id")
            if not record_id:
                raise DatasetValidationError(
                    f"Record at index {idx} in '{source_info}' is missing required field 'id'."
                )

            if record_id in seen_ids:
                logger.error(f"Duplicate record ID detected: '{record_id}' in '{source_info}'")
                raise DuplicateDatasetIDError(
                    duplicate_id=record_id,
                    message=f"Duplicate record ID '{record_id}' found in '{source_info}'. Dataset IDs must be unique.",
                )
            seen_ids.add(record_id)

            try:
                record = DatasetRecord.model_validate(item)
                validated_records.append(record)
            except ValidationError as val_err:
                logger.error(f"Validation failed for record ID '{record_id}': {val_err}")
                raise DatasetValidationError(
                    f"Schema validation error in record ID '{record_id}': {val_err}"
                ) from val_err

        # Enforce deterministic ordering by sorting records by ID
        validated_records.sort(key=lambda r: r.id)
        return validated_records
