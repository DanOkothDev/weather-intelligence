"""
Impact Intelligence Module
Generates actionable impact insights, business assessments, and risk tracking.
"""

from typing import Any


def generate_impact_insights(
    analysis: dict[str, Any],
    anomaly_report: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Convert weather analysis and anomaly information into
    actionable impact insights.
    """

    insights = []

    statistics = analysis.get("statistics", {})
    anomalies = anomaly_report.get("results", {})

    temperature = statistics.get("temperature")
    humidity = statistics.get("humidity")
    rainfall = statistics.get("rainfall")


    if temperature:

        maximum = temperature.get("maximum")
        mean = temperature.get("mean")

        if maximum is not None and maximum >= 35:
            insights.append({
                "category": "heat",
                "severity": "high",
                "title": "High temperature detected",
                "message": (
                    f"Maximum temperature reached {maximum}°C. "
                    "This may increase heat-stress risk and water demand."
                ),
                "recommendation": (
                    "Increase hydration monitoring and consider "
                    "additional cooling or irrigation measures."
                ),
            })

        elif maximum is not None and maximum >= 30:
            insights.append({
                "category": "heat",
                "severity": "moderate",
                "title": "Elevated temperature",
                "message": (
                    f"Maximum temperature reached {maximum}°C."
                ),
                "recommendation": (
                    "Monitor heat conditions and water requirements."
                ),
            })


    if humidity:

        maximum = humidity.get("maximum")

        if maximum is not None and maximum >= 85:
            insights.append({
                "category": "humidity",
                "severity": "moderate",
                "title": "High humidity detected",
                "message": (
                    f"Humidity reached {maximum}%. "
                    "Persistently high humidity can increase "
                    "crop disease and mold risk."
                ),
                "recommendation": (
                    "Monitor crops and ventilation conditions."
                ),
            })

   

    if rainfall:

        maximum = rainfall.get("maximum")
        total = rainfall.get("total")

        if maximum is not None and maximum >= 50:
            insights.append({
                "category": "flooding",
                "severity": "high",
                "title": "Heavy rainfall detected",
                "message": (
                    f"Maximum recorded rainfall reached {maximum} mm."
                ),
                "recommendation": (
                    "Monitor drainage systems, rivers, and "
                    "low-lying areas for possible flooding."
                ),
            })

        elif maximum is not None and maximum >= 20:
            insights.append({
                "category": "rainfall",
                "severity": "moderate",
                "title": "Significant rainfall detected",
                "message": (
                    f"Maximum recorded rainfall reached {maximum} mm."
                ),
                "recommendation": (
                    "Monitor runoff, drainage, and soil conditions."
                ),
            })

        elif total is not None and total == 0:
            insights.append({
                "category": "drought",
                "severity": "moderate",
                "title": "No rainfall recorded",
                "message": (
                    "No rainfall was recorded in the analyzed period."
                ),
                "recommendation": (
                    "Monitor soil moisture and water availability."
                ),
            })


    for variable, result in anomalies.items():

        if result.get("status") == "critical":

            insights.append({
                "category": "anomaly",
                "severity": "high",
                "title": f"Critical {variable} conditions",
                "message": (
                    f"A critical {variable} observation was detected "
                    "relative to the dataset baseline."
                ),
                "recommendation": (
                    f"Immediately investigate the {variable} measurement and "
                    "take corrective action to mitigate risk."
                ),
            })

        elif result.get("status") == "warning":

            insights.append({
                "category": "anomaly",
                "severity": "moderate",
                "title": f"{variable.capitalize()} requires attention",
                "message": (
                    f"A potentially unusual {variable} observation "
                    "was detected."
                ),
                "recommendation": (
                    "Continue monitoring future observations and assess trends."
                ),
            })

    if not insights:
        insights.append({
            "category": "general",
            "severity": "low",
            "title": "Weather conditions appear stable",
            "message": (
                "No major weather-impact conditions were identified "
                "from the available dataset."
            ),
            "recommendation": (
                "Continue monitoring weather observations."
            ),
        })

    return insights


def calculate_impact_score(
    analysis: dict[str, Any],
    anomaly_report: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate quantitative impact score (0-100).
    """
    
    component_scores = {
        "temperature": 0,
        "humidity": 0,
        "rainfall": 0,
        "anomalies": 0
    }
    
    statistics = analysis.get("statistics", {})
    
    # Temperature impact
    temp = statistics.get("temperature", {})
    temp_max = temp.get("maximum", 0)
    if temp_max >= 40:
        component_scores["temperature"] = 30
    elif temp_max >= 35:
        component_scores["temperature"] = 20
    elif temp_max >= 30:
        component_scores["temperature"] = 10
    
    # Humidity impact
    humidity = statistics.get("humidity", {})
    humid_max = humidity.get("maximum", 0)
    if humid_max >= 90:
        component_scores["humidity"] = 25
    elif humid_max >= 85:
        component_scores["humidity"] = 15
    elif humid_max >= 75:
        component_scores["humidity"] = 5
    
    # Rainfall impact
    rainfall = statistics.get("rainfall", {})
    rain_max = rainfall.get("maximum", 0)
    rain_total = rainfall.get("total", 0)
    
    if rain_max >= 60:
        component_scores["rainfall"] = 25
    elif rain_max >= 40:
        component_scores["rainfall"] = 15
    elif rain_total == 0:
        component_scores["rainfall"] = 10
    
    # Anomaly impact
    anomalies = anomaly_report.get("results", {})
    critical_count = sum(1 for r in anomalies.values() if r.get("status") == "critical")
    warning_count = sum(1 for r in anomalies.values() if r.get("status") == "warning")
    
    component_scores["anomalies"] = min(20, critical_count * 10 + warning_count * 3)
    
    overall = min(100, sum(component_scores.values()))
    
    return {
        "status": "success",
        "overall_score": overall,
        "component_scores": component_scores
    }


def assess_business_impact(
    analysis: dict[str, Any],
    anomaly_report: dict[str, Any],
) -> dict[str, Any]:
    """
    Assess impact across business sectors (agriculture, energy, health).
    """
    
    score = calculate_impact_score(analysis, anomaly_report)
    overall_impact = score["overall_score"]
    
    # Risk level mapping
    if overall_impact >= 70:
        risk_level = "high"
    elif overall_impact >= 40:
        risk_level = "moderate"
    else:
        risk_level = "low"
    
    sectors = [
        {
            "name": "agriculture",
            "risk_level": risk_level,
            "impact_description": (
                f"Crop yield and soil health affected by temperature, "
                f"rainfall, and humidity conditions (Score: {overall_impact})"
            ),
            "affected_operations": ["irrigation", "crop_protection", "harvest_timing"]
        },
        {
            "name": "energy",
            "risk_level": risk_level,
            "impact_description": (
                f"Electricity demand and renewable generation affected by weather (Score: {overall_impact})"
            ),
            "affected_operations": ["demand_forecast", "grid_stability", "solar_generation"]
        },
        {
            "name": "public_health",
            "risk_level": risk_level if overall_impact > 50 else "low",
            "impact_description": (
                f"Heat stress and disease transmission risk influenced by temperature and humidity"
            ),
            "affected_operations": ["emergency_response", "disease_monitoring", "heat_alerts"]
        }
    ]
    
    economic_impact = overall_impact * 10000 if overall_impact >= 50 else overall_impact * 1000
    
    return {
        "status": "success",
        "sectors": sectors,
        "economic_impact_estimate": {
            "currency": "USD",
            "low_estimate": int(economic_impact * 0.5),
            "high_estimate": int(economic_impact * 2.0),
            "confidence": 0.6
        }
    }


def track_risk_accumulation(
    analysis: dict[str, Any],
    anomaly_report: dict[str, Any],
) -> dict[str, Any]:
    """
    Track cumulative risk from multiple factors.
    """
    
    risk_factors = []
    statistics = analysis.get("statistics", {})
    anomalies = anomaly_report.get("results", {})
    
    # Temperature risk
    temp = statistics.get("temperature", {})
    temp_risk = min(30, max(0, (temp.get("maximum", 0) - 25) * 2))
    if temp_risk > 0:
        risk_factors.append({
            "factor": "high_temperature",
            "score": temp_risk,
            "description": f"Maximum temperature of {temp.get('maximum')}°C"
        })
    
    # Humidity risk
    humidity = statistics.get("humidity", {})
    humid_risk = min(25, max(0, (humidity.get("maximum", 50) - 70) * 0.5))
    if humid_risk > 0:
        risk_factors.append({
            "factor": "high_humidity",
            "score": humid_risk,
            "description": f"Maximum humidity of {humidity.get('maximum')}%"
        })
    
    # Rainfall risk
    rainfall = statistics.get("rainfall", {})
    rain_risk = min(25, max(0, rainfall.get("maximum", 0) * 0.4))
    if rain_risk > 0:
        risk_factors.append({
            "factor": "extreme_rainfall",
            "score": rain_risk,
            "description": f"Maximum rainfall of {rainfall.get('maximum')} mm"
        })
    
    # Anomaly risk
    for var, result in anomalies.items():
        if result.get("status") == "critical":
            risk_factors.append({
                "factor": f"{var}_anomaly",
                "score": 15,
                "description": f"Critical anomaly detected in {var}"
            })
        elif result.get("status") == "warning":
            risk_factors.append({
                "factor": f"{var}_warning",
                "score": 5,
                "description": f"Warning-level anomaly in {var}"
            })
    
    # Sort by score descending
    risk_factors = sorted(risk_factors, key=lambda x: x["score"], reverse=True)
    
    cumulative_risk = sum(rf["score"] for rf in risk_factors)
    
    return {
        "status": "success",
        "cumulative_risk_score": cumulative_risk,
        "risk_factors": risk_factors,
        "critical_risk_threshold_exceeded": cumulative_risk > 70
    }


def generate_impact_report(
    analysis: dict[str, Any],
    anomaly_report: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate comprehensive impact assessment report.
    """
    
    insights = generate_impact_insights(analysis, anomaly_report)
    impact_score = calculate_impact_score(analysis, anomaly_report)
    business_assessment = assess_business_impact(analysis, anomaly_report)
    risk_tracking = track_risk_accumulation(analysis, anomaly_report)
    
    # Generate recommended actions based on risk level
    recommended_actions = []
    
    for sector in business_assessment["sectors"]:
        if sector["risk_level"] == "high":
            recommended_actions.append({
                "action": f"Activate emergency protocols for {sector['name']}",
                "priority": "critical",
                "timeframe": "immediate"
            })
        elif sector["risk_level"] == "moderate":
            recommended_actions.append({
                "action": f"Increase monitoring for {sector['name']} operations",
                "priority": "high",
                "timeframe": "1-2 hours"
            })
    
    return {
        "status": "success",
        "insights": insights,
        "impact_score": impact_score,
        "business_assessment": business_assessment,
        "risk_tracking": risk_tracking,
        "recommended_actions": recommended_actions,
        "summary": {
            "overall_severity": impact_score["overall_score"],
            "sectors_at_risk": len([s for s in business_assessment["sectors"] if s["risk_level"] != "low"]),
            "critical_factors": len([rf for rf in risk_tracking["risk_factors"] if rf["score"] > 10])
        }
    }
 