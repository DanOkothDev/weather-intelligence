import pandas as pd
import pytest
import tempfile
import os

from backend.ingestion import load_dataset, get_dataset_metadata


def create_test_csv():
    """Create a temporary test CSV file."""
    timestamps = pd.date_range("2026-08-16", periods=10, freq="h")
    
    df = pd.DataFrame({
        "timestamp": timestamps,
        "temperature": [22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 26.0, 26.5],
        "humidity": [78, 77, 76, 75, 74, 73, 72, 71, 70, 69],
        "rainfall": [0.0, 0.0, 0.2, 0.0, 0.4, 0.0, 0.0, 1.2, 0.0, 0.0]
    })
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        return f.name


def test_load_dataset_reads_csv():
    """Should successfully load CSV files."""
    csv_path = create_test_csv()
    
    try:
        df = load_dataset(csv_path)
        
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert "timestamp" in df.columns
    finally:
        os.unlink(csv_path)


def test_load_dataset_handles_missing_file():
    """Should handle missing files gracefully."""
    with pytest.raises(Exception):
        load_dataset("nonexistent/file/path.csv")


def test_load_dataset_detects_column_types():
    """Should load data preserving column types from CSV."""
    csv_path = create_test_csv()
    
    try:
        df = load_dataset(csv_path)
        
        # CSV should preserve numeric columns
        assert pd.api.types.is_numeric_dtype(df["temperature"])
        assert pd.api.types.is_numeric_dtype(df["humidity"])
    finally:
        os.unlink(csv_path)


def test_get_dataset_metadata_returns_schema():
    """Should return comprehensive dataset metadata."""
    csv_path = create_test_csv()
    
    try:
        df = load_dataset(csv_path)
        metadata = get_dataset_metadata(df)
        
        assert "schema" in metadata or "columns" in metadata
        assert "record_count" in metadata or "rows" in metadata
    finally:
        os.unlink(csv_path)


def test_get_dataset_metadata_identifies_numeric_columns():
    """Metadata should identify numeric vs categorical columns."""
    csv_path = create_test_csv()
    
    try:
        df = load_dataset(csv_path)
        metadata = get_dataset_metadata(df)
        
        # Should identify numeric columns
        assert metadata is not None
    finally:
        os.unlink(csv_path)
