
from datetime import date, datetime, timedelta

import streamlit as st
import api_client as api
from translation import tr, translate_ai_response


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
    language = st.session_state.get("app_language", "English")

    st.markdown("### " + tr("📤 Upload your electricity bill", language))
    st.caption(
        tr(
            "Upload a PDF or a clear photo of your electricity bill. "
            "We'll attempt to extract the billing period, units, and amount.",
            language,
        )
    )

    bill_file = st.file_uploader(
        tr("Choose your electricity bill", language),
        type=["pdf", "jpg", "jpeg", "png"],
        key="bill_upload",
    )

    if bill_file is None:
        st.info(
            tr("Supported formats: PDF, JPG, JPEG, and PNG.", language)
        )
        return

    st.success(
        tr("Selected file:", language) + f" {bill_file.name}"
    )

    if st.button(
        tr("Extract details from this bill", language),
        type="primary",
        use_container_width=True,
        key="extract_bill_button",
    ):
        with st.spinner(tr("Reading your bill...", language)):
            result = api.safe_call(
                api.extract_bill,
                bill_file.name,
                bill_file.getvalue(),
                error_prefix=tr("Couldn't read the bill", language),
            )

        if not isinstance(result, dict):
            return

        if not result.get("ok"):
            message = result.get("message") or (
                "Couldn't extract the bill details. "
                "Please enter the values manually below."
            )
            st.error(tr(message, language))
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
                tr(
                    "The bill was processed, but some extracted values "
                    "could not be read.",
                    language,
                )
                + f" {exc}"
            )
            return

        confidence = result.get("confidence", "low")
        notice = (
            "Bill details extracted with {confidence} confidence. "
            "Review all values below before running the comparison."
        ).format(confidence=confidence)

        st.session_state[EXTRACTION_NOTICE_KEY] = (
            "success",
            tr(notice, language),
        )

        st.rerun()


def _render_manual_bill_form(dataset_id: int):
    language = st.session_state.get("app_language", "English")

    st.markdown("### " + tr("📝 Review bill details", language))
    st.caption(
        tr(
            "Verify the extracted values, or enter the information manually.",
            language,
        )
    )

    defaults = st.session_state[FORM_DEFAULTS_KEY]

    with st.form("bill_check_form"):
        col1, col2 = st.columns(2)

        period_start = col1.date_input(
            tr("Billing period start", language),
            value=defaults["period_start"],
            key="bill_period_start",
        )

        period_end = col2.date_input(
            tr("Billing period end", language),
            value=defaults["period_end"],
            key="bill_period_end",
        )

        col3, col4 = st.columns(2)

        billed_units = col3.number_input(
            tr("Units on your bill (kWh)", language),
            min_value=0.0,
            step=1.0,
            value=float(defaults["billed_units"]),
            key="bill_units",
        )

        billed_amount = col4.number_input(
            tr("Amount charged (₹)", language),
            min_value=0.0,
            step=10.0,
            value=float(defaults["billed_amount"]),
            key="bill_amount",
        )

        submitted = st.form_submit_button(
            tr("Check my bill", language),
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if period_end < period_start:
        st.error(
            tr(
                "The billing period end date must be after the start date.",
                language,
            )
        )
        return

    if billed_units == 0.0 and billed_amount == 0.0:
        st.error(
            tr(
                "Enter your bill's units and amount, or upload a bill "
                "to extract the details first.",
                language,
            )
        )
        return

    with st.spinner(
        tr("Comparing your bill against your meter data...", language)
    ):
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
            error_prefix=tr("Couldn't check the bill", language),
        )

    if result is not None:
        st.success(
            tr("Bill comparison completed. See the result below.", language)
        )
        st.rerun()


def _render_past_checks(dataset_id: int):
    language = st.session_state.get("app_language", "English")

    st.divider()
    st.markdown("### " + tr("📋 Past bill checks", language))

    checks = api.safe_call(
        api.list_bill_checks,
        dataset_id,
        error_prefix=tr("Couldn't load past checks", language),
    ) or []

    if not checks:
        st.info(
            tr(
                "No bill checks yet. Upload a bill or enter the details above "
                "to run your first comparison.",
                language,
            )
        )
        return

    for check in checks:
        severity = check.get("severity", "")
        badge = SEVERITY_BADGE.get(severity, "⚪")
        label = SEVERITY_LABEL.get(severity, severity or "Bill check")

        with st.container(border=True):
            st.markdown(
                f'{badge} **{tr(label, language)}** · '
                f'{str(check.get("period_start", ""))[:10]} → '
                f'{str(check.get("period_end", ""))[:10]}'
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                tr("Your meter says", language),
                f'{check.get("metered_kwh", 0)} kWh '
                f'(~₹{check.get("expected_cost", 0)})',
            )

            col2.metric(
                tr("Bill says", language),
                f'{check.get("billed_units", 0)} kWh '
                f'(~₹{check.get("billed_amount", 0)})',
            )

            cost_gap = float(check.get("cost_gap", 0) or 0)
            gap_pct = float(check.get("gap_pct", 0) or 0)
            gap_sign = "+" if cost_gap >= 0 else ""

            col3.metric(
                tr("Gap", language),
                f"{gap_sign}₹{cost_gap:.2f}",
                f"{gap_sign}{gap_pct * 100:.1f}%",
            )

            explanation = (
                check.get("explanation") or "No explanation available."
            )
            st.caption(translate_ai_response(explanation, language))


def render_bill_check_tab(dataset_id: int):
    language = st.session_state.get("app_language", "English")

    st.subheader(tr("⚡ Electricity Bill Check", language))

    st.caption(
        tr(
            "Upload your electricity bill or enter the details manually. "
            "Compare the billed units and amount against your meter data "
            "to identify possible discrepancies and unexpected charges.",
            language,
        )
    )

    _initialize_session_state()
    _display_extraction_notice()

    _render_bill_upload()

    st.divider()

    _render_manual_bill_form(dataset_id)
    _render_past_checks(dataset_id)
