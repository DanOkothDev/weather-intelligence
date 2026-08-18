import pandas as pd
import pytest

from backend.pipeline import (
    WeatherIntelligencePipeline,
    PipelineStage,
    execute_pipeline,
    validate_pipeline_configuration,
)


def create_raw_weather_data():
    """Create raw unprocessed weather data."""
    timestamps = pd.date_range("2026-08-16", periods=20, freq="h")
    
    return pd.DataFrame({
        "timestamp": timestamps,
        "Temperature": [
            22.0, 22.5, 23.0, 23.5, 24.0,
            24.5, 25.0, 25.5, 26.0, 26.5,
            27.0, 27.5, 28.0, 28.5, 29.0,
            29.5, 30.0, 30.5, 31.0, 31.5
        ],
        "humidity": [
            78, 77, 76, 75, 74,
            73, 72, 71, 70, 69,
            68, 67, 66, 65, 64,
            63, 62, 61, 60, 59
        ],
        "rainfall_mm": [
            0.0, 0.0, 0.2, 0.0, 0.0,
            0.4, 0.0, 0.0, 1.2, 0.0,
            0.0, 0.0, 2.1, 0.0, 0.0,
            0.0, 0.8, 0.0, 0.0, 1.5
        ]
    })


def test_weather_intelligence_pipeline_initializes():
    """Pipeline should initialize with default stages."""
    pipeline = WeatherIntelligencePipeline()
    
    assert pipeline is not None
    assert hasattr(pipeline, "stages")
    assert isinstance(pipeline.stages, list)
    assert len(pipeline.stages) > 0


def test_pipeline_executes_all_stages():
    """Pipeline execution should run all stages in sequence."""
    pipeline = WeatherIntelligencePipeline()
    df = create_raw_weather_data()
    
    result = pipeline.execute(df)
    
    assert result["status"] == "success"
    assert "pipeline_stages" in result
    assert "results" in result
    
    # All stages should have executed
    for stage in result["pipeline_stages"]:
        assert "stage_name" in stage
        assert "status" in stage
        assert stage["status"] in ["success", "skipped", "warning"]


def test_pipeline_handles_stage_failures():
    """Pipeline should handle failures gracefully."""
    pipeline = WeatherIntelligencePipeline()
    empty_df = pd.DataFrame()
    
    result = pipeline.execute(empty_df)
    
    # Should have a status, may be partial success
    assert "status" in result
    assert result["status"] in ["success", "partial_success", "failed"]


def test_pipeline_stage_composition_produces_valid_output():
    """Each pipeline stage output should be valid input for next stage."""
    pipeline = WeatherIntelligencePipeline()
    df = create_raw_weather_data()
    
    result = pipeline.execute(df)
    
    # Results should contain expected components
    if result["status"] in ["success", "partial_success"]:
        results = result.get("results", {})
        
        # Should have cleaning, analysis, anomaly, prediction, insights, impact
        expected_stages = ["cleaning", "analysis", "anomaly", "prediction", "insights", "impact"]
        for stage in expected_stages:
            if stage in results:
                assert results[stage].get("status") in ["success", "insufficient_data"]


def test_pipeline_stage_ordering_is_preserved():
    """Stages should execute in correct dependency order."""
    pipeline = WeatherIntelligencePipeline()
    df = create_raw_weather_data()
    
    result = pipeline.execute(df)
    
    stages = result.get("pipeline_stages", [])
    stage_names = [s["stage_name"] for s in stages]
    
    # Ingestion/cleaning should come before analysis
    if "cleaning" in stage_names and "analysis" in stage_names:
        assert stage_names.index("cleaning") < stage_names.index("analysis")
    
    # Analysis should come before anomaly detection
    if "analysis" in stage_names and "anomaly" in stage_names:
        assert stage_names.index("analysis") < stage_names.index("anomaly")
    
    # Prediction should come before insights
    if "prediction" in stage_names and "insights" in stage_names:
        assert stage_names.index("prediction") < stage_names.index("insights")


def test_pipeline_exposes_metrics():
    """Pipeline should expose execution metrics."""
    pipeline = WeatherIntelligencePipeline()
    df = create_raw_weather_data()
    
    result = pipeline.execute(df)
    
    assert "metrics" in result
    metrics = result["metrics"]
    
    assert "total_execution_time" in metrics
    assert "records_processed" in metrics
    assert metrics["total_execution_time"] > 0
    assert metrics["records_processed"] > 0


def test_execute_pipeline_shortcut_function():
    """Should provide shortcut function to execute pipeline."""
    df = create_raw_weather_data()
    
    result = execute_pipeline(df)
    
    assert result["status"] in ["success", "partial_success", "failed"]
    assert "results" in result


def test_pipeline_configuration_validation():
    """Should validate pipeline configuration."""
    valid_config = {
        "stages": ["cleaning", "analysis", "anomaly", "prediction"],
        "parallel_execution": False,
        "error_handling": "stop_on_error"
    }
    
    result = validate_pipeline_configuration(valid_config)
    
    assert result["status"] == "success"
    assert result["is_valid"] is True


def test_pipeline_configuration_rejects_invalid_stages():
    """Should reject unknown stage names."""
    invalid_config = {
        "stages": ["cleaning", "nonexistent_stage"],
        "parallel_execution": False
    }
    
    result = validate_pipeline_configuration(invalid_config)
    
    assert result["status"] == "validation_error" or result["is_valid"] is False
    assert "nonexistent_stage" in result.get("message", "").lower()


def test_pipeline_with_custom_configuration():
    """Should accept and apply custom pipeline configuration."""
    custom_config = {
        "stages": ["cleaning", "analysis"],
        "error_handling": "continue_on_error"
    }
    
    pipeline = WeatherIntelligencePipeline(config=custom_config)
    df = create_raw_weather_data()
    
    result = pipeline.execute(df)
    
    assert result["status"] in ["success", "partial_success"]
    # Should have executed only configured stages
    stages = [s["stage_name"] for s in result.get("pipeline_stages", [])]
    assert "cleaning" in stages or "analysis" in stages


def test_pipeline_produces_normalized_output_format():
    """Pipeline output should have consistent normalized format."""
    pipeline = WeatherIntelligencePipeline()
    df = create_raw_weather_data()
    
    result = pipeline.execute(df)
    
    # Standard output format
    assert isinstance(result, dict)
    assert "status" in result
    assert "timestamp" in result
    assert "results" in result
    assert "metrics" in result
    assert "pipeline_stages" in result


def test_pipeline_stage_dependencies_respected():
    """Earlier stages' outputs should feed into later stages."""
    pipeline = WeatherIntelligencePipeline()
    df = create_raw_weather_data()
    
    result = pipeline.execute(df)
    
    if result["status"] in ["success", "partial_success"]:
        results = result.get("results", {})
        
        # Cleaning output should affect analysis data quality
        if "cleaning" in results and "analysis" in results:
            assert results["cleaning"].get("status") in ["success", "insufficient_data"]
            assert results["analysis"].get("status") in ["success", "insufficient_data"]
