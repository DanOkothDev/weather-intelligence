from pathlib import Path

import requests
import streamlit as st
import plotly.graph_objects as go



st.set_page_config(
    page_title="Weather Intelligence",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BACKEND_URL = "http://localhost:8000"
DEFAULT_DATASET = Path("data/test/weather_mock_data.csv")



st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        .main-title {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #8b949e;
            font-size: 1rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            padding: 1.2rem;
            border-radius: 14px;
            border: 1px solid rgba(128, 128, 128, 0.2);
            background: rgba(128, 128, 128, 0.05);
        }

        .metric-label {
            font-size: 0.85rem;
            color: #8b949e;
        }

        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            margin-top: 0.25rem;
        }

        .metric-description {
            font-size: 0.8rem;
            color: #8b949e;
            margin-top: 0.2rem;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 650;
            margin-top: 1rem;
            margin-bottom: 0.8rem;
        }

        .status-card {
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid rgba(128, 128, 128, 0.2);
        }

        .alert-item {
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 10px;
            background: rgba(128, 128, 128, 0.07);
        }
    </style>
    """,
    unsafe_allow_html=True,
)



if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "source_name" not in st.session_state:
    st.session_state.source_name = "Default weather dataset"



def backend_is_available():
    """Check whether the FastAPI backend is running."""

    try:
        response = requests.get(
            f"{BACKEND_URL}/health",
            timeout=3,
        )

        return response.status_code == 200

    except requests.RequestException:
        return False


def analyze_default_dataset():
    """Send the default dataset to the backend."""

    if not DEFAULT_DATASET.exists():
        raise FileNotFoundError(
            f"Default dataset not found: {DEFAULT_DATASET}"
        )

    with DEFAULT_DATASET.open("rb") as file:
        response = requests.post(
            f"{BACKEND_URL}/api/data/upload",
            files={
                "file": (
                    DEFAULT_DATASET.name,
                    file,
                    "text/csv",
                )
            },
            timeout=120,
        )

    response.raise_for_status()

    return response.json()


def analyze_uploaded_dataset(uploaded_file):
    """Send a user-uploaded CSV to the backend."""

    response = requests.post(
        f"{BACKEND_URL}/api/data/upload",
        files={
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "text/csv",
            )
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()



def get_analysis(result):
    return result.get("analysis", {})


def get_statistics(result):
    return get_analysis(result).get("statistics", {})


def get_rainfall(result):
    return get_analysis(result).get("rainfall", {})


def get_anomalies(result):
    return result.get("anomaly_report", {})


def get_predictions(result):
    return result.get("prediction_report", {})


def get_impact(result):
    return result.get("impact_report", {})


def get_latest_values(result):
    """
    The current API response doesn't return the raw cleaned
    dataframe. These values are therefore derived from the
    analysis statistics for V1.
    """

    statistics = get_statistics(result)

    return {
        "temperature": statistics.get("temperature", {}).get("mean"),
        "humidity": statistics.get("humidity", {}).get("mean"),
        "rainfall": statistics.get("rainfall", {}).get("mean"),
        "wind_speed": statistics.get("wind_speed", {}).get("mean"),
        "pressure": statistics.get("pressure", {}).get("mean"),
    }


def create_forecast_chart(predictions):
    """Create a forecast chart from prediction results."""

    temperature = predictions.get("results", {}).get(
        "temperature", {}
    )

    forecast = temperature.get("predictions", [])

    if not forecast:
        return None

    timestamps = [
        item.get("timestamp")
        for item in forecast
    ]

    values = [
        item.get("value")
        for item in forecast
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=timestamps,
            y=values,
            mode="lines+markers",
            name="Temperature",
        )
    )

    figure.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="Time",
        yaxis_title="Temperature °C",
        hovermode="x unified",
    )

    return figure



with st.sidebar:

    st.markdown("## 🌦️ Weather")
    st.markdown("### Intelligence")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Forecast",
            "Anomalies",
            "Impact",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("### Data Source")

    source = st.radio(
        "Choose source",
        [
            "Default",
            "Use my own data",
        ],
        index=0,
        label_visibility="collapsed",
    )

    uploaded_file = None

    if source == "Use my own data":

        uploaded_file = st.file_uploader(
            "Upload weather CSV",
            type=["csv"],
        )

        st.caption(
            "API data sources will be supported here in a later version."
        )

        analyze_custom = st.button(
            "Analyze Dataset →",
            use_container_width=True,
            type="primary",
        )

    else:

        analyze_custom = False

    st.divider()

    if backend_is_available():

        st.success(
            "Backend online",
        )

    else:

        st.error(
            "Backend offline",
        )




if (
    source == "Default"
    and st.session_state.analysis_result is None
):

    if backend_is_available():

        with st.spinner("Analyzing weather data..."):

            try:

                result = analyze_default_dataset()

                st.session_state.analysis_result = result
                st.session_state.source_name = (
                    "Default weather dataset"
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Unable to analyze default dataset: {exc}"
                )

    else:

        st.warning(
            "Start the FastAPI backend to load weather intelligence."
        )




if (
    source == "Use my own data"
    and analyze_custom
):

    if uploaded_file is None:

        st.warning(
            "Choose a CSV file first."
        )

    else:

        if not backend_is_available():

            st.error(
                "The backend is offline."
            )

        else:

            with st.spinner("Analyzing your dataset..."):

                try:

                    result = analyze_uploaded_dataset(
                        uploaded_file
                    )

                    st.session_state.analysis_result = result
                    st.session_state.source_name = (
                        uploaded_file.name
                    )

                    st.rerun()

                except requests.HTTPError as exc:

                    st.error(
                        f"Backend rejected the dataset: {exc}"
                    )

                except Exception as exc:

                    st.error(
                        f"Analysis failed: {exc}"
                    )


result = st.session_state.analysis_result

if result is None:

    st.markdown(
        '<div class="main-title">🌦️ Weather Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "Weather analytics, forecasting and risk intelligence"
        "</div>",
        unsafe_allow_html=True,
    )

    st.info(
        "Your weather intelligence dashboard is waiting for data."
    )

    st.stop()



st.markdown(
    '<div class="main-title">🌦️ Weather Intelligence</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="subtitle">'
    f"Source: {st.session_state.source_name}"
    f"</div>",
    unsafe_allow_html=True,
)



quality = result.get("quality_report", {})

rows = quality.get("rows", 0)

missing_percentage = quality.get(
    "missing_percentage",
    0,
)

st.caption(
    f"Analyzed {rows:,} records • "
    f"Missing data: {missing_percentage:.1f}%"
)


latest = get_latest_values(result)

col1, col2, col3, col4, col5 = st.columns(5)


def metric_card(column, label, value, description):

    with column:

        display_value = (
            "—"
            if value is None
            else f"{value:.1f}"
        )

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    {label}
                </div>

                <div class="metric-value">
                    {display_value}
                </div>

                <div class="metric-description">
                    {description}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


metric_card(
    col1,
    "Temperature",
    latest["temperature"],
    "Average °C",
)

metric_card(
    col2,
    "Humidity",
    latest["humidity"],
    "Average %",
)

metric_card(
    col3,
    "Rainfall",
    latest["rainfall"],
    "Average mm",
)

metric_card(
    col4,
    "Wind Speed",
    latest["wind_speed"],
    "Average km/h",
)

metric_card(
    col5,
    "Pressure",
    latest["pressure"],
    "Average hPa",
)


st.markdown("")



left, right = st.columns([2, 1])


with left:

    st.markdown(
        '<div class="section-title">'
        "Weather Overview"
        "</div>",
        unsafe_allow_html=True,
    )

    statistics = get_statistics(result)

    temp = statistics.get("temperature", {})
    humidity = statistics.get("humidity", {})
    rainfall = statistics.get("rainfall", {})

    overview_data = {
        "Metric": [
            "Temperature",
            "Humidity",
            "Rainfall",
        ],
        "Minimum": [
            temp.get("minimum"),
            humidity.get("minimum"),
            rainfall.get("minimum"),
        ],
        "Average": [
            temp.get("mean"),
            humidity.get("mean"),
            rainfall.get("mean"),
        ],
        "Maximum": [
            temp.get("maximum"),
            humidity.get("maximum"),
            rainfall.get("maximum"),
        ],
    }

    st.dataframe(
        overview_data,
        use_container_width=True,
        hide_index=True,
    )


with right:

    st.markdown(
        '<div class="section-title">'
        "Alerts"
        "</div>",
        unsafe_allow_html=True,
    )

    anomaly_report = get_anomalies(result)

    warnings = anomaly_report.get(
        "total_warnings",
        0,
    )

    critical = anomaly_report.get(
        "total_critical",
        0,
    )

    if critical > 0:

        st.error(
            f"🔴 {critical} critical anomaly"
            f"{'ies' if critical != 1 else 'y'} detected."
        )

    if warnings > 0:

        st.warning(
            f"🟡 {warnings} warning-level anomalies."
        )

    if critical == 0 and warnings == 0:

        st.success(
            "No significant anomalies detected."
        )



st.markdown(
    '<div class="section-title">🔮 Forecast</div>',
    unsafe_allow_html=True,
)

prediction_report = get_predictions(result)

forecast_chart = create_forecast_chart(
    prediction_report
)

if forecast_chart:

    st.plotly_chart(
        forecast_chart,
        use_container_width=True,
    )

else:

    st.info(
        "Forecast data is currently unavailable."
    )

st.markdown(
    '<div class="section-title">⚡ Impact & Risk</div>',
    unsafe_allow_html=True,
)

impact_report = get_impact(result)

impact_score = (
    impact_report
    .get("impact_score", {})
    .get("overall_score")
)

risk_tracking = impact_report.get(
    "risk_tracking",
    {},
)

risk_score = risk_tracking.get(
    "cumulative_risk_score"
)

impact_col1, impact_col2, impact_col3 = st.columns(3)


with impact_col1:

    st.metric(
        "Impact Score",
        "—"
        if impact_score is None
        else f"{impact_score}/100",
    )


with impact_col2:

    st.metric(
        "Cumulative Risk",
        "—"
        if risk_score is None
        else f"{risk_score:.1f}",
    )


with impact_col3:

    severity = (
        impact_report
        .get("summary", {})
        .get("overall_severity", "—")
    )

    st.metric(
        "Overall Severity",
        severity,
    )


st.divider()

st.caption(
    "Weather Intelligence • "
    "Analysis powered by the Weather Intelligence API"
)