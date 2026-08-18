import pandas as pd
import pytest

from backend.insights import (
    calculate_confidence_intervals,
    analyze_forecast_trend,
    detect_forecast_anomalies,
    quantify_uncertainty,
    generate_insights_report,
)


def create_valid_forecast_data():
    """Create a valid forecast dataset with predictions."""
    timestamps = pd.date_range("2026-08-16", periods=10, freq="h")
    
    return pd.DataFrame({
        "timestamp": timestamps,
        "temperature": [
            22.0, 22.5, 23.0, 23.5, 24.0,
            24.5, 25.0, 25.5, 26.0, 26.5
        ],
        "forecast": [
            22.1, 22.4, 23.2, 23.4, 24.1,
            24.6, 25.0, 25.4, 26.1, 26.3
        ],
        "model": "RandomForest"
    })


def test_calculate_confidence_intervals_returns_bounds():
    """Confidence intervals should include lower and upper bounds."""
    df = create_valid_forecast_data()
    
    result = calculate_confidence_intervals(
        df,
        forecast_column="forecast",
        confidence_level=0.95
    )
    
    assert result["status"] == "success"
    assert "intervals" in result
    assert len(result["intervals"]) == len(df)
    
    for interval in result["intervals"]:
        assert "timestamp" in interval
        assert "lower" in interval
        assert "upper" in interval
        assert "point_estimate" in interval
        assert interval["lower"] < interval["upper"]
        assert interval["lower"] <= interval["point_estimate"]
        assert interval["point_estimate"] <= interval["upper"]


def test_calculate_confidence_intervals_validates_columns():
    """Should validate that forecast column exists."""
    df = create_valid_forecast_data()
    df_no_forecast = df.drop(columns=["forecast"])
    
    result = calculate_confidence_intervals(
        df_no_forecast,
        forecast_column="forecast",
        confidence_level=0.95
    )
    
    assert result["status"] == "validation_error"
    assert "forecast" in result["message"].lower()


def test_calculate_confidence_intervals_respects_confidence_level():
    """Wider confidence levels should produce wider intervals."""
    df = create_valid_forecast_data()
    
    result_90 = calculate_confidence_intervals(df, "forecast", 0.90)
    result_99 = calculate_confidence_intervals(df, "forecast", 0.99)
    
    assert result_90["status"] == "success"
    assert result_99["status"] == "success"
    
    # 99% CI should be wider than 90% CI
    width_90 = (
        result_90["intervals"][0]["upper"] - 
        result_90["intervals"][0]["lower"]
    )
    width_99 = (
        result_99["intervals"][0]["upper"] - 
        result_99["intervals"][0]["lower"]
    )
    
    assert width_99 > width_90


def test_analyze_forecast_trend_detects_increasing():
    """Should detect increasing trend in forecasts."""
    df = create_valid_forecast_data()
    
    result = analyze_forecast_trend(df, "forecast")
    
    assert result["status"] == "success"
    assert "trend" in result
    assert result["trend"] in ["increasing", "decreasing", "stable"]
    assert "slope" in result
    assert "r_squared" in result
    
    # Temperature is steadily increasing, so trend should be detected
    assert result["trend"] == "increasing"
    assert result["slope"] > 0


def test_analyze_forecast_trend_validates_columns():
    """Should validate forecast column exists."""
    df = create_valid_forecast_data()
    df_no_forecast = df.drop(columns=["forecast"])
    
    result = analyze_forecast_trend(df_no_forecast, "forecast")
    
    assert result["status"] == "validation_error"
    assert "forecast" in result["message"].lower()


def test_analyze_forecast_trend_handles_stable_forecast():
    """Should detect stable trend when values are constant."""
    df = create_valid_forecast_data()
    df["forecast"] = 24.0  # Constant value
    
    result = analyze_forecast_trend(df, "forecast")
    
    assert result["status"] == "success"
    assert result["trend"] == "stable"
    assert result["slope"] == 0


def test_detect_forecast_anomalies_identifies_outliers():
    """Should identify predictions that deviate significantly from actual."""
    df = create_valid_forecast_data()
    df.loc[5, "forecast"] = 50.0  # Insert anomalous forecast
    
    result = detect_forecast_anomalies(
        df,
        actual_column="temperature",
        forecast_column="forecast",
        threshold=2.0
    )
    
    assert result["status"] == "success"
    assert "anomalies" in result
    assert len(result["anomalies"]) >= 1
    
    anomaly = result["anomalies"][0]
    assert "timestamp" in anomaly
    assert "actual" in anomaly
    assert "forecast" in anomaly
    assert "error" in anomaly
    assert "severity" in anomaly


def test_detect_forecast_anomalies_validates_columns():
    """Should validate required columns exist."""
    df = create_valid_forecast_data()
    df_no_actual = df.drop(columns=["temperature"])
    
    result = detect_forecast_anomalies(
        df_no_actual,
        actual_column="temperature",
        forecast_column="forecast"
    )
    
    assert result["status"] == "validation_error"
    assert "temperature" in result["message"].lower()


def test_detect_forecast_anomalies_respects_threshold():
    """Stricter threshold should detect fewer anomalies."""
    df = create_valid_forecast_data()
    df.loc[3, "forecast"] = 28.0  # Moderate deviation
    
    result_strict = detect_forecast_anomalies(
        df, "temperature", "forecast", threshold=1.0
    )
    result_loose = detect_forecast_anomalies(
        df, "temperature", "forecast", threshold=5.0
    )
    
    assert result_strict["status"] == "success"
    assert result_loose["status"] == "success"
    
    # Stricter threshold should find more (or equal) anomalies
    assert len(result_strict["anomalies"]) >= len(result_loose["anomalies"])


def test_quantify_uncertainty_exposes_metrics():
    """Should compute uncertainty metrics (RMSE, MAE, coverage)."""
    df = create_valid_forecast_data()
    
    result = quantify_uncertainty(
        df,
        actual_column="temperature",
        forecast_column="forecast"
    )
    
    assert result["status"] == "success"
    assert "mae" in result
    assert "rmse" in result
    assert "mape" in result
    assert "prediction_interval_coverage" in result
    assert result["mae"] >= 0
    assert result["rmse"] >= 0
    assert result["mape"] >= 0


def test_quantify_uncertainty_handles_perfect_forecast():
    """Should handle case where forecast perfectly matches actual."""
    df = create_valid_forecast_data()
    df["forecast"] = df["temperature"]  # Perfect match
    
    result = quantify_uncertainty(df, "temperature", "forecast")
    
    assert result["status"] == "success"
    assert result["mae"] == 0.0
    assert result["rmse"] == 0.0
    assert result["mape"] == 0.0


def test_generate_insights_report_integrates_all_components():
    """Full insights report should include all analyses."""
    df = create_valid_forecast_data()
    
    report = generate_insights_report(df)
    
    assert report["status"] == "success"
    assert "confidence_intervals" in report
    assert "trend_analysis" in report
    assert "anomaly_detection" in report
    assert "uncertainty_quantification" in report
    
    # Each component should have success status
    assert report["confidence_intervals"]["status"] == "success"
    assert report["trend_analysis"]["status"] == "success"
    assert report["anomaly_detection"]["status"] == "success"
    assert report["uncertainty_quantification"]["status"] == "success"


def test_generate_insights_report_validates_dataset():
    """Should validate required columns in dataset."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-08-16", periods=5, freq="h")
    })
    
    result = generate_insights_report(df)
    
    # Should handle gracefully - either validate_error or work with available data
    assert result["status"] in {"success", "validation_error"}
