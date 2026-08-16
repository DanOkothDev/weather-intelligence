import pandas as pd

from backend.quality import generate_quality_report


df = pd.DataFrame({
    "timestamp": pd.to_datetime([
        "2026-08-16 10:00",
        "2026-08-16 11:00",
        "2026-08-16 12:00",
        "2026-08-16 12:00",
    ]),
    "temperature": [24.5, 25.1, None, 26.3],
    "humidity": [68, 65, 62, 62],
    "rainfall": [0.0, 0.0, 1.2, 1.2],
})


report = generate_quality_report(df)

print("\nDATA QUALITY REPORT")
print(report)