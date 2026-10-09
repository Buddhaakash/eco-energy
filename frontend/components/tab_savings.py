import streamlit as st

import api_client as api

PRIORITY_LABEL = {1: "🔴 High", 2: "🟠 Medium", 3: "🟢 Low"}


def render_savings_tab(dataset_id: int):
    st.subheader("Savings plan")

    recs = api.safe_call(
        api.list_recommendations, dataset_id, error_prefix="Couldn't load recommendations"
    ) or []

    if not recs:
        st.info("No recommendations yet — upload or load data on the Data tab.")
        return

    total_potential = sum(r["est_cost_saved"] for r in recs)
    done_savings = sum(r["est_cost_saved"] for r in recs if r["status"] == "done")
    if total_potential > 0:
        st.progress(
            min(done_savings / total_potential, 1.0),
            text=f"₹{done_savings:.0f} of ₹{total_potential:.0f} potential savings actioned",
        )

    for r in recs:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f'{PRIORITY_LABEL.get(r["priority"], "")} **{r["title"]}**')
                st.caption(r["detail"])
                if r["est_cost_saved"] > 0:
                    st.caption(f'Estimated savings: {r["est_kwh_saved"]} kWh (~₹{r["est_cost_saved"]}/period)')
            with c2:
                new_status = st.selectbox(
                    "Status", options=["open", "done", "snoozed"],
                    index=["open", "done", "snoozed"].index(r["status"]),
                    key=f'rec_status_{r["id"]}', label_visibility="collapsed",
                )
                if new_status != r["status"]:
                    api.safe_call(
                        api.update_recommendation_status, r["id"], new_status,
                        error_prefix="Couldn't update status",
                    )
                    st.rerun()
