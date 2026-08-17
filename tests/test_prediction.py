import pandas as pd

from backend.prediction import (
    train_prediction_model,
    generate_predictions,
    generate_prediction_report
)


def create_test_data():
    timestamps = pd.date_range(
        "2026-08-16 00:00",
        periods=20,
        freq="h"
    )

    return pd.DataFrame({
        "timestamp": timestamps,

        "temperature": [
            22.0, 22.3, 22.7, 23.1, 23.5,
            23.9, 24.2, 24.6, 25.0, 25.3,
            25.7, 26.0, 26.2, 26.4, 26.5,
            26.7, 26.8, 27.0, 27.1, 27.3
        ],

        "humidity": [
            78, 77, 76, 75, 74,
            73, 72, 71, 70, 69,
            68, 67, 66, 65, 64,
            63, 62, 61, 60, 59
        ],

        "rainfall": [
            0.0, 0.0, 0.2, 0.0, 0.0,
            0.4, 0.0, 0.0, 1.2, 0.0,
            0.0, 0.0, 2.1, 0.0, 0.0,
            0.0, 0.8, 0.0, 0.0, 1.5
        ]
    })


def main():

    df = create_test_data()

    print("\nPREDICTION TEST DATA")
    print(df)

    print("\nTEMPERATURE MODEL")

    model_report = train_prediction_model(
        df,
        "temperature"
    )

    print(model_report)

    print("\nTEMPERATURE FORECAST")

    forecast = generate_predictions(
        df,
        "temperature",
        horizon=5
    )

    print(forecast)

    print("\nFULL WEATHER FORECAST")

    report = generate_prediction_report(
        df,
        horizon=5
    )

    print(report)


if __name__ == "__main__":
    main()