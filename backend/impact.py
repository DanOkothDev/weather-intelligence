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

        if result.get("status") == "anomaly":

            insights.append({
                "category": "anomaly",
                "severity": "high",
                "title": f"Unusual {variable} conditions",
                "message": (
                    f"An unusual {variable} observation was detected "
                    "relative to the dataset baseline."
                ),
                "recommendation": (
                    f"Investigate the {variable} measurement and "
                    "monitor subsequent observations."
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
                    "Continue monitoring future observations."
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