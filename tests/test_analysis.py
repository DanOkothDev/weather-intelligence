import pandas as pd

from backend.analysis import generate_analysis


df = pd.DataFrame({
    "timestamp": pd.to_datetime([
        "2026-08-16 10:00",
        "2026-08-16 11:00",
        "2026-08-16 12:00",
        "2026-08-16 13:00",
    ]),
    "temperature": [24.5, 25.1, 26.3, 25.8],
    "humidity": [68, 65, 62, 70],
    "rainfall": [0.0, 0.0, 1.2, 3.4],
})


result = generate_analysis(df)

print("\nWEATHER ANALYSIS")
print(result)