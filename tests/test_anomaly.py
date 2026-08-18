import pandas as pd

from backend.anomaly import detect_anomalies, generate_anomaly_report


def test_detect_anomalies_uses_normal_warning_and_critical_statuses():
    df = pd.DataFrame({
        "temperature": [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 60.0],
    })

    result = detect_anomalies(df, warning_threshold=1.5, anomaly_threshold=2.0)
    anomalies = result["temperature"]["anomalies"]

    assert result["temperature"]["status"] == "critical"
    assert all(item["severity"] in {"warning", "critical"} for item in anomalies)
    assert any(item["severity"] == "critical" for item in anomalies)


def test_detect_anomalies_reports_insufficient_data_and_ignores_missing_values():
    df = pd.DataFrame({
        "temperature": [20.0, 20.1, None, 20.2, None],
    })

    result = detect_anomalies(df)
    column_report = result["temperature"]

    assert column_report["status"] == "insufficient_data"
    assert column_report["records_analyzed"] == 3
    assert column_report["minimum_required_records"] == 5
    assert "message" in column_report


def test_generate_anomaly_report_uses_configurable_thresholds_and_counts():
    df = pd.DataFrame({
        "temperature": [10, 10, 10, 10, 10, 10, 30],
    })

    report = generate_anomaly_report(
        df,
        warning_threshold=1.0,
        anomaly_threshold=2.0,
    )

    assert report["variables_analyzed"] == ["temperature"]
    assert report["results"]["temperature"]["status"] in {"normal", "warning", "critical"}
    assert "total_warnings" in report
    assert "total_critical" in report