
import streamlit as st

import api_client as api
from translation import tr


def render_sidebar() -> int | None:
    """Render translated settings and dataset picker.
    Returns the selected dataset ID, or None if no datasets exist.
    """
    st.sidebar.title(tr("⚡ EcoEnergy"))
    st.sidebar.caption(tr("AI Energy Leak Finder"))

    # ---- Settings ----
    st.sidebar.subheader(tr("Settings"))

    settings = api.safe_call(
        api.get_settings,
        error_prefix="Couldn't load settings",
    ) or {
        "tariff_per_kwh": 8.0,
        "monthly_budget": 2000.0,
        "sensitivity": "medium",
    }

    tariff = st.sidebar.number_input(
        tr("Tariff (₹ per kWh)"),
        min_value=1.0,
        max_value=50.0,
        value=float(settings["tariff_per_kwh"]),
        step=0.5,
    )

    budget = st.sidebar.number_input(
        tr("Monthly budget (₹)"),
        min_value=100.0,
        value=float(settings["monthly_budget"]),
        step=100.0,
    )

    sensitivity_options = ["low", "medium", "high"]
    sensitivity_labels = {
        "low": tr("Low"),
        "medium": tr("Medium"),
        "high": tr("High"),
    }

    current_sensitivity = settings.get("sensitivity", "medium")
    if current_sensitivity not in sensitivity_options:
        current_sensitivity = "medium"

    sensitivity = st.sidebar.select_slider(
        tr("Detection sensitivity"),
        options=sensitivity_options,
        value=current_sensitivity,
        format_func=lambda value: sensitivity_labels[value],
    )

    if st.sidebar.button(
        tr("Save settings"),
        use_container_width=True,
    ):
        result = api.safe_call(
            api.update_settings,
            tariff_per_kwh=tariff,
            monthly_budget=budget,
            sensitivity=sensitivity,
            error_prefix="Couldn't save settings",
        )

        if result is not None:
            st.sidebar.success(tr("Saved — re-analyzing datasets..."))
            st.rerun()

    st.sidebar.divider()

    # ---- Dataset picker ----
    st.sidebar.subheader(tr("Dataset"))

    datasets = api.safe_call(
        api.list_datasets,
        error_prefix="Couldn't load datasets",
    ) or []

    if not datasets:
        st.sidebar.info(
            tr(
                "No data yet. Go to the Data tab to upload a CSV "
                "or load demo data."
            )
        )
        return None

    labels = {
        dataset["id"]: (
            f'{dataset["name"]} ({tr(dataset["source"])})'
        )
        for dataset in datasets
    }
    ids = list(labels.keys())

    # Preserve the previously selected dataset.
    last_selected = st.session_state.get("selected_dataset_id")
    default_index = ids.index(last_selected) if last_selected in ids else 0

    selected_id = st.sidebar.selectbox(
        tr("Active dataset"),
        options=ids,
        index=default_index,
        format_func=lambda dataset_id: labels[dataset_id],
        key="dataset_selector",
    )

    st.session_state["selected_dataset_id"] = selected_id
    return selected_id
