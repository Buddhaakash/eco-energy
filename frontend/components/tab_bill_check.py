from datetime import date, datetime, timedelta

import streamlit as st

import api_client as api

SEVERITY_BADGE = {"ok": "🟢", "minor": "🟡", "major": "🔴"}
SEVERITY_LABEL = {"ok": "Matches your usage", "minor": "Minor gap", "major": "Unwanted charge?"}

FORM_DEFAULTS_KEY = "bill_form_defaults"


def _default_form_values():
    return {
        "period_start": date.today() - timedelta(days=30),
        "period_end": date.today(),
        "billed_units": 0.0,
        "billed_amount": 0.0,
    }


def render_bill_check_tab(dataset_id: int):
    st.subheader("Check your bill against your actual usage")
    st.caption(
        "Upload your bill (or enter the details by hand) and we compare it "
        "against your own meter data to flag anything that doesn't add up — "
        "a wrong meter reading, an unexpected charge, or an incorrect tariff slab."
    )

    if FORM_DEFAULTS_KEY not in st.session_state:
        st.session_state[FORM_DEFAULTS_KEY] = _default_form_values()

    # ---------- Upload & extract ----------
    with st.expander("📤 Upload your bill (PDF or photo) to auto-fill the form", expanded=True):
        bill_file = st.file_uploader(
            "Upload bill", type=["pdf", "jpg", "jpeg", "png"], key="bill_upload"
        )
        if bill_file is not None and st.button("Extract details from this bill"):
            with st.spinner("Reading your bill..."):
                result = api.safe_call(
                    api.extract_bill, bill_file.name, bill_file.getvalue(),
                    error_prefix="Couldn't read the bill",
                )
            if result:
                if result["ok"]:
                    defaults = st.session_state[FORM_DEFAULTS_KEY]
                    if result.get("period_start"):
                        defaults["period_start"] = datetime.fromisoformat(result["period_start"]).date()
                    if result.get("period_end"):
                        defaults["period_end"] = datetime.fromisoformat(result["period_end"]).date()
                    if result.get("billed_units") is not None:
                        defaults["billed_units"] = float(result["billed_units"])
                    if result.get("billed_amount") is not None:
                        defaults["billed_amount"] = float(result["billed_amount"])

                    confidence = result.get("confidence", "low")
                    if confidence == "high":
                        st.success("Extracted successfully — please double-check the values below before submitting.")
                    else:
                        st.warning(
                            f"Extracted with {confidence} confidence — some values may be "
                            "missing or wrong. Please check them carefully below."
                        )
                else:
                    st.error(result.get("message") or "Couldn't extract details — please fill the form manually below.")

    # ---------- Manual form (pre-filled if extraction ran) ----------
    defaults = st.session_state[FORM_DEFAULTS_KEY]

    with st.form("bill_check_form"):
        st.markdown("**Review and confirm the details below:**")
        c1, c2 = st.columns(2)
        period_start = c1.date_input("Billing period start", value=defaults["period_start"])
        period_end = c2.date_input("Billing period end", value=defaults["period_end"])

        c3, c4 = st.columns(2)
        billed_units = c3.number_input(
            "Units on your bill (kWh)", min_value=0.0, step=1.0, value=defaults["billed_units"]
        )
        billed_amount = c4.number_input(
            "Amount charged (₹)", min_value=0.0, step=10.0, value=defaults["billed_amount"]
        )

        submitted = st.form_submit_button("Check my bill", use_container_width=True)

    if submitted:
        if period_end < period_start:
            st.error("The billing period end date must be after the start date.")
        elif billed_units == 0.0 and billed_amount == 0.0:
            st.error("Enter your bill's units and amount (or upload a bill above to auto-fill them).")
        else:
            with st.spinner("Comparing against your meter data..."):
                result = api.safe_call(
                    api.create_bill_check,
                    dataset_id,
                    datetime.combine(period_start, datetime.min.time()).isoformat(),
                    datetime.combine(period_end, datetime.max.time()).isoformat(),
                    billed_units, billed_amount,
                    error_prefix="Couldn't check the bill",
                )
            if result:
                st.session_state[FORM_DEFAULTS_KEY] = _default_form_values()  # reset for next time
                st.success("Done — see the result below.")
                st.rerun()

    st.divider()
    st.markdown("**Past checks**")

    checks = api.safe_call(
        api.list_bill_checks, dataset_id, error_prefix="Couldn't load past checks"
    ) or []

    if not checks:
        st.info("No bill checks yet — upload a bill or fill in the form above to run your first one.")
        return

    for c in checks:
        badge = SEVERITY_BADGE.get(c["severity"], "")
        label = SEVERITY_LABEL.get(c["severity"], c["severity"])
        with st.container(border=True):
            st.markdown(
                f'{badge} **{label}** · '
                f'{c["period_start"][:10]} → {c["period_end"][:10]}'
            )
            m1, m2, m3 = st.columns(3)
            m1.metric("Your meter says", f'{c["metered_kwh"]} kWh (~₹{c["expected_cost"]})')
            m2.metric("Bill says", f'{c["billed_units"]} kWh (~₹{c["billed_amount"]})')
            gap_sign = "+" if c["cost_gap"] >= 0 else ""
            m3.metric("Gap", f'{gap_sign}₹{c["cost_gap"]}', f'{gap_sign}{round(c["gap_pct"]*100, 1)}%')
            st.caption(c["explanation"] or "No explanation available.")
