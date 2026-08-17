from pathlib import Path
import shutil

from fastapi import FastAPI, File, HTTPException, UploadFile

from backend.ingestion import (
    IngestionError,
    get_dataset_metadata,
    load_dataset,
)

from backend.cleaning import clean_weather_data
from backend.quality import generate_quality_report
from backend.analysis import generate_analysis
from backend.anomaly import generate_anomaly_report
from backend.impact import generate_impact_insights
from backend.prediction import PredictionError, generate_prediction_report

app = FastAPI(
    title="Weather Intelligence API",
    description="Weather data ingestion and analytics backend",
    version="0.1.0", 
)


UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def root():
    return {
        "name": "Weather Intelligence API",
        "status": "online",
        "version": "0.1.0",
    }


@app.post("/api/data/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload and inspect a weather dataset."""

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    file_path = UPLOAD_DIR / file.filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = load_dataset(str(file_path))

        raw_metadata = get_dataset_metadata(df)

        df = clean_weather_data(df)

        cleaned_metadata = get_dataset_metadata(df)
        quality_report = generate_quality_report(df)
        analysis = generate_analysis(df)
        anomaly_report = generate_anomaly_report(df)
        impact_insights = generate_impact_insights(
            analysis,
            anomaly_report,
        )
        try:
            prediction_report = generate_prediction_report(
                df,
                horizon=5,
            )
        except PredictionError as exc:
            prediction_report = {
                "status": "unavailable",
                "message": str(exc),
            }

        return {
            "message": "Dataset ingested, cleaned, quality-checked, analyzed, and predicted successfully.",
            "filename": file.filename,
            "raw_metadata": raw_metadata,
            "cleaned_metadata": cleaned_metadata,
            "quality_report": quality_report,
            "analysis": analysis,
            "anomaly_report": anomaly_report,
            "impact_insights": impact_insights,
            "prediction": prediction_report,
        }

    except IngestionError as exc:
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected ingestion error: {exc}",
        ) from exc