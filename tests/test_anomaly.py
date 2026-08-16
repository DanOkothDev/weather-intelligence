import pandas as pd

from backend.anomaly import generate_anomaly_report


df = pd.DataFrame({
    "timestamp": pd.date_range(
        "2026-08-16 00:00",
        periods=10,
        freq="h",
    ),

    "temperature": [
        24.5,
        24.8,
        25.1,
        25.0,
        25.3,
        25.2,
        25.4,
        25.1,
        25.5,
        40.0,
    ],

    "humidity": [
        68,
        67,
        66,
        65,
        64,
        66,
        67,
        65,
        64,
        63,
    ],

    "rainfall": [
        0.0,
        0.0,
        0.2,
        0.0,
        0.4,
        0.0,
        0.1,
        0.0,
        0.0,
        0.3,
    ],
})


report = generate_anomaly_report(df)

print("\nANOMALY REPORT")
print(report)