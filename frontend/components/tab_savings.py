
import streamlit as st

import api_client as api
from translation import tr, translate_ai_response


PRIORITY_LABEL = {
    1: "🔴 High",
    2: "🟠 Medium",
    3: "🟢 Low",
}

STATUS_OPTIONS = ["open", "done", "snoozed"]

STATUS_LABELS = {
    "open": "Open",
    "done": "Done",
    "snoozed": "Snoozed",
}


def render_savings_tab(dataset_id: int):
    language = st.session_state.get("app_language", "English")

    st.subheader(tr("Savings plan", language))

    recs = api.safe_call(
        api.list_recommendations,
        dataset_id,
        error_prefix=tr("Couldn't load recommendations", language),
    ) or []

    if not recs:
        st.info(
            tr(
                "No recommendations yet — upload or load data on the Data tab.",
                language,
            )
        )
        return

    total_potential = sum(
        float(r.get("est_cost_saved", 0) or 0) for r in recs
    )

    done_savings = sum(
        float(r.get("est_cost_saved", 0) or 0)
        for r in recs
        if r.get("status") == "done"
    )

    if total_potential > 0:
        st.progress(
            min(done_savings / total_potential, 1.0),
            text=tr(
                f"₹{done_savings:.0f} of ₹{total_potential:.0f} "
                "potential savings actioned",
                language,
            ),
        )

    for recommendation in recs:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])

            with c1:
                priority = PRIORITY_LABEL.get(
                    recommendation.get("priority"), ""
                )

                title = recommendation.get("title", "")
                detail = recommendation.get("detail", "")

                st.markdown(
                    f"{tr(priority, language)} "
                    f"**{translate_ai_response(title, language)}**"
                )

                st.caption(translate_ai_response(detail, language))

                cost_saved = float(
                    recommendation.get("est_cost_saved", 0) or 0
                )
                kwh_saved = recommendation.get("est_kwh_saved", 0)

                if cost_saved > 0:
                    st.caption(
                        tr("Estimated savings:", language)
                        + f" {kwh_saved} kWh "
                        + f"(~₹{cost_saved}/"
                        + tr("period", language)
                        + ")"
                    )

            with c2:
                current_status = recommendation.get("status", "open")

                if current_status not in STATUS_OPTIONS:
                    current_status = "open"

                new_status = st.selectbox(
                    tr("Status", language),
                    options=STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(current_status),
                    format_func=lambda status: tr(
                        STATUS_LABELS[status], language
                    ),
                    key=f'rec_status_{recommendation["id"]}',
                    label_visibility="collapsed",
                )

                if new_status != current_status:
                    result = api.safe_call(
                        api.update_recommendation_status,
                        recommendation["id"],
                        new_status,
                        error_prefix=tr("Couldn't update status", language),
                    )

                    if result is not None:
                        st.rerun()
