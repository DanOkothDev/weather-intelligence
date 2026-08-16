from backend.impact import generate_impact_insights


analysis = {
    "statistics": {
        "temperature": {
            "mean": 32.5,
            "maximum": 37.2,
        },
        "humidity": {
            "maximum": 89,
        },
        "rainfall": {
            "total": 72.4,
            "maximum": 54.8,
        },
    }
}


anomaly_report = {
    "results": {
        "temperature": {
            "status": "anomaly",
            "anomaly_count": 1,
            "anomalies": [
                {
                    "index": 42,
                    "value": 37.2,
                    "z_score": 3.2,
                    "severity": "anomaly",
                }
            ],
        }
    }
}


insights = generate_impact_insights(
    analysis,
    anomaly_report,
)


print("\nIMPACT INSIGHTS")

for insight in insights:
    print("\n", insight)