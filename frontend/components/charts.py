
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from translation import tr

SEVERITY_COLOR = {
    "low": "#f4c430",
    "medium": "#ff8c42",
    "high": "#e63946",
}


def render_timeline(timeline: list[dict], anomalies: list[dict]):
    language = st.session_state.get("app_language", "English")

    if not timeline:
        st.info(tr("No readings to show yet.", language))
        return

    df = pd.DataFrame(timeline)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["kwh"],
            mode="lines",
            name=tr("Usage (kWh)", language),
            line=dict(color="#2a9d8f", width=1.5),
            hovertemplate=(
                "%{x|%Y-%m-%d %H:%M}<br>"
                + tr("Usage", language)
                + ": %{y:.3f} kWh<extra></extra>"
            ),
        )
    )

    for anomaly in anomalies:
        color = SEVERITY_COLOR.get(
            anomaly.get("severity"), "#e63946"
        )

        fig.add_vrect(
            x0=anomaly["start"],
            x1=anomaly["end"],
            fillcolor=color,
            opacity=0.25,
            line_width=0,
        )

    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title=tr("Time", language),
        yaxis_title=tr("Electricity usage (kWh)", language),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        f'🟡 {tr("Low", language)} · '
        f'🟠 {tr("Medium", language)} · '
        f'🔴 {tr("High", language)} — '
        + tr(
            "shaded regions mark detected anomalies",
            language,
        )
    )
