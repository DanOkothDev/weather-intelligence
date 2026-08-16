import pandas as pd


def generate_quality_report(df: pd.DataFrame) -> dict:
    """Generate a data-quality report for a weather dataset."""

    total_cells = df.shape[0] * df.shape[1]

    missing_cells = int(df.isna().sum().sum())

    missing_percentage = (
        (missing_cells / total_cells) * 100
        if total_cells > 0
        else 0
    )

    duplicate_rows = int(df.duplicated().sum())

    report = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "total_cells": int(total_cells),
        "missing_cells": missing_cells,
        "missing_percentage": round(missing_percentage, 2),
        "duplicate_rows": duplicate_rows,
        "columns": {},
    }

    for column in df.columns:

        column_report = {
            "dtype": str(df[column].dtype),
            "missing": int(df[column].isna().sum()),
            "unique_values": int(df[column].nunique()),
        }

        if pd.api.types.is_numeric_dtype(df[column]):
            column_report["min"] = (
                float(df[column].min())
                if not df[column].dropna().empty
                else None
            )

            column_report["max"] = (
                float(df[column].max())
                if not df[column].dropna().empty
                else None
            )

            column_report["mean"] = (
                float(df[column].mean())
                if not df[column].dropna().empty
                else None
            )

        report["columns"][column] = column_report

    return report