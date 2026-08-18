from pathlib import Path
import shutil
import json
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.ingestion import (
    IngestionError,
    get_dataset_metadata,
    load_dataset,
)

from backend.cleaning import clean_weather_data
from backend.quality import generate_quality_report
from backend.analysis import generate_analysis
from backend.anomaly import generate_anomaly_report
from backend.impact import generate_impact_report
from backend.prediction import PredictionError, generate_prediction_report
from backend.insights import generate_insights_report
from backend.pipeline import execute_pipeline, validate_pipeline_configuration
from backend.api_utils import serialize_response

app = FastAPI(
    title="Weather Intelligence API",
    description="Weather data ingestion and analytics backend",
    version="0.2.0", 
)


UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def root():
    """Root endpoint showing API status and version."""
    return serialize_response({
        "name": "Weather Intelligence API",
        "status": "online",
        "version": "0.2.0",
        "endpoints": {
            "health": "GET /health",
            "upload": "POST /api/data/upload",
            "analyze": "POST /api/analyze",
            "predictions": "POST /api/predictions",
            "anomalies": "POST /api/anomalies",
            "insights": "POST /api/insights",
            "impact": "POST /api/impact",
            "quality": "POST /api/quality"
        }
    })


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return serialize_response({"status": "healthy", "service": "weather-intelligence"})


@app.post("/api/data/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload and inspect a weather dataset.
    
    Executes the complete analysis pipeline on the uploaded file.
    Returns raw metadata, cleaning report, analysis, anomalies, predictions, and impact.
    """

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

        # Execute complete pipeline
        df_cleaned, cleaning_report = clean_weather_data(df)
        cleaned_metadata = get_dataset_metadata(df_cleaned)
        quality_report = generate_quality_report(df_cleaned)
        analysis = generate_analysis(df_cleaned)
        anomaly_report = generate_anomaly_report(df_cleaned)
        
        impact_report = generate_impact_report(analysis, anomaly_report)
        
        try:
            prediction_report = generate_prediction_report(
                df_cleaned,
                horizon=5,
            )
        except PredictionError as exc:
            prediction_report = {
                "status": "unavailable",
                "message": str(exc),
            }

        return serialize_response({
            "status": "success",
            "message": "Dataset ingested, cleaned, quality-checked, analyzed, predicted, and impact-assessed successfully.",
            "filename": file.filename,
            "raw_metadata": raw_metadata,
            "cleaning_report": cleaning_report,
            "cleaned_metadata": cleaned_metadata,
            "quality_report": quality_report,
            "analysis": analysis,
            "anomaly_report": anomaly_report,
            "prediction_report": prediction_report,
            "impact_report": impact_report,
        })

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


@app.post("/api/analyze")
async def full_analysis(file: UploadFile = File(...)):
    """Execute complete weather intelligence pipeline.
    
    Performs: data cleaning → analysis → anomaly detection → 
    prediction → insights → impact assessment
    
    Returns aggregated results from all pipeline stages.
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_path = UPLOAD_DIR / file.filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = load_dataset(str(file_path))
        
        # Execute full pipeline with orchestration
        pipeline_result = execute_pipeline(df)
        
        return serialize_response({
            "status": pipeline_result.get("status"),
            "timestamp": pipeline_result.get("timestamp"),
            "filename": file.filename,
            "pipeline_stages": pipeline_result.get("pipeline_stages", []),
            "results": pipeline_result.get("results", {}),
            "metrics": pipeline_result.get("metrics", {})
        })

    except Exception as exc:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/predictions")
async def generate_predictions(file: UploadFile = File(...), horizon: int = 5):
    """Generate weather predictions for specified horizon.
    
    Args:
        file: CSV file with historical weather data
        horizon: Number of time periods to forecast (default: 5)
    
    Returns:
        Prediction report with point estimates, confidence intervals, and metrics.
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_path = UPLOAD_DIR / file.filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = load_dataset(str(file_path))
        df_cleaned, _ = clean_weather_data(df)
        
        prediction_report = generate_prediction_report(df_cleaned, horizon=horizon)
        
        return serialize_response({
            "status": prediction_report.get("status", "success"),
            "filename": file.filename,
            "horizon": horizon,
            "prediction_report": prediction_report
        })

    except Exception as exc:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/anomalies")
async def detect_weather_anomalies(
    file: UploadFile = File(...),
    warning_threshold: float = 2.0,
    anomaly_threshold: float = 3.0
):
    """Detect anomalous weather observations.
    
    Args:
        file: CSV file with weather data
        warning_threshold: Z-score threshold for warning severity (default: 2.0)
        anomaly_threshold: Z-score threshold for critical severity (default: 3.0)
    
    Returns:
        Anomaly report with identified outliers and severity levels.
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_path = UPLOAD_DIR / file.filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = load_dataset(str(file_path))
        df_cleaned, _ = clean_weather_data(df)
        
        anomaly_report = generate_anomaly_report(
            df_cleaned,
            warning_threshold=warning_threshold,
            anomaly_threshold=anomaly_threshold
        )
        
        return serialize_response({
            "status": anomaly_report.get("status", "success"),
            "filename": file.filename,
            "warning_threshold": warning_threshold,
            "anomaly_threshold": anomaly_threshold,
            "anomaly_report": anomaly_report
        })

    except Exception as exc:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/insights")
async def forecast_insights(file: UploadFile = File(...), confidence_level: float = 0.95):
    """Analyze forecast quality with confidence intervals and trend analysis.
    
    Args:
        file: CSV file with predictions and actual values
        confidence_level: Statistical confidence level for intervals (default: 0.95)
    
    Returns:
        Forecast insights including confidence intervals, trend detection, and anomalies.
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_path = UPLOAD_DIR / file.filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = load_dataset(str(file_path))
        df_cleaned, _ = clean_weather_data(df)
        
        # Analyze forecast quality if forecast data is available
        try:
            insights_report = generate_insights_report(df_cleaned)
        except Exception:
            # If forecast columns not present, return basic success with message
            insights_report = {
                "status": "success",
                "message": "Insights analysis requires forecast data columns",
                "data": get_dataset_metadata(df_cleaned)
            }
        
        return serialize_response({
            "status": insights_report.get("status", "success"),
            "filename": file.filename,
            "confidence_level": confidence_level,
            "insights_report": insights_report
        })

    except Exception as exc:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/impact")
async def business_impact_assessment(file: UploadFile = File(...)):
    """Assess business and public health impacts of weather patterns.
    
    Args:
        file: CSV file with weather data
    
    Returns:
        Impact report with risk scoring, sector analysis, and recommendations.
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_path = UPLOAD_DIR / file.filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = load_dataset(str(file_path))
        df_cleaned, _ = clean_weather_data(df)
        
        analysis = generate_analysis(df_cleaned)
        anomaly_report = generate_anomaly_report(df_cleaned)
        
        impact_report = generate_impact_report(analysis, anomaly_report)
        
        return serialize_response({
            "status": impact_report.get("status", "success"),
            "filename": file.filename,
            "impact_report": impact_report
        })

    except Exception as exc:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/quality")
async def data_quality_assessment(file: UploadFile = File(...)):
    """Assess data quality metrics and completeness.
    
    Args:
        file: CSV file with weather data
    
    Returns:
        Quality report with missing values, outliers, and data profile.
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_path = UPLOAD_DIR / file.filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = load_dataset(str(file_path))
        df_cleaned, cleaning_report = clean_weather_data(df)
        
        quality_report = generate_quality_report(df_cleaned)
        
        return serialize_response({
            "status": "success",
            "filename": file.filename,
            "cleaning_report": cleaning_report,
            "quality_report": quality_report
        })

    except Exception as exc:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/pipeline/validate")
async def validate_pipeline_config(config: Optional[dict] = None):
    """Validate pipeline configuration.
    
    Args:
        config: Pipeline configuration dict with 'stages' and 'error_handling'
    
    Returns:
        Validation result with is_valid flag and any error messages.
    """
    
    if config is None:
        config = {
            "stages": ["cleaning", "analysis", "anomaly", "prediction", "insights", "impact"],
            "error_handling": "stop_on_error"
        }
    
    validation_result = validate_pipeline_configuration(config)
    
    return serialize_response({
        "config": config,
        "validation": validation_result
    })


@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """Get summary metrics about the API and services."""
    return serialize_response({
        "service": "weather-intelligence",
        "version": "0.2.0",
        "upload_directory": str(UPLOAD_DIR),
        "status": "operational"
    })
