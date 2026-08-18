"""
Weather Intelligence Pipeline Service
Orchestrates the complete weather analysis workflow with dependency management.
"""

import pandas as pd
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from backend.cleaning import clean_weather_data
from backend.analysis import generate_analysis
from backend.anomaly import detect_anomalies, generate_anomaly_report
from backend.prediction import generate_prediction_report
from backend.insights import generate_insights_report
from backend.impact import generate_impact_report


@dataclass
class PipelineStage:
    """Represents a single stage in the pipeline."""
    name: str
    function: callable
    required_columns: List[str] = None
    depends_on: List[str] = None
    skip_on_error: bool = False


class PipelineError(Exception):
    """Custom exception for pipeline errors."""
    pass


class WeatherIntelligencePipeline:
    """
    Orchestrates complete weather analysis pipeline.
    Handles data flow, error handling, and metrics collection.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize pipeline with optional custom configuration."""
        self.config = config or self._get_default_config()
        self.stages = self._setup_stages()
        self.metrics = {}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default pipeline configuration."""
        return {
            "stages": [
                "cleaning",
                "analysis",
                "anomaly",
                "prediction",
                "insights",
                "impact"
            ],
            "error_handling": "stop_on_error",
            "parallel_execution": False,
            "log_metrics": True
        }
    
    def _setup_stages(self) -> List[PipelineStage]:
        """Setup pipeline stages with dependencies."""
        stages_config = self.config.get("stages", [])
        
        all_stages = {
            "cleaning": PipelineStage(
                name="cleaning",
                function=self._stage_cleaning,
                depends_on=[]
            ),
            "analysis": PipelineStage(
                name="analysis",
                function=self._stage_analysis,
                depends_on=["cleaning"]
            ),
            "anomaly": PipelineStage(
                name="anomaly",
                function=self._stage_anomaly,
                depends_on=["cleaning", "analysis"]
            ),
            "prediction": PipelineStage(
                name="prediction",
                function=self._stage_prediction,
                depends_on=["cleaning"]
            ),
            "insights": PipelineStage(
                name="insights",
                function=self._stage_insights,
                depends_on=["prediction"]
            ),
            "impact": PipelineStage(
                name="impact",
                function=self._stage_impact,
                depends_on=["analysis", "anomaly"]
            )
        }
        
        # Build stages in order, only including configured stages
        stages = []
        for stage_name in stages_config:
            if stage_name in all_stages:
                stages.append(all_stages[stage_name])
        
        return stages
    
    def execute(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute complete pipeline on input data."""
        start_time = time.time()
        
        if df is None or len(df) == 0:
            return {
                "status": "failed",
                "message": "Empty or None dataframe provided",
                "timestamp": datetime.now().isoformat(),
                "results": {},
                "metrics": {"total_execution_time": 0}
            }
        
        results = {}
        pipeline_stages = []
        stage_data = {"df": df}
        
        error_handling = self.config.get("error_handling", "stop_on_error")
        
        for stage in self.stages:
            stage_start = time.time()
            stage_result = {
                "stage_name": stage.name,
                "status": "pending",
                "execution_time": 0
            }
            
            try:
                # Check dependencies
                for dep in stage.depends_on or []:
                    if dep not in results:
                        stage_result["status"] = "skipped"
                        stage_result["reason"] = f"Dependency '{dep}' not executed"
                        pipeline_stages.append(stage_result)
                        continue
                
                # Execute stage
                result = stage.function(stage_data, results)
                
                results[stage.name] = result
                stage_data = result.get("data", stage_data)
                
                stage_result["status"] = "success"
                stage_result["message"] = result.get("message", "")
                
            except Exception as e:
                stage_result["status"] = "error"
                stage_result["error"] = str(e)
                
                if error_handling == "stop_on_error":
                    stage_result["status"] = "error"
                    pipeline_stages.append(stage_result)
                    
                    return {
                        "status": "failed",
                        "message": f"Pipeline failed at stage '{stage.name}': {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                        "results": results,
                        "pipeline_stages": pipeline_stages,
                        "metrics": {
                            "total_execution_time": time.time() - start_time,
                            "records_processed": len(df)
                        }
                    }
            
            finally:
                stage_result["execution_time"] = time.time() - stage_start
                pipeline_stages.append(stage_result)
        
        total_time = time.time() - start_time
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "pipeline_stages": pipeline_stages,
            "metrics": {
                "total_execution_time": round(total_time, 3),
                "records_processed": len(df),
                "stages_executed": len(pipeline_stages),
                "stages_successful": len([s for s in pipeline_stages if s["status"] == "success"])
            }
        }
    
    def _stage_cleaning(self, data: Dict, previous_results: Dict) -> Dict:
        """Cleaning stage: normalize schema and data types."""
        df = data.get("df")
        
        if df is None or len(df) == 0:
            return {
                "status": "insufficient_data",
                "message": "No data to clean",
                "data": df
            }
        
        cleaned_df, cleaning_report = clean_weather_data(df)
        
        return {
            "status": "success",
            "message": "",
            "cleaning_report": cleaning_report,
            "data": cleaned_df
        }
    
    def _stage_analysis(self, data: Dict, previous_results: Dict) -> Dict:
        """Analysis stage: compute statistics and correlations."""
        df = data.get("df")
        
        if df is None or len(df) == 0:
            return {
                "status": "insufficient_data",
                "message": "No data to analyze",
                "data": {}
            }
        
        analysis = generate_analysis(df)
        
        return {
            "status": analysis.get("status", "success"),
            "message": "",
            "analysis": analysis,
            "data": analysis
        }
    
    def _stage_anomaly(self, data: Dict, previous_results: Dict) -> Dict:
        """Anomaly stage: detect unusual observations."""
        df = data.get("df")
        
        if df is None or len(df) == 0:
            return {
                "status": "insufficient_data",
                "message": "No data for anomaly detection",
                "data": {}
            }
        
        anomaly_report = generate_anomaly_report(df)
        
        return {
            "status": anomaly_report.get("status", "success"),
            "message": "",
            "anomaly_report": anomaly_report,
            "data": anomaly_report
        }
    
    def _stage_prediction(self, data: Dict, previous_results: Dict) -> Dict:
        """Prediction stage: forecast future weather values."""
        df = data.get("df")
        
        if df is None or len(df) == 0:
            return {
                "status": "insufficient_data",
                "message": "No data for predictions",
                "data": {}
            }
        
        prediction_report = generate_prediction_report(df, horizon=5)
        
        return {
            "status": prediction_report.get("status", "success"),
            "message": "",
            "prediction_report": prediction_report,
            "data": prediction_report
        }
    
    def _stage_insights(self, data: Dict, previous_results: Dict) -> Dict:
        """Insights stage: analyze forecast quality and confidence."""
        prediction_report = data.get("df")
        
        if not prediction_report or not isinstance(prediction_report, dict):
            return {
                "status": "insufficient_data",
                "message": "No predictions available for insights",
                "data": {}
            }
        
        # Extract sample forecast data for insights
        results = prediction_report.get("results", {})
        if not results:
            return {
                "status": "insufficient_data",
                "message": "No prediction results to analyze",
                "data": {}
            }
        
        # Use first available variable for insights
        var_name = list(results.keys())[0] if results else None
        
        if var_name and results[var_name].get("predictions"):
            predictions = results[var_name]["predictions"]
            df_forecast = pd.DataFrame(predictions)
            
            insights = generate_insights_report(df_forecast)
        else:
            insights = {
                "status": "insufficient_data",
                "message": "No valid predictions for insights analysis"
            }
        
        return {
            "status": insights.get("status", "success"),
            "message": "",
            "insights": insights,
            "data": insights
        }
    
    def _stage_impact(self, data: Dict, previous_results: Dict) -> Dict:
        """Impact stage: assess business and public health impacts."""
        analysis = previous_results.get("analysis", {}).get("analysis", {})
        anomaly_report = previous_results.get("anomaly", {}).get("anomaly_report", {})
        
        if not analysis:
            return {
                "status": "insufficient_data",
                "message": "Analysis data required for impact assessment",
                "data": {}
            }
        
        impact_report = generate_impact_report(analysis, anomaly_report)
        
        return {
            "status": impact_report.get("status", "success"),
            "message": "",
            "impact_report": impact_report,
            "data": impact_report
        }


def execute_pipeline(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to execute the pipeline.
    
    Args:
        df: Input weather data
        config: Optional pipeline configuration
    
    Returns:
        Pipeline execution result
    """
    pipeline = WeatherIntelligencePipeline(config=config)
    return pipeline.execute(df)


def validate_pipeline_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate pipeline configuration.
    
    Args:
        config: Pipeline configuration to validate
    
    Returns:
        Validation result
    """
    valid_stages = [
        "cleaning", "analysis", "anomaly", "prediction", "insights", "impact"
    ]
    
    stages = config.get("stages", [])
    
    invalid_stages = [s for s in stages if s not in valid_stages]
    
    if invalid_stages:
        return {
            "status": "validation_error",
            "is_valid": False,
            "message": f"Invalid stages: {', '.join(invalid_stages)}",
            "valid_stages": valid_stages
        }
    
    valid_error_handling = ["stop_on_error", "continue_on_error", "skip_failed_stages"]
    error_handling = config.get("error_handling", "stop_on_error")
    
    if error_handling not in valid_error_handling:
        return {
            "status": "validation_error",
            "is_valid": False,
            "message": f"Invalid error_handling: {error_handling}",
            "valid_options": valid_error_handling
        }
    
    return {
        "status": "success",
        "is_valid": True,
        "message": "Configuration is valid"
    }
