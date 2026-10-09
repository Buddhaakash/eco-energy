import streamlit as st

import api_client as api


def render_sidebar() -> int | None:
    """Renders settings + dataset picker in the sidebar.
    Returns the currently selected dataset_id, or None if there isn't one."""
    st.sidebar.title("⚡ EcoEnergy")
    st.sidebar.caption("AI Energy Leak Finder")

    # ---- Settings ----
    st.sidebar.subheader("Settings")
    settings = api.safe_call(api.get_settings, error_prefix="Couldn't load settings") or {
        "tariff_per_kwh": 8.0, "monthly_budget": 2000.0, "sensitivity": "medium"
    }

    tariff = st.sidebar.number_input(
        "Tariff (₹ per kWh)", min_value=1.0, max_value=50.0,
        value=float(settings["tariff_per_kwh"]), step=0.5,
    )
    budget = st.sidebar.number_input(
        "Monthly budget (₹)", min_value=100.0,
        value=float(settings["monthly_budget"]), step=100.0,
    )
    sensitivity = st.sidebar.select_slider(
        "Detection sensitivity", options=["low", "medium", "high"],
        value=settings["sensitivity"],
    )

    if st.sidebar.button("Save settings", use_container_width=True):
        api.safe_call(
            api.update_settings,
            tariff_per_kwh=tariff, monthly_budget=budget, sensitivity=sensitivity,
            error_prefix="Couldn't save settings",
        )
        st.sidebar.success("Saved — re-analyzing datasets...")
        st.rerun()

    st.sidebar.divider()

    # ---- Dataset picker ----
    st.sidebar.subheader("Dataset")
    datasets = api.safe_call(api.list_datasets, error_prefix="Couldn't load datasets") or []

    if not datasets:
        st.sidebar.info("No data yet. Go to the Data tab to upload a CSV or load demo data.")
        return None

    labels = {d["id"]: f'{d["name"]} ({d["source"]})' for d in datasets}
    ids = list(labels.keys())

    # Remember the last dataset the user picked, so it stays selected across
    # reruns (tab switches, button clicks, settings saves) instead of
    # resetting to the first item in the list every time.
    last_selected = st.session_state.get("selected_dataset_id")
    default_index = ids.index(last_selected) if last_selected in ids else 0

    selected_id = st.sidebar.selectbox(
        "Active dataset", options=ids, index=default_index,
        format_func=lambda i: labels[i], key="dataset_selector",
    )
    st.session_state["selected_dataset_id"] = selected_id
    return selected_id
