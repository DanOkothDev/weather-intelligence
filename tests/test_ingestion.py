from backend.ingestion import load_dataset, get_dataset_metadata


df = load_dataset("data/test/weather.csv")

print("\nDATASET")
print(df)

print("\nMETADATA")
print(get_dataset_metadata(df))