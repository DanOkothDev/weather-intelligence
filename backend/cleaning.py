import re

import pandas as pd


# Canonical field -> possible names we may receive
COLUMN_ALIASES = {
    "timestamp": [
        "timestamp",
        "datetime",
        "date_time",
        "date",
        "time",
        "recorded_at",
        "measurement_time",
    ],
    "temperature": [
        "temperature",
        "temp",
        "air_temperature",
        "air_temp",
        "temperature_c",
        "temp_c",
    ],
    "humidity": [
        "humidity",
        "relative_humidity",
        "rh",
        "humidity_percent",
        "relative_humidity_percent",
    ],
    "rainfall": [
        "rainfall",
        "rain",
        "precipitation",
        "precip",
        "rainfall_mm",
        "rain_mm",
    ],
    "pressure": [
        "pressure",
        "air_pressure",
        "atmospheric_pressure",
        "pressure_hpa",
    ],
    "wind_speed": [
        "wind_speed",
        "windspeed",
        "wind_velocity",
        "wind_speed_ms",
    ],
    "wind_direction": [
        "wind_direction",
        "wind_dir",
        "wind_direction_deg",
    ],
    "solar_radiation": [
        "solar_radiation",
        "solar",
        "solar_energy",
        "radiation",
    ],
    "uv_index": [
        "uv_index",
        "uv",
        "uvi",
        "ultraviolet_index",
    ],
    "cloud_cover": [
        "cloud_cover",
        "cloudiness",
        "cloud_cover_percent",
        "cloud_percentage",
    ],
    "visibility": [
        "visibility",
        "visibility_km",
        "vis",
    ],
    "dew_point": [
        "dew_point",
        "dewpoint",
        "dew_point_temperature",
        "dewpoint_temperature",
    ],
}


def normalize_column_name(column: str) -> str:
    """
    Convert a column name into a predictable comparison format.
    """

    column = str(column).strip().lower()

    # Replace spaces and special characters with underscores
    column = re.sub(r"[^a-z0-9]+", "_", column)

    # Remove duplicate underscores
    column = re.sub(r"_+", "_", column)

    return column.strip("_")


def detect_weather_columns(df: pd.DataFrame) -> dict:
    """
    Match dataset columns against known weather-field aliases.

    Returns:
        {
            "temperature": "Temp",
            "humidity": "RH",
            ...
        }
    """

    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    detected = {}

    for canonical_name, aliases in COLUMN_ALIASES.items():

        normalized_aliases = {
            normalize_column_name(alias)
            for alias in aliases
        }

        for normalized_alias in normalized_aliases:
            if normalized_alias in normalized_columns:
                detected[canonical_name] = normalized_columns[
                    normalized_alias
                ]
                break

    return detected


def normalize_weather_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename detected weather columns to canonical names.
    """

    detected = detect_weather_columns(df)

    rename_map = {
        original: canonical
        for canonical, original in detected.items()
    }

    normalized_df = df.rename(columns=rename_map).copy()

    return normalized_df


def clean_weather_data(df: pd.DataFrame) -> pd.DataFrame:

    df = normalize_weather_schema(df)

    # Convert timestamp when available
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )

    # Convert numerical weather measurements
    numeric_columns = [
        "temperature",
        "humidity",
        "rainfall",
        "pressure",
        "wind_speed",
        "solar_radiation",
        "uv_index",
        "cloud_cover",
        "visibility",
        "dew_point",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    if "wind_direction" in df.columns:

        direction_map = {
            "N": 0,
            "NNE": 22.5,
            "NE": 45,
            "ENE": 67.5,
            "E": 90,
            "ESE": 112.5,
            "SE": 135,
            "SSE": 157.5,
            "S": 180,
            "SSW": 202.5,
            "SW": 225,
            "WSW": 247.5,
            "W": 270,
            "WNW": 292.5,
            "NW": 315,
            "NNW": 337.5,
        }

        def convert_wind_direction(value):
            if pd.isna(value):
                return None

            # Already numeric
            if isinstance(value, (int, float)):
                return float(value)

            value = str(value).strip().upper()

            # Cardinal/intercardinal direction
            if value in direction_map:
                return direction_map[value]

            # Numeric string such as "135"
            try:
                return float(value)
            except ValueError:
                return None

        df["wind_direction"] = df["wind_direction"].apply(
            convert_wind_direction
        )

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove duplicate measurements
    df = df.drop_duplicates()

    return df