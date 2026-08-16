import pandas as pd

from backend.cleaning import (
    detect_weather_columns,
    clean_weather_data,
)


df = pd.DataFrame({
    "Date Time": [
        "2026-08-16 10:00",
        "2026-08-16 11:00",
        "2026-08-16 12:00",
    ],
    "Temp": [24.5, 25.1, 26.3],
    "RH": [68, 65, 62],
    "Rain": [0, 0, 1.2],
})


print("\nDETECTED COLUMNS")
print(detect_weather_columns(df))

print("\nCLEANED DATA")
cleaned = clean_weather_data(df)

print(cleaned)

print("\nDATA TYPES")
print(cleaned.dtypes)