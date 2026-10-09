import streamlit as st

import api_client as api

SEVERITY_BADGE = {"low": "🟡", "medium": "🟠", "high": "🔴"}
STATUS_LABEL = {"new": "New", "expected": "Expected", "fixed": "Fixed", "ignored": "Ignored"}


def render_anomalies_tab(dataset_id: int):
    st.subheader("Detected issues")

    severity_filter = st.multiselect(
        "Filter by severity", options=["low", "medium", "high"],
        default=["low", "medium", "high"],
    )

    anomalies = api.safe_call(
        api.list_anomalies, dataset_id, error_prefix="Couldn't load anomalies"
    ) or []
    anomalies = [a for a in anomalies if a["severity"] in severity_filter]

    if not anomalies:
        st.info("No anomalies match this filter (or none detected — nice!).")
        return

    for a in anomalies:
        badge = SEVERITY_BADGE.get(a["severity"], "")
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(
                    f'{badge} **{a["kind"].replace("_", " ").title()}** · '
                    f'{a["start"][:16].replace("T", " ")} → {a["end"][11:16]}  '
                    f'&nbsp;·&nbsp; +{a["extra_kwh"]} kWh (~₹{a["est_cost"]})'
                )
                st.caption(a["explanation"] or "No explanation available.")
                st.caption(f'Status: **{STATUS_LABEL.get(a["status"], a["status"])}**')
            with c2:
                new_status = st.selectbox(
                    "Mark as", options=["new", "expected", "fixed", "ignored"],
                    index=["new", "expected", "fixed", "ignored"].index(a["status"]),
                    key=f'status_{a["id"]}', label_visibility="collapsed",
                )
                if new_status != a["status"]:
                    api.safe_call(
                        api.update_anomaly_status, a["id"], new_status,
                        error_prefix="Couldn't update status",
                    )
                    st.rerun()
