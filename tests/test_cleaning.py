import pandas as pd
import pytest

from backend.cleaning import (
    detect_weather_columns,
    clean_weather_data,
)


def test_detect_weather_columns_handles_common_aliases():
    df = pd.DataFrame({
        "Date Time": ["2026-08-16 10:00", "2026-08-16 11:00"],
        "Temp": [24.5, 25.1],
        "RH": [68, 65],
        "UV Level": [2.1, 3.0],
        "Cloud Percentage": [45, 60],
        "Visibility (km)": [9.5, 8.7],
        "Dewpoint": [10.4, 11.2],
    })

    detected = detect_weather_columns(df)

    assert detected["timestamp"] == "Date Time"
    assert detected["temperature"] == "Temp"
    assert detected["humidity"] == "RH"
    assert detected["uv_index"] == "UV Level"
    assert detected["cloud_cover"] == "Cloud Percentage"
    assert detected["visibility"] == "Visibility (km)"
    assert detected["dew_point"] == "Dewpoint"


def test_clean_weather_data_reports_invalid_values_and_removes_problem_rows():
    df = pd.DataFrame({
        "timestamp": [
            "2026-08-16 10:00",
            "2026-08-16 11:00",
            "bad-timestamp",
            "2026-08-16 11:00",
            "2026-08-16 13:00",
        ],
        "temperature": [21.4, "bad", 20.0, 21.4, 22.1],
        "uv_level": [1.2, 2.5, 4.0, 2.5, "oops"],
        "humidity": [50, 55, 60, 55, 58],
    })

    cleaned, report = clean_weather_data(df)

    assert len(cleaned) == 4
    assert report["rows_removed"]["duplicate_rows"] == 0
    assert report["rows_removed"]["invalid_timestamp_rows"] == 1
    assert report["timestamp_conversion"]["invalid_values"] == 1
    assert report["numeric_conversions"]["temperature"]["invalid_values"] == 1
    assert report["numeric_conversions"]["uv_index"]["invalid_values"] == 1
    assert report["summary"]["invalid_values_found"] == 3
    assert "timestamp" in cleaned.columns
    assert cleaned["timestamp"].notna().all()