
import streamlit as st

import api_client as api
from translation import tr

DEMO_CSV_PATH = "data/sample_meter.csv"


def render_data_tab(selected_dataset_id: int | None):
    language = st.session_state.get("app_language", "English")

    st.subheader(tr("Manage your data", language))

    col1, col2 = st.columns(2)

    # Upload user's own CSV
    with col1:
        st.markdown("**" + tr("Upload your own meter CSV", language) + "**")
        st.caption(
            tr(
                "Needs a timestamp column and a kWh/usage column.",
                language,
            )
        )

        uploaded = st.file_uploader(
            tr("Choose a CSV file", language),
            type=["csv"],
            key="meter_csv_upload",
        )

        if uploaded is not None and st.button(
            tr("Upload & analyze", language),
            use_container_width=True,
        ):
            with st.spinner(
                tr("Uploading and running analysis...", language)
            ):
                result = api.safe_call(
                    api.upload_dataset,
                    uploaded.name,
                    uploaded.getvalue(),
                    error_prefix=tr("Upload failed", language),
                )

            if result:
                st.success(
                    tr("Uploaded", language)
                    + f' "{result["name"]}" — '
                    + tr("analysis complete.", language)
                )
                st.rerun()

    # Demo data
    with col2:
        st.markdown("**" + tr("Or just use demo data", language) + "**")
        st.caption(
            tr(
                "30 days of realistic household usage with a few leaks built in.",
                language,
            )
        )

        if st.button(
            tr("Load demo dataset", language),
            use_container_width=True,
        ):
            try:
                with open(DEMO_CSV_PATH, "rb") as file:
                    file_bytes = file.read()

                with st.spinner(
                    tr("Loading demo data and running analysis...", language)
                ):
                    result = api.safe_call(
                        api.upload_dataset,
                        "demo_meter.csv",
                        file_bytes,
                        error_prefix=tr("Couldn't load demo data", language),
                    )

                if result:
                    st.success(tr("Demo dataset loaded.", language))
                    st.rerun()

            except FileNotFoundError:
                st.error(
                    tr("Demo data file not found:", language)
                    + f" {DEMO_CSV_PATH}. "
                    + tr(
                        "Run 'python -m data.generate_demo_data' first.",
                        language,
                    )
                )

    st.divider()
    st.markdown("**" + tr("Your datasets", language) + "**")

    datasets = api.safe_call(
        api.list_datasets,
        error_prefix=tr("Couldn't load datasets", language),
    ) or []

    if not datasets:
        st.info(tr("No datasets yet.", language))
        return

    for dataset in datasets:
        c1, c2, c3 = st.columns([3, 2, 1])

        selected_marker = (
            "⭐ " if dataset["id"] == selected_dataset_id else ""
        )
        c1.write(f'{selected_marker}{dataset["name"]}')

        source = tr(str(dataset["source"]), language)
        uploaded_at = str(dataset.get("uploaded_at", ""))[:10]
        c2.write(f"{source} · {uploaded_at}")

        if c3.button(
            tr("Delete", language),
            key=f'del_{dataset["id"]}',
        ):
            result = api.safe_call(
                api.delete_dataset,
                dataset["id"],
                error_prefix=tr("Couldn't delete", language),
            )

            if result is not None:
                st.rerun()
