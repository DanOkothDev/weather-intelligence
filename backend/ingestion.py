from pathlib import Path
import json

import pandas as pd


SUPPORTED_FORMATS = {".csv", ".json", ".xlsx", ".xls"}


class IngestionError(Exception):
    """Raised when a dataset cannot be ingested."""


def detect_format(filename: str) -> str:
    """Detect the dataset format from its file extension."""
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_FORMATS:
        raise IngestionError(
            f"Unsupported file format: {extension or 'unknown'}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    return extension


def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load a supported dataset into a pandas DataFrame.
    """

    path = Path(file_path)

    if not path.exists():
        raise IngestionError(f"File not found: {file_path}")

    extension = detect_format(path.name)

    try:
        if extension == ".csv":
            df = pd.read_csv(path)

        elif extension == ".json":
            df = pd.read_json(path)

        elif extension in {".xlsx", ".xls"}:
            df = pd.read_excel(path)

        else:
            raise IngestionError(f"Unsupported format: {extension}")

    except Exception as exc:
        raise IngestionError(
            f"Failed to read dataset: {exc}"
        ) from exc

    if df.empty:
        raise IngestionError("The dataset is empty.")

    if df.columns.empty:
        raise IngestionError("The dataset contains no columns.")

    return df


def get_dataset_metadata(df: pd.DataFrame) -> dict:
    """Generate basic metadata about an ingested dataset."""

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "data_types": {
            column: str(dtype)
            for column, dtype in df.dtypes.items()
        },
        "missing_values": {
            column: int(value)
            for column, value in df.isna().sum().items()
        },
    }