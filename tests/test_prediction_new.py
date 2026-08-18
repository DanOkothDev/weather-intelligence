import pandas as pd
import pytest

from backend.prediction import (
    train_prediction_model,
    generate_predictions,
    generate_prediction_report,
)


def create_valid_test_data():
    """Create a clean test dataset with consistent frequency."""
    timestamps = pd.date_range(
        "2026-08-16 00:00",
        periods=20,
        freq="h"
    )

    return pd.DataFrame({
        "timestamp": timestamps,
        "temperature": [
            22.0, 22.3, 22.7, 23.1, 23.5,
            23.9, 24.2, 24.6, 25.0, 25.3,
            25.7, 26.0, 26.2, 26.4, 26.5,
            26.7, 26.8, 27.0, 27.1, 27.3
        ],
        "humidity": [
            78, 77, 76, 75, 74,
            73, 72, 71, 70, 69,
            68, 67, 66, 65, 64,
            63, 62, 61, 60, 59
        ],
        "rainfall": [
            0.0, 0.0, 0.2, 0.0, 0.0,
            0.4, 0.0, 0.0, 1.2, 0.0,
            0.0, 0.0, 2.1, 0.0, 0.0,
            0.0, 0.8, 0.0, 0.0, 1.5
        ]
    })


def test_train_prediction_model_validates_required_timestamp():
    df = create_valid_test_data()
    df_no_ts = df.drop(columns=["timestamp"])

    result = train_prediction_model(df_no_ts, "temperature")

    assert result["status"] == "validation_error"
    assert "timestamp" in result["message"].lower()


def test_train_prediction_model_validates_target_column():
    df = create_valid_test_data()

    result = train_prediction_model(df, "pressure")

    assert result["status"] == "validation_error"
    assert "pressure" in result["message"].lower()


def test_train_prediction_model_requires_minimum_records():
    df = create_valid_test_data().iloc[:5]

    result = train_prediction_model(df, "temperature")

    assert result["status"] == "insufficient_data"
    assert result["records_available"] <= 5


def test_train_prediction_model_exposes_mae_and_rmse_metrics():
    df = create_valid_test_data()

    result = train_prediction_model(df, "temperature")

    assert result["status"] == "success"
    assert "metrics" in result
    assert "mae" in result["metrics"]
    assert "rmse" in result["metrics"]
    assert result["metrics"]["mae"] > 0
    assert result["metrics"]["rmse"] > 0


def test_generate_predictions_handles_missing_timestamps():
    df = create_valid_test_data()
    df.loc[5, "timestamp"] = pd.NaT

    result = generate_predictions(df, "temperature", horizon=3)

    assert result["status"] in {"success", "insufficient_data"}


def test_generate_predictions_handles_missing_target_values():
    df = create_valid_test_data()
    df.loc[3:5, "temperature"] = None

    result = generate_predictions(df, "temperature", horizon=3)

    assert result["status"] in {"success", "insufficient_data"}
    assert "predictions" in result


def test_generate_predictions_handles_constant_values():
    df = create_valid_test_data()
    df["temperature"] = 25.0

    result = generate_predictions(df, "temperature", horizon=3)

    assert result["status"] in {"success", "insufficient_data"}
    if result["status"] == "success" and result["predictions"]:
        assert all(isinstance(p["value"], (int, float)) for p in result["predictions"])


def test_generate_predictions_detects_repeated_predictions():
    df = create_valid_test_data()

    result = generate_predictions(df, "temperature", horizon=5)

    if result["status"] == "success" and len(result["predictions"]) >= 2:
        predictions = [p["value"] for p in result["predictions"]]
        unique_predictions = len(set(predictions))
        assert "repeated_predictions_count" in result
        repeated_count = result["repeated_predictions_count"]
        total_predictions = len(predictions)
        assert repeated_count == total_predictions - unique_predictions


def test_generate_prediction_report_validates_all_datasets():
    df = create_valid_test_data()

    report = generate_prediction_report(df, horizon=3)

    assert "variables_analyzed" in report
    assert "results" in report
    for var, result in report["results"].items():
        if result["status"] == "success":
            assert "metrics" in result
            assert "mae" in result["metrics"]
            assert "rmse" in result["metrics"]
