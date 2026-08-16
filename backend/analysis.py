import pandas as pd


NUMERIC_WEATHER_COLUMNS = [
    "temperature",
    "humidity",
    "rainfall",
    "pressure",
    "wind_speed",
    "wind_direction",
    "solar_radiation",
]


def analyze_numeric_columns(df: pd.DataFrame) -> dict:
    """Generate descriptive statistics for available numeric weather data."""

    analysis = {}

    for column in NUMERIC_WEATHER_COLUMNS:
        if column not in df.columns:
            continue

        series = pd.to_numeric(df[column], errors="coerce").dropna()

        if series.empty:
            continue

        analysis[column] = {
            "count": int(series.count()),
            "mean": round(float(series.mean()), 3),
            "median": round(float(series.median()), 3),
            "minimum": round(float(series.min()), 3),
            "maximum": round(float(series.max()), 3),
            "standard_deviation": round(float(series.std()), 3)
            if len(series) > 1
            else 0.0,
        }

    return analysis


def analyze_rainfall(df: pd.DataFrame) -> dict:
    """Analyze rainfall when rainfall data is available."""

    if "rainfall" not in df.columns:
        return {}

    rainfall = pd.to_numeric(
        df["rainfall"],
        errors="coerce",
    ).dropna()

    if rainfall.empty:
        return {}

    return {
        "total": round(float(rainfall.sum()), 3),
        "mean": round(float(rainfall.mean()), 3),
        "maximum": round(float(rainfall.max()), 3),
        "rainy_records": int((rainfall > 0).sum()),
        "dry_records": int((rainfall == 0).sum()),
    }


def analyze_correlations(df: pd.DataFrame) -> dict:
    """Calculate correlations between available numeric weather variables."""

    available_columns = [
        column
        for column in NUMERIC_WEATHER_COLUMNS
        if column in df.columns
    ]

    if len(available_columns) < 2:
        return {}

    numeric_df = df[available_columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    correlation_matrix = numeric_df.corr()

    correlations = {}

    for column_a in correlation_matrix.columns:
        for column_b in correlation_matrix.columns:

            if column_a >= column_b:
                continue

            value = correlation_matrix.loc[column_a, column_b]

            if pd.notna(value):
                correlations[f"{column_a}_vs_{column_b}"] = round(
                    float(value),
                    3,
                )

    return correlations


def analyze_trends(df: pd.DataFrame) -> dict:
    """Estimate simple linear trends over record order."""

    trends = {}

    for column in NUMERIC_WEATHER_COLUMNS:

        if column not in df.columns:
            continue

        series = pd.to_numeric(
            df[column],
            errors="coerce",
        ).dropna()

        if len(series) < 2:
            continue

        x = range(len(series))

        slope = pd.Series(series.values).corr(
            pd.Series(list(x))
        )

        if pd.isna(slope):
            direction = "stable"
        elif slope > 0.1:
            direction = "increasing"
        elif slope < -0.1:
            direction = "decreasing"
        else:
            direction = "stable"

        trends[column] = {
            "direction": direction,
            "correlation_with_time": round(
                float(slope),
                3,
            ),
        }

    return trends


def generate_analysis(df: pd.DataFrame) -> dict:
    """Generate the complete weather analysis."""

    return {
        "statistics": analyze_numeric_columns(df),
        "rainfall": analyze_rainfall(df),
        "correlations": analyze_correlations(df),
        "trends": analyze_trends(df),
    }