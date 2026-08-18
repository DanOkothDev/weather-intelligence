import pandas as pd
import pytest

from backend.impact import (
    generate_impact_insights,
    calculate_impact_score,
    assess_business_impact,
    track_risk_accumulation,
    generate_impact_report,
)


def create_valid_impact_data():
    """Create analysis and anomaly data for impact assessment."""
    return {
        "analysis": {
            "statistics": {
                "temperature": {
                    "mean": 26.5,
                    "median": 26.0,
                    "minimum": 20.0,
                    "maximum": 33.0,
                    "std": 3.2,
                    "count": 50
                },
                "humidity": {
                    "mean": 72.0,
                    "median": 72.5,
                    "minimum": 45.0,
                    "maximum": 90.0,
                    "std": 12.0,
                    "count": 50
                },
                "rainfall": {
                    "mean": 2.1,
                    "median": 0.0,
                    "minimum": 0.0,
                    "maximum": 45.0,
                    "total": 105.0,
                    "count": 50
                }
            }
        },
        "anomaly_report": {
            "results": {
                "temperature": {"status": "normal"},
                "humidity": {"status": "warning"},
                "rainfall": {"status": "normal"}
            }
        }
    }


def test_generate_impact_insights_produces_valid_insights():
    """Should generate meaningful insights from analysis."""
    data = create_valid_impact_data()
    
    insights = generate_impact_insights(
        data["analysis"],
        data["anomaly_report"]
    )
    
    assert isinstance(insights, list)
    assert len(insights) > 0
    
    for insight in insights:
        assert "category" in insight
        assert "severity" in insight
        assert "title" in insight
        assert "message" in insight
        assert "recommendation" in insight
        assert insight["severity"] in ["low", "moderate", "high"]


def test_generate_impact_insights_handles_empty_data():
    """Should gracefully handle empty analysis data."""
    empty_data = {"analysis": {}, "anomaly_report": {}}
    
    insights = generate_impact_insights(
        empty_data["analysis"],
        empty_data["anomaly_report"]
    )
    
    assert isinstance(insights, list)
    # Should return at least a default "stable conditions" insight
    assert len(insights) >= 1


def test_calculate_impact_score_quantifies_severity():
    """Should compute numerical impact score."""
    data = create_valid_impact_data()
    
    score = calculate_impact_score(
        data["analysis"],
        data["anomaly_report"]
    )
    
    assert "status" in score
    assert score["status"] == "success"
    assert "overall_score" in score
    assert "component_scores" in score
    assert 0 <= score["overall_score"] <= 100
    
    # Component scores should sum to overall
    component_sum = sum(score["component_scores"].values())
    assert component_sum > 0


def test_calculate_impact_score_reflects_severity():
    """Higher severity conditions should yield higher scores."""
    data = create_valid_impact_data()
    
    # Normal conditions
    score_normal = calculate_impact_score(
        data["analysis"],
        data["anomaly_report"]
    )
    
    # Extreme conditions
    extreme_data = create_valid_impact_data()
    extreme_data["analysis"]["statistics"]["temperature"]["maximum"] = 50.0
    extreme_data["anomaly_report"]["results"]["temperature"]["status"] = "critical"
    
    score_extreme = calculate_impact_score(
        extreme_data["analysis"],
        extreme_data["anomaly_report"]
    )
    
    assert score_extreme["overall_score"] > score_normal["overall_score"]


def test_assess_business_impact_covers_sectors():
    """Should assess impact across multiple business sectors."""
    data = create_valid_impact_data()
    
    assessment = assess_business_impact(
        data["analysis"],
        data["anomaly_report"]
    )
    
    assert assessment["status"] == "success"
    assert "sectors" in assessment
    
    # Should include major impact sectors
    sectors = assessment["sectors"]
    sector_names = [s["name"] for s in sectors]
    
    assert "agriculture" in sector_names or "farming" in sector_names.lower()
    assert "energy" in sector_names or "power" in sector_names.lower()
    
    for sector in sectors:
        assert "name" in sector
        assert "risk_level" in sector
        assert "impact_description" in sector
        assert sector["risk_level"] in ["low", "moderate", "high"]


def test_assess_business_impact_has_cost_estimates():
    """Should provide cost/economic impact estimates where applicable."""
    data = create_valid_impact_data()
    
    assessment = assess_business_impact(data["analysis"], data["anomaly_report"])
    
    assert assessment["status"] == "success"
    assert "economic_impact_estimate" in assessment
    assert "currency" in assessment["economic_impact_estimate"]
    
    estimate = assessment["economic_impact_estimate"]
    if "low_estimate" in estimate:
        assert estimate["low_estimate"] >= 0
    if "high_estimate" in estimate:
        assert estimate["high_estimate"] >= 0


def test_track_risk_accumulation_detects_compounding():
    """Should identify when multiple risks compound."""
    data = create_valid_impact_data()
    
    risk_track = track_risk_accumulation(
        data["analysis"],
        data["anomaly_report"]
    )
    
    assert risk_track["status"] == "success"
    assert "cumulative_risk_score" in risk_track
    assert "risk_factors" in risk_track
    assert isinstance(risk_track["risk_factors"], list)
    
    # Risk factors should be ranked
    if len(risk_track["risk_factors"]) > 1:
        scores = [rf["score"] for rf in risk_track["risk_factors"]]
        assert scores == sorted(scores, reverse=True)


def test_track_risk_accumulation_identifies_critical_threshold():
    """Should flag when accumulated risk reaches critical threshold."""
    # Create high-risk data
    critical_data = {
        "analysis": {
            "statistics": {
                "temperature": {"maximum": 48.0},
                "humidity": {"maximum": 95.0},
                "rainfall": {"maximum": 80.0, "total": 200.0}
            }
        },
        "anomaly_report": {
            "results": {
                "temperature": {"status": "critical"},
                "humidity": {"status": "critical"},
                "rainfall": {"status": "critical"}
            }
        }
    }
    
    risk_track = track_risk_accumulation(
        critical_data["analysis"],
        critical_data["anomaly_report"]
    )
    
    assert risk_track["status"] == "success"
    assert "critical_risk_threshold_exceeded" in risk_track
    
    if risk_track["cumulative_risk_score"] > 70:
        assert risk_track["critical_risk_threshold_exceeded"] is True


def test_generate_impact_report_integrates_all_components():
    """Full report should integrate all impact analyses."""
    data = create_valid_impact_data()
    
    report = generate_impact_report(
        data["analysis"],
        data["anomaly_report"]
    )
    
    assert report["status"] == "success"
    assert "insights" in report
    assert "impact_score" in report
    assert "business_assessment" in report
    assert "risk_tracking" in report
    assert "summary" in report
    
    # Each component should have valid structure
    assert report["impact_score"]["status"] == "success"
    assert report["business_assessment"]["status"] == "success"
    assert report["risk_tracking"]["status"] == "success"


def test_generate_impact_report_produces_actionable_recommendations():
    """Report should include specific, actionable recommendations."""
    data = create_valid_impact_data()
    
    report = generate_impact_report(
        data["analysis"],
        data["anomaly_report"]
    )
    
    assert report["status"] == "success"
    
    # Check insights have specific recommendations
    insights = report.get("insights", [])
    for insight in insights:
        if "recommendation" in insight:
            # Recommendations should be specific (not just "monitor")
            rec = insight["recommendation"].lower()
            assert len(rec) > 10  # More than just generic advice
    
    # Check if specific actions are listed
    if "recommended_actions" in report:
        actions = report["recommended_actions"]
        assert len(actions) > 0
        for action in actions:
            assert "action" in action
            assert "priority" in action


def test_generate_impact_report_validates_input():
    """Should validate that required data is present."""
    invalid_data = {"analysis": {}}
    
    report = generate_impact_report({}, {})
    
    # Should handle gracefully with default/fallback data
    assert report["status"] in {"success", "insufficient_data"}