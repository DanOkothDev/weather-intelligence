import pandas as pd


DEFAULT_WARNING_THRESHOLD = 2.0
DEFAULT_ANOMALY_THRESHOLD = 3.0
MINIMUM_RECORDS = 5


def detect_anomalies(
    df: pd.DataFrame,
    warning_threshold: float = DEFAULT_WARNING_THRESHOLD,
    anomaly_threshold: float = DEFAULT_ANOMALY_THRESHOLD,
) -> dict:
    """
    Detect statistical anomalies in numeric weather variables.

    Z-score is used to determine how far each observation is
    from the variable's mean.
    """

    results = {}

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:

        series = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        valid = series.dropna()

        # Not enough observations for meaningful statistics
        if len(valid) < MINIMUM_RECORDS:
            results[column] = {
                "status": "insufficient_data",
                "message": (
                    f"At least {MINIMUM_RECORDS} valid records "
                    f"are required for anomaly detection."
                ),
                "records_analyzed": int(len(valid)),
                "anomaly_count": 0,
                "anomalies": [],
            }

            continue

        mean = valid.mean()
        std = valid.std()

        # Constant values cannot produce meaningful z-scores
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
                severity = "anomaly"
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

        if any(
            anomaly["severity"] == "anomaly"
            for anomaly in anomalies
        ):
            status = "anomaly"
        elif anomalies:
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


def generate_anomaly_report(df: pd.DataFrame) -> dict:
    """
    Generate a complete anomaly report.
    """

    results = detect_anomalies(df)

    total_anomalies = sum(
        result["anomaly_count"]
        for result in results.values()
    )

    warning_count = sum(
        sum(
            anomaly["severity"] == "warning"
            for anomaly in result["anomalies"]
        )
        for result in results.values()
    )

    critical_count = sum(
        sum(
            anomaly["severity"] == "anomaly"
            for anomaly in result["anomalies"]
        )
        for result in results.values()
    )

    return {
        "total_anomalies": total_anomalies,
        "warnings": warning_count,
        "critical_anomalies": critical_count,
        "variables_analyzed": list(results.keys()),
        "results": results,
    }