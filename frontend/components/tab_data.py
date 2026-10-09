import streamlit as st

import api_client as api

DEMO_CSV_PATH = "data/sample_meter.csv"


def render_data_tab(selected_dataset_id: int | None):
    st.subheader("Manage your data")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Upload your own meter CSV**")
        st.caption("Needs a timestamp column and a kWh/usage column.")
        uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
        if uploaded is not None and st.button("Upload & analyze", use_container_width=True):
            with st.spinner("Uploading and running analysis..."):
                result = api.safe_call(
                    api.upload_dataset, uploaded.name, uploaded.getvalue(),
                    error_prefix="Upload failed",
                )
            if result:
                st.success(f'Uploaded "{result["name"]}" — analysis complete.')
                st.rerun()

    with col2:
        st.markdown("**Or just use demo data**")
        st.caption("30 days of realistic household usage with a few leaks built in.")
        if st.button("Load demo dataset", use_container_width=True):
            try:
                with open(DEMO_CSV_PATH, "rb") as f:
                    file_bytes = f.read()
                with st.spinner("Loading demo data and running analysis..."):
                    result = api.safe_call(
                        api.upload_dataset, "demo_meter.csv", file_bytes,
                        error_prefix="Couldn't load demo data",
                    )
                if result:
                    st.success("Demo dataset loaded.")
                    st.rerun()
            except FileNotFoundError:
                st.error(
                    f"{DEMO_CSV_PATH} not found. Run "
                    "'python -m data.generate_demo_data' first."
                )

    st.divider()
    st.markdown("**Your datasets**")
    datasets = api.safe_call(api.list_datasets) or []
    if not datasets:
        st.info("No datasets yet.")
        return

    for d in datasets:
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f'{"⭐ " if d["id"] == selected_dataset_id else ""}{d["name"]}')
        c2.write(f'{d["source"]} · {d["uploaded_at"][:10]}')
        if c3.button("Delete", key=f'del_{d["id"]}'):
            api.safe_call(api.delete_dataset, d["id"], error_prefix="Couldn't delete")
            st.rerun()
