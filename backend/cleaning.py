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


# Columns that should contain numerical values
NUMERIC_COLUMNS = [
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


# Compass direction -> degrees
WIND_DIRECTION_MAP = {
    "N": 0.0,
    "NNE": 22.5,
    "NE": 45.0,
    "ENE": 67.5,
    "E": 90.0,
    "ESE": 112.5,
    "SE": 135.0,
    "SSE": 157.5,
    "S": 180.0,
    "SSW": 202.5,
    "SW": 225.0,
    "WSW": 247.5,
    "W": 270.0,
    "WNW": 292.5,
    "NW": 315.0,
    "NNW": 337.5,
}


def normalize_column_name(column: str) -> str:

    column = str(column).strip().lower()

    # Replace spaces and special characters with underscores
    column = re.sub(r"[^a-z0-9]+", "_", column)

    # Remove duplicate underscores
    column = re.sub(r"_+", "_", column)

    return column.strip("_")


def detect_weather_columns(df: pd.DataFrame) -> dict:

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


def normalize_weather_schema(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:

    detected = detect_weather_columns(df)

    rename_map = {
        original: canonical
        for canonical, original in detected.items()
        if original != canonical
    }

    normalized_df = df.rename(
        columns=rename_map
    ).copy()

    return normalized_df, rename_map


def convert_numeric_column(
    df: pd.DataFrame,
    column: str,
) -> dict:

    if column not in df.columns:
        return {
            "original_non_null": 0,
            "converted_non_null": 0,
            "invalid_values": 0,
        }

    original = df[column]

    original_non_null = int(original.notna().sum())

    converted = pd.to_numeric(
        original,
        errors="coerce",
    )

    converted_non_null = int(converted.notna().sum())

    invalid_values = max(
        original_non_null - converted_non_null,
        0,
    )

    df[column] = converted

    return {
        "original_non_null": original_non_null,
        "converted_non_null": converted_non_null,
        "invalid_values": invalid_values,
    }


def convert_wind_direction(value):

    if pd.isna(value):
        return None

    # Already numeric
    if isinstance(value, (int, float)):
        direction = float(value)

    else:
        value = str(value).strip().upper()

        # Compass/intercardinal direction
        if value in WIND_DIRECTION_MAP:
            return WIND_DIRECTION_MAP[value]

        # Numeric string
        try:
            direction = float(value)
        except ValueError:
            return None

    # Valid compass bearing
    if 0 <= direction <= 360:
        return direction

    return None


def convert_wind_direction_column(
    df: pd.DataFrame,
) -> dict:

    if "wind_direction" not in df.columns:
        return {
            "original_non_null": 0,
            "converted_non_null": 0,
            "invalid_values": 0,
        }

    original = df["wind_direction"]

    original_non_null = int(
        original.notna().sum()
    )

    converted = original.apply(
        convert_wind_direction
    )

    converted_non_null = int(
        converted.notna().sum()
    )

    invalid_values = max(
        original_non_null - converted_non_null,
        0,
    )

    df["wind_direction"] = converted

    return {
        "original_non_null": original_non_null,
        "converted_non_null": converted_non_null,
        "invalid_values": invalid_values,
    }


def clean_weather_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:

    # Work on a copy so the caller's DataFrame is not modified.
    df = df.copy()

    original_rows = len(df)
    original_columns = list(df.columns)


    df, rename_map = normalize_weather_schema(df)

    timestamp_report = {
        "present": False,
        "original_non_null": 0,
        "converted_non_null": 0,
        "invalid_values": 0,
    }

    if "timestamp" in df.columns:

        timestamp_report["present"] = True

        original_timestamp = df["timestamp"]

        original_non_null = int(
            original_timestamp.notna().sum()
        )

        converted_timestamp = pd.to_datetime(
            original_timestamp,
            errors="coerce",
        )

        converted_non_null = int(
            converted_timestamp.notna().sum()
        )

        invalid_values = max(
            original_non_null - converted_non_null,
            0,
        )

        df["timestamp"] = converted_timestamp

        timestamp_report.update(
            {
                "original_non_null": original_non_null,
                "converted_non_null": converted_non_null,
                "invalid_values": invalid_values,
            }
        )


    numeric_conversion_report = {}

    for column in NUMERIC_COLUMNS:

        if column not in df.columns:
            continue

        numeric_conversion_report[column] = (
            convert_numeric_column(
                df,
                column,
            )
        )


    wind_direction_report = (
        convert_wind_direction_column(df)
    )


    rows_before_empty_removal = len(df)

    df = df.dropna(
        how="all"
    )

    empty_rows_removed = (
        rows_before_empty_removal - len(df)
    )


    rows_before_duplicate_removal = len(df)

    df = df.drop_duplicates()

    duplicate_rows_removed = (
        rows_before_duplicate_removal - len(df)
    )


    cleaning_report = {
        "original_shape": {
            "rows": original_rows,
            "columns": len(original_columns),
        },
        "final_shape": {
            "rows": len(df),
            "columns": len(df.columns),
        },
        "columns": {
            "original": original_columns,
            "final": list(df.columns),
            "renamed": rename_map,
        },
        "timestamp_conversion": timestamp_report,
        "numeric_conversions": numeric_conversion_report,
        "wind_direction_conversion": wind_direction_report,
        "rows_removed": {
            "empty_rows": empty_rows_removed,
            "duplicate_rows": duplicate_rows_removed,
            "total": (
                empty_rows_removed
                + duplicate_rows_removed
            ),
        },
    }

    return df, cleaning_report