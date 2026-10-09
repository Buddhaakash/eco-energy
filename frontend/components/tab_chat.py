import streamlit as st

import api_client as api

SUGGESTED_QUESTIONS = [
    "Why was my usage so high overnight?",
    "What's my single best action to save money?",
    "Am I on track to stay under budget this month?",
]


def render_chat_tab(dataset_id: int):
    st.subheader("Ask AI about your energy usage")

    history_key = f"chat_history_{dataset_id}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    cols = st.columns(len(SUGGESTED_QUESTIONS))
    for i, q in enumerate(SUGGESTED_QUESTIONS):
        if cols[i].button(q, key=f"suggest_{i}", use_container_width=True):
            _ask(dataset_id, history_key, q)

    for role, text in st.session_state[history_key]:
        with st.chat_message(role):
            st.write(text)

    question = st.chat_input("Ask a question about this dataset...")
    if question:
        _ask(dataset_id, history_key, question)


def _ask(dataset_id: int, history_key: str, question: str):
    st.session_state[history_key].append(("user", question))
    with st.spinner("Thinking..."):
        answer = api.safe_call(
            api.ask_ai, dataset_id, question, error_prefix="Couldn't get an answer"
        )
    if answer:
        st.session_state[history_key].append(("assistant", answer))
    st.rerun()
