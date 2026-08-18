import pandas as pd

from backend.analysis import generate_analysis


def test_generate_analysis_detects_available_numeric_weather_variables():
    df = pd.DataFrame({
        "timestamp": [
            "2026-08-16 10:00",
            "2026-08-16 11:00",
            "2026-08-16 12:00",
        ],
        "temperature": [21.2, 22.0, 23.1],
        "humidity": [60, 58, 55],
        "wind_speed": [4.1, 5.0, 4.8],
        "uv_index": [2.0, 2.9, 3.2],
        "cloud_cover": [40, 35, 44],
        "visibility": [8.0, 9.5, 10.2],
        "dew_point": [11.5, 12.2, 13.0],
        "wind_direction": [359, 0, 2],
        "id": [1, 2, 3],
    })

    result = generate_analysis(df)
    stats = result["statistics"]

    assert {"temperature", "humidity", "wind_speed", "uv_index", "cloud_cover", "visibility", "dew_point", "wind_direction"}.issubset(stats)
    assert "id" not in stats


def test_generate_analysis_uses_circular_statistics_for_wind_direction():
    df = pd.DataFrame({
        "timestamp": [
            "2026-08-16 10:00",
            "2026-08-16 11:00",
            "2026-08-16 12:00",
            "2026-08-16 13:00",
        ],
        "wind_direction": [359, 1, 358, 0],
    })

    result = generate_analysis(df)
    stats = result["statistics"]["wind_direction"]

    assert "circular_mean" in stats
    assert "sin_component" in stats
    assert "cos_component" in stats
    assert abs(stats["circular_mean"]) <= 360
    assert abs(stats["sin_component"]) <= 1.0
    assert abs(stats["cos_component"]) <= 1.0