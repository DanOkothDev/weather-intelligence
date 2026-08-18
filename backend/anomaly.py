import pandas as pd


DEFAULT_WARNING_THRESHOLD = 2.0
DEFAULT_CRITICAL_THRESHOLD = 3.0
MINIMUM_RECORDS = 5


def detect_anomalies(
    df: pd.DataFrame,
    warning_threshold: float = DEFAULT_WARNING_THRESHOLD,
    anomaly_threshold: float = DEFAULT_CRITICAL_THRESHOLD,
    minimum_required_records: int = MINIMUM_RECORDS,
) -> dict:
    """Detect anomalies using z-scores with centralized severity thresholds."""

    results = {}

    numeric_columns = df.select_dtypes(include="number").columns

    for column in numeric_columns:
        series = pd.to_numeric(df[column], errors="coerce")
        valid = series.dropna()

        if len(valid) < minimum_required_records:
            results[column] = {
                "status": "insufficient_data",
                "message": (
                    f"At least {minimum_required_records} valid records are required "
                    f"for anomaly detection in '{column}'."
                ),
                "records_analyzed": int(len(valid)),
                "minimum_required_records": minimum_required_records,
                "anomaly_count": 0,
                "anomalies": [],
            }
            continue

        mean = valid.mean()
        std = valid.std()

        if std == 0 or pd.isna(std):
            results[column] = {
                "status": "normal",
                "records_analyzed": int(len(valid)),
                "mean": round(float(mean), 3),
                "standard_deviation": 0.0,
                "anomaly_count": 0,
                "anomalies": [],
            }
            continue

        z_scores = (series - mean) / std
        anomalies = []

        for index, z_score in z_scores.items():
            if pd.isna(z_score):
                continue

            absolute_z = abs(float(z_score))

            if absolute_z >= anomaly_threshold:
                severity = "critical"
            elif absolute_z >= warning_threshold:
                severity = "warning"
            else:
                continue

            anomalies.append({
                "index": int(index),
                "value": round(float(series.loc[index]), 3),
                "z_score": round(float(z_score), 3),
                "severity": severity,
            })

        if any(anomaly["severity"] == "critical" for anomaly in anomalies):
            status = "critical"
        elif any(anomaly["severity"] == "warning" for anomaly in anomalies):
            status = "warning"
        else:
            status = "normal"

        results[column] = {
            "status": status,
            "records_analyzed": int(len(valid)),
            "mean": round(float(mean), 3),
            "standard_deviation": round(float(std), 3),
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
        }

    return results


def generate_anomaly_report(
    df: pd.DataFrame,
    warning_threshold: float = DEFAULT_WARNING_THRESHOLD,
    anomaly_threshold: float = DEFAULT_CRITICAL_THRESHOLD,
    minimum_required_records: int = MINIMUM_RECORDS,
) -> dict:
    """Generate a complete anomaly report using consistent severity labels."""

    results = detect_anomalies(
        df,
        warning_threshold=warning_threshold,
        anomaly_threshold=anomaly_threshold,
        minimum_required_records=minimum_required_records,
    )

    total_warnings = sum(
        sum(
            anomaly["severity"] == "warning"
            for anomaly in result["anomalies"]
        )
        for result in results.values()
    )

    total_critical = sum(
        sum(
            anomaly["severity"] == "critical"
            for anomaly in result["anomalies"]
        )
        for result in results.values()
    )

    return {
        "total_warnings": total_warnings,
        "total_critical": total_critical,
        "variables_analyzed": list(results.keys()),
        "results": results,
    }