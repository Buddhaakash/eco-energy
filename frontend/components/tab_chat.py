
import streamlit as st

import api_client as api
from translation import tr, translate_ai_response

SUGGESTED_QUESTIONS = [
    "Why was my usage so high overnight?",
    "What's my single best action to save money?",
    "Am I on track to stay under budget this month?",
]


def render_chat_tab(dataset_id: int):
    language = st.session_state.get("app_language", "English")

    st.subheader(tr("Ask AI about your energy usage", language))

    history_key = f"chat_history_{dataset_id}"

    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # Suggested questions
    cols = st.columns(len(SUGGESTED_QUESTIONS))

    for i, question in enumerate(SUGGESTED_QUESTIONS):
        translated_question = tr(question, language)

        if cols[i].button(
            translated_question,
            key=f"suggest_{i}",
            use_container_width=True,
        ):
            _ask(dataset_id, history_key, question, language)

    # Display existing chat history.
    # Translate saved messages when the user changes languages.
    for role, message in st.session_state[history_key]:
        with st.chat_message(role):
            if role == "assistant":
                st.write(translate_ai_response(message, language))
            else:
                st.write(tr(message, language))

    question = st.chat_input(
        tr("Ask a question about this dataset...", language)
    )

    if question:
        _ask(dataset_id, history_key, question, language)


def _ask(
    dataset_id: int,
    history_key: str,
    question: str,
    language: str = "English",
):
    st.session_state[history_key].append(("user", question))

    # Ask the existing backend for an answer.
    # The language instruction is included in the question so the
    # backend can use it without changing the API endpoint.
    language_instruction = (
        f"\n\nPlease answer in {language}. "
        "Keep energy units, numerical values, dates, and currency amounts accurate."
    )

    with st.spinner(tr("Thinking...", language)):
        answer = api.safe_call(
            api.ask_ai,
            dataset_id,
            question + language_instruction,
            error_prefix=tr("Couldn't get an answer", language),
        )

    if answer:
        if isinstance(answer, dict):
            answer_text = (
                answer.get("answer")
                or answer.get("response")
                or str(answer)
            )
        else:
            answer_text = str(answer)

        # Translate the returned text as a fallback if the backend
        # did not follow the requested language.
        translated_answer = translate_ai_response(answer_text, language)
        st.session_state[history_key].append(
            ("assistant", translated_answer)
        )

    st.rerun()
