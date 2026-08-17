import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


class PredictionError(Exception):
    """Raised when prediction cannot be performed."""
    pass


WEATHER_VARIABLES = [
    "temperature",
    "humidity",
    "rainfall"
]


def prepare_features(df: pd.DataFrame, target: str, lags: int = 3):
    """
    Prepare time-series features for prediction.

    Creates:
    - lag features
    - hour
    - day
    - month
    """

    if target not in df.columns:
        raise PredictionError(
            f"Required variable '{target}' was not found in the dataset."
        )

    if "timestamp" not in df.columns:
        raise PredictionError(
            "A 'timestamp' column is required for prediction."
        )

    data = df.copy()

    data = data.sort_values("timestamp").reset_index(drop=True)

    # Time-based features
    data["hour"] = data["timestamp"].dt.hour
    data["day"] = data["timestamp"].dt.day
    data["month"] = data["timestamp"].dt.month

    # Lag features
    for lag in range(1, lags + 1):
        data[f"{target}_lag_{lag}"] = data[target].shift(lag)

    # Remove rows where lag values don't exist
    data = data.dropna().reset_index(drop=True)

    feature_columns = [
        "hour",
        "day",
        "month"
    ]

    feature_columns += [
        f"{target}_lag_{lag}"
        for lag in range(1, lags + 1)
    ]


    X = data[feature_columns]
    y = data[target]

    return X, y, feature_columns


def train_prediction_model(
    df: pd.DataFrame,
    target: str,
    lags: int = 3
):
    """
    Train a Random Forest regression model for one weather variable.
    """

    valid_data = df[[col for col in df.columns]].copy()

    valid_data = valid_data.dropna(
        subset=["timestamp", target]
    )

    if len(valid_data) < 10:
        return {
            "status": "insufficient_data",
            "message": (
                "At least 10 valid records are required "
                "for prediction."
            ),
            "records_available": len(valid_data)
        }

    X, y, feature_columns = prepare_features(
        valid_data,
        target,
        lags
    )

    if len(X) < 8:
        return {
            "status": "insufficient_data",
            "message": (
                "Not enough records remain after "
                "creating lag features."
            ),
            "records_available": len(X)
        }

    # Time-aware split.
    # The first 80% is training data.
    # The final 20% is testing data.
    split_index = int(len(X) * 0.8)

    if split_index <= 0 or split_index >= len(X):
        raise PredictionError(
            "Unable to create a valid time-based train/test split."
        )

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    return {
        "status": "success",
        "model": "RandomForestRegressor",
        "target": target,
        "records_used": len(X),
        "training_records": len(X_train),
        "testing_records": len(X_test),
        "metrics": {
            "mae": round(float(mae), 4),
            "rmse": round(float(rmse), 4)
        },
        "feature_columns": feature_columns
    }


def generate_predictions(
    df: pd.DataFrame,
    target: str,
    horizon: int = 3,
    lags: int = 3
):
    """
    Generate future predictions for a weather variable.
    """

    valid_data = df.dropna(
        subset=["timestamp", target]
    ).copy()

    valid_data = valid_data.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    if len(valid_data) < 10:
        return {
            "status": "insufficient_data",
            "message": (
                "At least 10 valid records are required "
                "for prediction."
            ),
            "predictions": []
        }

    X, y, feature_columns = prepare_features(
        valid_data,
        target,
        lags
    )

    if len(X) < 8:
        return {
            "status": "insufficient_data",
            "message": "Not enough data after feature preparation.",
            "predictions": []
        }

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    history = valid_data[target].tolist()

    last_timestamp = valid_data["timestamp"].iloc[-1]

    # Determine sampling frequency
    timestamps = valid_data["timestamp"]

    if len(timestamps) >= 2:
        frequency = timestamps.iloc[-1] - timestamps.iloc[-2]
    else:
        frequency = pd.Timedelta(hours=1)

    predictions = []

    for step in range(1, horizon + 1):

        future_timestamp = (
            last_timestamp + frequency * step
        )

        feature_data = {
            "hour": future_timestamp.hour,
            "day": future_timestamp.day,
            "month": future_timestamp.month
        }

        # Latest lag values
        for lag in range(1, lags + 1):

            if len(history) >= lag:
                feature_data[
                    f"{target}_lag_{lag}"
                ] = history[-lag]

            else:
                feature_data[
                    f"{target}_lag_{lag}"
                ] = history[0]

        feature_row = pd.DataFrame(
            [feature_data]
        )

        # Ensure exact feature ordering
        feature_row = feature_row[
            [
                column
                for column in feature_columns
                if column in feature_row.columns
            ]
        ]

        prediction = float(
            model.predict(feature_row)[0]
        )

        predictions.append({
            "timestamp": future_timestamp.isoformat(),
            "value": round(prediction, 3)
        })

        # Feed prediction back into history
        # so the next prediction can use it.
        history.append(prediction)

    return {
        "status": "success",
        "target": target,
        "model": "RandomForestRegressor",
        "forecast_horizon": horizon,
        "frequency": str(frequency),
        "predictions": predictions
    }


def generate_prediction_report(
    df: pd.DataFrame,
    horizon: int = 3
):
    """
    Generate predictions for all supported weather variables.
    """

    report = {
        "forecast_horizon": horizon,
        "variables_analyzed": [],
        "results": {}
    }

    for variable in WEATHER_VARIABLES:

        if variable not in df.columns:
            continue

        report["variables_analyzed"].append(variable)

        result = generate_predictions(
            df,
            variable,
            horizon=horizon
        )

        report["results"][variable] = result

    if not report["variables_analyzed"]:
        raise PredictionError(
            "No supported weather variables were found."
        )

    return report