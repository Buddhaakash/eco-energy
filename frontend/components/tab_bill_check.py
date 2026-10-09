
from datetime import date, datetime, timedelta

import streamlit as st
import api_client as api


SEVERITY_BADGE = {
    "ok": "🟢",
    "minor": "🟡",
    "major": "🔴",
}

SEVERITY_LABEL = {
    "ok": "Matches your usage",
    "minor": "Minor gap",
    "major": "Unwanted charge?",
}

FORM_DEFAULTS_KEY = "bill_form_defaults"
EXTRACTION_NOTICE_KEY = "bill_extraction_notice"


def _default_form_values():
    return {
        "period_start": date.today() - timedelta(days=30),
        "period_end": date.today(),
        "billed_units": 0.0,
        "billed_amount": 0.0,
    }


def _initialize_session_state():
    if FORM_DEFAULTS_KEY not in st.session_state:
        st.session_state[FORM_DEFAULTS_KEY] = _default_form_values()


def _display_extraction_notice():
    notice = st.session_state.pop(EXTRACTION_NOTICE_KEY, None)

    if notice:
        notice_type, message = notice

        if notice_type == "success":
            st.success(message)
        else:
            st.warning(message)


def _render_bill_upload():
    """Display the visible PDF/photo upload and extract bill details."""

    st.markdown("### 📤 Upload your electricity bill")
    st.caption(
        "Upload a PDF or a clear photo of your electricity bill. "
        "We'll attempt to extract the billing period, units, and amount."
    )

    bill_file = st.file_uploader(
        "Choose your electricity bill",
        type=["pdf", "jpg", "jpeg", "png"],
        key="bill_upload",
    )

    if bill_file is None:
        st.info("Supported formats: PDF, JPG, JPEG, and PNG.")
        return

    st.success(f"Selected file: {bill_file.name}")

    if st.button(
        "Extract details from this bill",
        type="primary",
        use_container_width=True,
        key="extract_bill_button",
    ):
        with st.spinner("Reading your bill..."):
            result = api.safe_call(
                api.extract_bill,
                bill_file.name,
                bill_file.getvalue(),
                error_prefix="Couldn't read the bill",
            )

        if not isinstance(result, dict):
            return

        if not result.get("ok"):
            st.error(
                result.get("message")
                or "Couldn't extract the bill details. "
                   "Please enter the values manually below."
            )
            return

        defaults = st.session_state[FORM_DEFAULTS_KEY]

        try:
            if result.get("period_start"):
                defaults["period_start"] = datetime.fromisoformat(
                    result["period_start"]
                ).date()

            if result.get("period_end"):
                defaults["period_end"] = datetime.fromisoformat(
                    result["period_end"]
                ).date()

            if result.get("billed_units") is not None:
                defaults["billed_units"] = float(result["billed_units"])

            if result.get("billed_amount") is not None:
                defaults["billed_amount"] = float(result["billed_amount"])

        except (ValueError, TypeError, OverflowError) as exc:
            st.error(
                "The bill was processed, but some extracted values "
                f"could not be read: {exc}"
            )
            return

        confidence = result.get("confidence", "low")

        st.session_state[EXTRACTION_NOTICE_KEY] = (
            "success",
            f"Bill details extracted with {confidence} confidence. "
            "Review all values below before running the comparison.",
        )

        # Rerun so the manual form displays the extracted values.
        st.rerun()


def _render_manual_bill_form(dataset_id: int):
    """Allow the user to review and submit bill details."""

    st.markdown("### 📝 Review bill details")
    st.caption(
        "Verify the extracted values, or enter the information manually."
    )

    defaults = st.session_state[FORM_DEFAULTS_KEY]

    with st.form("bill_check_form"):
        col1, col2 = st.columns(2)

        period_start = col1.date_input(
            "Billing period start",
            value=defaults["period_start"],
            key="bill_period_start",
        )

        period_end = col2.date_input(
            "Billing period end",
            value=defaults["period_end"],
            key="bill_period_end",
        )

        col3, col4 = st.columns(2)

        billed_units = col3.number_input(
            "Units on your bill (kWh)",
            min_value=0.0,
            step=1.0,
            value=float(defaults["billed_units"]),
            key="bill_units",
        )

        billed_amount = col4.number_input(
            "Amount charged (₹)",
            min_value=0.0,
            step=10.0,
            value=float(defaults["billed_amount"]),
            key="bill_amount",
        )

        submitted = st.form_submit_button(
            "Check my bill",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if period_end < period_start:
        st.error("The billing period end date must be after the start date.")
        return

    if billed_units == 0.0 and billed_amount == 0.0:
        st.error(
            "Enter your bill's units and amount, or upload a bill "
            "to extract the details first."
        )
        return

    with st.spinner("Comparing your bill against your meter data..."):
        result = api.safe_call(
            api.create_bill_check,
            dataset_id,
            datetime.combine(
                period_start, datetime.min.time()
            ).isoformat(),
            datetime.combine(
                period_end, datetime.max.time()
            ).isoformat(),
            billed_units,
            billed_amount,
            error_prefix="Couldn't check the bill",
        )

    if result is not None:
        st.success("Bill comparison completed. See the result below.")
        st.rerun()


def _render_past_checks(dataset_id: int):
    """Display previously saved bill comparisons."""

    st.divider()
    st.markdown("### 📋 Past bill checks")

    checks = api.safe_call(
        api.list_bill_checks,
        dataset_id,
        error_prefix="Couldn't load past checks",
    ) or []

    if not checks:
        st.info(
            "No bill checks yet. Upload a bill or enter the details above "
            "to run your first comparison."
        )
        return

    for check in checks:
        severity = check.get("severity", "")
        badge = SEVERITY_BADGE.get(severity, "⚪")
        label = SEVERITY_LABEL.get(severity, severity or "Bill check")

        with st.container(border=True):
            st.markdown(
                f'{badge} **{label}** · '
                f'{str(check.get("period_start", ""))[:10]} → '
                f'{str(check.get("period_end", ""))[:10]}'
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Your meter says",
                f'{check.get("metered_kwh", 0)} kWh '
                f'(~₹{check.get("expected_cost", 0)})',
            )

            col2.metric(
                "Bill says",
                f'{check.get("billed_units", 0)} kWh '
                f'(~₹{check.get("billed_amount", 0)})',
            )

            cost_gap = float(check.get("cost_gap", 0) or 0)
            gap_pct = float(check.get("gap_pct", 0) or 0)
            gap_sign = "+" if cost_gap >= 0 else ""

            col3.metric(
                "Gap",
                f"{gap_sign}₹{cost_gap:.2f}",
                f"{gap_sign}{gap_pct * 100:.1f}%",
            )

            st.caption(
                check.get("explanation")
                or "No explanation available."
            )


def render_bill_check_tab(dataset_id: int):
    st.subheader("⚡ Electricity Bill Check")

    st.caption(
        "Upload your electricity bill or enter the details manually. "
        "Compare the billed units and amount against your meter data "
        "to identify possible discrepancies and unexpected charges."
    )

    _initialize_session_state()
    _display_extraction_notice()

    # Visible upload section.
    _render_bill_upload()

    st.divider()

    # Manual form populated with extracted values when available.
    _render_manual_bill_form(dataset_id)

    # Previously saved comparisons.
    _render_past_checks(dataset_id)
