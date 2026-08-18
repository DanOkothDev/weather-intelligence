"""
Forecast Insights Module
Generates confidence intervals, trend analysis, anomaly detection, and uncertainty quantification.
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error


class InsightsError(Exception):
    """Custom exception for insights module."""
    pass


def calculate_confidence_intervals(
    df: pd.DataFrame,
    forecast_column: str,
    confidence_level: float = 0.95,
    window_size: int = 5
):
    """
    Calculate confidence intervals for forecast predictions.
    
    Args:
        df: DataFrame with forecast values
        forecast_column: Name of column containing forecasts
        confidence_level: Confidence level (0.90, 0.95, 0.99)
        window_size: Rolling window for uncertainty estimation
    
    Returns:
        Dict with status and intervals
    """
    
    if forecast_column not in df.columns:
        return {
            "status": "validation_error",
            "message": f"The forecast column '{forecast_column}' was not found."
        }
    
    if confidence_level not in [0.90, 0.95, 0.99]:
        confidence_level = 0.95
    
    # Map confidence level to z-score
    z_score = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}[confidence_level]
    
    # Calculate rolling standard deviation to estimate uncertainty
    rolling_std = df[forecast_column].rolling(
        window=window_size,
        min_periods=1
    ).std().fillna(df[forecast_column].std() / 2)
    
    intervals = []
    
    for idx, row in df.iterrows():
        forecast_value = row[forecast_column]
        std_dev = rolling_std.iloc[idx]
        
        margin_of_error = z_score * std_dev
        
        intervals.append({
            "timestamp": row.get("timestamp", idx),
            "point_estimate": round(float(forecast_value), 3),
            "lower": round(float(forecast_value - margin_of_error), 3),
            "upper": round(float(forecast_value + margin_of_error), 3),
            "margin_of_error": round(float(margin_of_error), 3)
        })
    
    return {
        "status": "success",
        "confidence_level": confidence_level,
        "intervals": intervals
    }


def analyze_forecast_trend(
    df: pd.DataFrame,
    forecast_column: str
):
    """
    Analyze trend in forecast (increasing, decreasing, stable).
    
    Args:
        df: DataFrame with forecast values
        forecast_column: Name of column containing forecasts
    
    Returns:
        Dict with trend analysis results
    """
    
    if forecast_column not in df.columns:
        return {
            "status": "validation_error",
            "message": f"The forecast column '{forecast_column}' was not found."
        }
    
    values = df[forecast_column].values.reshape(-1, 1)
    X = np.arange(len(values)).reshape(-1, 1)
    
    # Check if all values are the same
    if np.std(values) < 1e-6:
        return {
            "status": "success",
            "trend": "stable",
            "slope": 0.0,
            "r_squared": 1.0,
            "mean_value": float(np.mean(values))
        }
    
    model = LinearRegression()
    model.fit(X, values)
    
    slope = float(model.coef_[0][0])
    r_squared = model.score(X, values)
    
    # Determine trend based on slope
    if abs(slope) < 0.01:
        trend = "stable"
    elif slope > 0:
        trend = "increasing"
    else:
        trend = "decreasing"
    
    return {
        "status": "success",
        "trend": trend,
        "slope": round(float(slope), 4),
        "r_squared": round(float(r_squared), 4),
        "forecast_change": round(float(slope * len(df)), 3)
    }


def detect_forecast_anomalies(
    df: pd.DataFrame,
    actual_column: str = "temperature",
    forecast_column: str = "forecast",
    threshold: float = 2.0
):
    """
    Detect anomalies (prediction errors > threshold).
    
    Args:
        df: DataFrame with actual and forecast values
        actual_column: Column name for actual values
        forecast_column: Column name for forecasts
        threshold: Standard deviations for anomaly threshold
    
    Returns:
        Dict with anomaly detection results
    """
    
    if actual_column not in df.columns:
        return {
            "status": "validation_error",
            "message": f"The actual column '{actual_column}' was not found."
        }
    
    if forecast_column not in df.columns:
        return {
            "status": "validation_error",
            "message": f"The forecast column '{forecast_column}' was not found."
        }
    
    # Calculate errors
    errors = df[forecast_column] - df[actual_column]
    mean_error = errors.mean()
    std_error = errors.std()
    
    if std_error < 1e-6:
        std_error = 1.0
    
    # Normalize errors (z-score)
    z_scores = (errors - mean_error) / std_error
    
    # Identify anomalies
    anomalies = []
    
    for idx, row in df.iterrows():
        z_score = z_scores.iloc[idx]
        
        if abs(z_score) > threshold:
            error = errors.iloc[idx]
            severity = "critical" if abs(z_score) > threshold * 1.5 else "warning"
            
            anomalies.append({
                "timestamp": row.get("timestamp", idx),
                "actual": round(float(row[actual_column]), 3),
                "forecast": round(float(row[forecast_column]), 3),
                "error": round(float(error), 3),
                "z_score": round(float(z_score), 3),
                "severity": severity
            })
    
    return {
        "status": "success",
        "threshold": threshold,
        "mean_error": round(float(mean_error), 3),
        "std_error": round(float(std_error), 3),
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies
    }


def quantify_uncertainty(
    df: pd.DataFrame,
    actual_column: str = "temperature",
    forecast_column: str = "forecast"
):
    """
    Quantify forecast uncertainty with error metrics.
    
    Args:
        df: DataFrame with actual and forecast values
        actual_column: Column name for actual values
        forecast_column: Column name for forecasts
    
    Returns:
        Dict with uncertainty metrics
    """
    
    if actual_column not in df.columns:
        return {
            "status": "validation_error",
            "message": f"The actual column '{actual_column}' was not found."
        }
    
    if forecast_column not in df.columns:
        return {
            "status": "validation_error",
            "message": f"The forecast column '{forecast_column}' was not found."
        }
    
    y_actual = df[actual_column].values
    y_forecast = df[forecast_column].values
    
    mae = mean_absolute_error(y_actual, y_forecast)
    rmse = np.sqrt(mean_squared_error(y_actual, y_forecast))
    
    # Mean Absolute Percentage Error
    non_zero_mask = y_actual != 0
    if non_zero_mask.any():
        mape = 100 * np.mean(
            np.abs((y_actual[non_zero_mask] - y_forecast[non_zero_mask]) / 
                   y_actual[non_zero_mask])
        )
    else:
        mape = 0.0
    
    # Prediction interval coverage estimate
    errors = y_forecast - y_actual
    std_error = np.std(errors)
    
    if std_error > 0:
        within_interval = np.sum(np.abs(errors) <= 1.96 * std_error) / len(errors)
    else:
        within_interval = 1.0 if np.allclose(y_actual, y_forecast) else 0.0
    
    return {
        "status": "success",
        "mae": round(float(mae), 3),
        "rmse": round(float(rmse), 3),
        "mape": round(float(mape), 3),
        "prediction_interval_coverage": round(float(within_interval), 3),
        "forecast_bias": round(float(np.mean(y_forecast - y_actual)), 3)
    }


def generate_insights_report(
    df: pd.DataFrame,
    actual_column: str = "temperature",
    forecast_column: str = "forecast"
):
    """
    Generate comprehensive forecast insights report.
    
    Args:
        df: DataFrame with actual and forecast data
        actual_column: Column name for actual values
        forecast_column: Column name for forecasts
    
    Returns:
        Complete insights report
    """
    
    # Validate minimum requirements
    if len(df) < 2:
        return {
            "status": "insufficient_data",
            "message": "At least 2 records required for insights."
        }
    
    if "timestamp" not in df.columns:
        # Add index-based timestamps if not present
        df = df.copy()
        df["timestamp"] = pd.date_range(
            "2026-08-16",
            periods=len(df),
            freq="h"
        )
    
    if forecast_column not in df.columns:
        return {
            "status": "validation_error",
            "message": f"The forecast column '{forecast_column}' was not found."
        }
    
    # Generate all components
    confidence_intervals = calculate_confidence_intervals(
        df,
        forecast_column
    )
    
    trend_analysis = analyze_forecast_trend(df, forecast_column)
    
    # For anomaly and uncertainty, we need actual values
    if actual_column in df.columns:
        anomaly_detection = detect_forecast_anomalies(
            df,
            actual_column,
            forecast_column
        )
        uncertainty = quantify_uncertainty(df, actual_column, forecast_column)
    else:
        anomaly_detection = {
            "status": "skipped",
            "message": f"Actual column '{actual_column}' not found"
        }
        uncertainty = {
            "status": "skipped",
            "message": f"Actual column '{actual_column}' not found"
        }
    
    return {
        "status": "success",
        "records_analyzed": len(df),
        "confidence_intervals": confidence_intervals,
        "trend_analysis": trend_analysis,
        "anomaly_detection": anomaly_detection,
        "uncertainty_quantification": uncertainty,
        "summary": {
            "forecast_trend": trend_analysis.get("trend", "unknown"),
            "anomalies_found": anomaly_detection.get("anomalies_detected", 0),
            "uncertainty_mae": uncertainty.get("mae", None)
        }
    }
