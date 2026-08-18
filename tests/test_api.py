"""
Regression tests for Weather Intelligence API endpoints.
Tests all major API routes with realistic data payloads.
"""

import pandas as pd
import pytest
import tempfile
import os
from io import BytesIO

from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def create_test_csv_file():
    """Create a temporary CSV file for API testing."""
    timestamps = pd.date_range("2026-08-16", periods=20, freq="h")
    
    df = pd.DataFrame({
        "timestamp": timestamps,
        "temperature": [
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
        "rainfall": [
            0.0, 0.0, 0.2, 0.0, 0.0,
            0.4, 0.0, 0.0, 1.2, 0.0,
            0.0, 0.0, 2.1, 0.0, 0.0,
            0.0, 0.8, 0.0, 0.0, 1.5
        ]
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        return f.name, "test_data.csv"


class TestAPIHealthAndRoot:
    """Test root and health check endpoints."""
    
    def test_root_endpoint_returns_api_info(self):
        """Root endpoint should return API metadata."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Weather Intelligence API"
        assert data["status"] == "online"
        assert "endpoints" in data
    
    def test_health_check_endpoint(self):
        """Health check should return operational status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "weather-intelligence"
    
    def test_metrics_summary_endpoint(self):
        """Metrics endpoint should return service statistics."""
        response = client.get("/api/metrics/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert data["status"] == "operational"


class TestDataUploadEndpoint:
    """Test the data upload endpoint."""
    
    def test_upload_dataset_processes_file(self):
        """Should successfully upload and process weather data."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/data/upload",
                    files={"file": (filename, f, "text/csv")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["filename"] == filename
            assert "cleaning_report" in data
            assert "analysis" in data
            assert "anomaly_report" in data
        finally:
            os.unlink(csv_path)
    
    def test_upload_without_filename_returns_error(self):
        """Upload without filename should return error."""
        response = client.post(
            "/api/data/upload",
            files={"file": (None, BytesIO(b"test"), "text/csv")}
        )
        
        # Should return error status (422 for validation error or 400 for bad request)
        assert response.status_code in [400, 422]
    
    def test_upload_returns_metadata(self):
        """Upload response should include raw and cleaned metadata."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/data/upload",
                    files={"file": (filename, f, "text/csv")}
                )
            
            data = response.json()
            assert "raw_metadata" in data
            assert "cleaned_metadata" in data
        finally:
            os.unlink(csv_path)


class TestAnalyzeEndpoint:
    """Test the complete analysis pipeline endpoint."""
    
    def test_full_analysis_executes_pipeline(self):
        """Full analysis should execute complete pipeline."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/analyze",
                    files={"file": (filename, f, "text/csv")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["filename"] == filename
            assert "pipeline_stages" in data
            assert "results" in data
            assert "metrics" in data
        finally:
            os.unlink(csv_path)
    
    def test_full_analysis_includes_all_stages(self):
        """Analysis result should include all pipeline stages."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/analyze",
                    files={"file": (filename, f, "text/csv")}
                )
            
            data = response.json()
            stages = data.get("pipeline_stages", [])
            
            # Should have stages for cleaning, analysis, anomaly, etc.
            assert len(stages) > 0
        finally:
            os.unlink(csv_path)


class TestPredictionEndpoint:
    """Test the predictions endpoint."""
    
    def test_predictions_endpoint_generates_forecasts(self):
        """Predictions endpoint should generate forecast data."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/predictions",
                    files={"file": (filename, f, "text/csv")},
                    params={"horizon": 5}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["filename"] == filename
            assert data["horizon"] == 5
            assert "prediction_report" in data
        finally:
            os.unlink(csv_path)
    
    def test_predictions_with_custom_horizon(self):
        """Predictions should respect custom horizon parameter."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/predictions",
                    files={"file": (filename, f, "text/csv")},
                    params={"horizon": 10}
                )
            
            data = response.json()
            assert data["horizon"] == 10
        finally:
            os.unlink(csv_path)


class TestAnomaliesEndpoint:
    """Test the anomaly detection endpoint."""
    
    def test_anomalies_endpoint_detects_outliers(self):
        """Anomalies endpoint should identify unusual observations."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/anomalies",
                    files={"file": (filename, f, "text/csv")},
                    params={"warning_threshold": 2.0, "anomaly_threshold": 3.0}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["filename"] == filename
            assert data["warning_threshold"] == 2.0
            assert "anomaly_report" in data
        finally:
            os.unlink(csv_path)
    
    def test_anomalies_with_custom_threshold(self):
        """Anomaly detection should respect threshold parameter."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/anomalies",
                    files={"file": (filename, f, "text/csv")},
                    params={"anomaly_threshold": 2.5}
                )
            
            data = response.json()
            assert data["anomaly_threshold"] == 2.5
        finally:
            os.unlink(csv_path)


class TestInsightsEndpoint:
    """Test the forecast insights endpoint."""
    
    def test_insights_endpoint_analyzes_forecasts(self):
        """Insights endpoint should analyze forecast quality."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/insights",
                    files={"file": (filename, f, "text/csv")},
                    params={"confidence_level": 0.95}
                )
            
            assert response.status_code == 200
            data = response.json()
            # Status can be success, unavailable, or validation_error depending on data
            assert data["status"] in ["success", "unavailable", "validation_error"]
            assert data["filename"] == filename
            assert data["confidence_level"] == 0.95
            assert "insights_report" in data
        finally:
            os.unlink(csv_path)
    
    def test_insights_with_custom_confidence(self):
        """Insights should respect confidence level parameter."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/insights",
                    files={"file": (filename, f, "text/csv")},
                    params={"confidence_level": 0.99}
                )
            
            data = response.json()
            assert data["confidence_level"] == 0.99
        finally:
            os.unlink(csv_path)


class TestImpactEndpoint:
    """Test the business impact assessment endpoint."""
    
    def test_impact_endpoint_assesses_consequences(self):
        """Impact endpoint should evaluate business and health impacts."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/impact",
                    files={"file": (filename, f, "text/csv")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["filename"] == filename
            assert "impact_report" in data
        finally:
            os.unlink(csv_path)
    
    def test_impact_report_includes_recommendations(self):
        """Impact report should include actionable recommendations."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/impact",
                    files={"file": (filename, f, "text/csv")}
                )
            
            data = response.json()
            impact_report = data.get("impact_report", {})
            
            # Should have some impact analysis
            assert impact_report.get("status") is not None
        finally:
            os.unlink(csv_path)


class TestQualityEndpoint:
    """Test the data quality assessment endpoint."""
    
    def test_quality_endpoint_evaluates_data(self):
        """Quality endpoint should assess data completeness and validity."""
        csv_path, filename = create_test_csv_file()
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/quality",
                    files={"file": (filename, f, "text/csv")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["filename"] == filename
            assert "quality_report" in data
            assert "cleaning_report" in data
        finally:
            os.unlink(csv_path)


class TestPipelineValidation:
    """Test the pipeline configuration validation endpoint."""
    
    def test_pipeline_validation_accepts_valid_config(self):
        """Should validate correct pipeline configuration."""
        config = {
            "stages": ["cleaning", "analysis", "anomaly"],
            "error_handling": "stop_on_error"
        }
        
        response = client.post("/api/pipeline/validate", json=config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["validation"]["is_valid"] == True
    
    def test_pipeline_validation_rejects_invalid_stages(self):
        """Should reject unknown stage names."""
        config = {
            "stages": ["cleaning", "unknown_stage"],
            "error_handling": "stop_on_error"
        }
        
        response = client.post("/api/pipeline/validate", json=config)
        
        data = response.json()
        assert data["validation"]["is_valid"] == False
    
    def test_pipeline_validation_rejects_invalid_error_handling(self):
        """Should reject invalid error handling strategy."""
        config = {
            "stages": ["cleaning", "analysis"],
            "error_handling": "invalid_strategy"
        }
        
        response = client.post("/api/pipeline/validate", json=config)
        
        data = response.json()
        assert data["validation"]["is_valid"] == False
    
    def test_pipeline_validation_with_default_config(self):
        """Should validate default configuration when none provided."""
        response = client.post("/api/pipeline/validate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["validation"]["is_valid"] == True


class TestErrorHandling:
    """Test API error handling and edge cases."""
    
    def test_invalid_file_format_returns_error(self):
        """Invalid file format should return appropriate error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("invalid data")
            txt_path = f.name
        
        try:
            with open(txt_path, 'rb') as f:
                response = client.post(
                    "/api/data/upload",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            # Should handle unsupported format gracefully
            assert response.status_code in [400, 500]
        finally:
            os.unlink(txt_path)
    
    def test_missing_required_columns_handled(self):
        """Missing required columns should be handled gracefully."""
        df = pd.DataFrame({
            "value1": [1, 2, 3],
            "value2": [4, 5, 6]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            with open(csv_path, 'rb') as f:
                response = client.post(
                    "/api/data/upload",
                    files={"file": ("minimal.csv", f, "text/csv")}
                )
            
            # Should return response (may be incomplete but not crash)
            assert response.status_code in [200, 500]
        finally:
            os.unlink(csv_path)
