from pathlib import Path

from backend.ingestion import load_dataset
from backend.cleaning import clean_weather_data
from backend.analysis import generate_analysis


def main():
    dataset_path = Path("data/uploads/weather_mock_data.csv")

    # Load dataset
    df = load_dataset(str(dataset_path))

    print("\nRAW DATA")
    print(df.head())
    print(f"\nRows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # Clean dataset
    df, cleaning_report = clean_weather_data(df)

    print("\nCLEANING REPORT")
    print(cleaning_report)

    print("\nCLEANED DATA")
    print(df.head())

    print("\nCLEANED DATA TYPES")
    print(df.dtypes)

    # Analyze dataset
    result = generate_analysis(df)

    print("\nWEATHER ANALYSIS")
    print(result)


if __name__ == "__main__":
    main()