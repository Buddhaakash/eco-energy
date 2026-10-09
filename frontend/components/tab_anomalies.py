
import streamlit as st

import api_client as api
from translation import tr, translate_ai_response


SEVERITY_BADGE = {
    "low": "🟡",
    "medium": "🟠",
    "high": "🔴",
}

STATUS_LABEL = {
    "new": "New",
    "expected": "Expected",
    "fixed": "Fixed",
    "ignored": "Ignored",
}

STATUS_OPTIONS = ["new", "expected", "fixed", "ignored"]


def render_anomalies_tab(dataset_id: int):
    language = st.session_state.get("app_language", "English")

    st.subheader(tr("Detected issues", language))

    severity_options = ["low", "medium", "high"]

    severity_filter = st.multiselect(
        tr("Filter by severity", language),
        options=severity_options,
        default=severity_options,
        format_func=lambda severity: tr(severity.title(), language),
    )

    anomalies = api.safe_call(
        api.list_anomalies,
        dataset_id,
        error_prefix=tr("Couldn't load anomalies", language),
    ) or []

    anomalies = [
        anomaly
        for anomaly in anomalies
        if anomaly.get("severity") in severity_filter
    ]

    if not anomalies:
        st.info(
            tr(
                "No anomalies match this filter (or none detected — nice!).",
                language,
            )
        )
        return

    for anomaly in anomalies:
        severity = anomaly.get("severity", "")
        badge = SEVERITY_BADGE.get(severity, "")

        with st.container(border=True):
            c1, c2 = st.columns([4, 1])

            with c1:
                kind = anomaly.get("kind", "Issue")
                kind_label = kind.replace("_", " ").title()

                start = str(anomaly.get("start", ""))[:16].replace("T", " ")
                end = str(anomaly.get("end", ""))[11:16]

                extra_kwh = anomaly.get("extra_kwh", 0)
                estimated_cost = anomaly.get("est_cost", 0)

                st.markdown(
                    f"{badge} **{tr(kind_label, language)}** · "
                    f"{start} → {end} · "
                    f"+{extra_kwh} kWh (~₹{estimated_cost})"
                )

                explanation = (
                    anomaly.get("explanation")
                    or "No explanation available."
                )

                st.caption(
                    translate_ai_response(explanation, language)
                )

                current_status = anomaly.get("status", "new")
                status_label = STATUS_LABEL.get(
                    current_status, current_status
                )

                st.caption(
                    tr("Status:", language)
                    + f" **{tr(status_label, language)}**"
                )

            with c2:
                current_status = anomaly.get("status", "new")

                if current_status not in STATUS_OPTIONS:
                    current_status = "new"

                new_status = st.selectbox(
                    tr("Mark as", language),
                    options=STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(current_status),
                    format_func=lambda status: tr(
                        STATUS_LABEL[status], language
                    ),
                    key=f'status_{anomaly["id"]}',
                    label_visibility="collapsed",
                )

                if new_status != current_status:
                    result = api.safe_call(
                        api.update_anomaly_status,
                        anomaly["id"],
                        new_status,
                        error_prefix=tr(
                            "Couldn't update status", language
                        ),
                    )

                    if result is not None:
                        st.rerun()
