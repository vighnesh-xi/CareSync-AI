import uuid
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Post Discharge Medical AI Assistant",
    layout="centered"
)


def initialize_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "session_started" not in st.session_state:
        st.session_state.session_started = False


def start_backend_session():
    try:
        response = requests.post(
            f"{API_BASE_URL}/start-session",
            params={"session_id": st.session_state.session_id},
            timeout=20
        )
        response.raise_for_status()
        data = response.json()

        st.session_state.chat_history.append({
            "role": "assistant",
            "agent": data.get("agent", "receptionist"),
            "content": data.get("response", "")
        })
        st.session_state.session_started = True

    except requests.RequestException as exc:
        st.error(f"Could not start backend session: {exc}")


def send_message_to_backend(message: str):
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "session_id": st.session_state.session_id,
                "message": message
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        st.error(f"Error communicating with backend: {exc}")
        return None


def render_chat():
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            agent = chat.get("agent", "").title()
            if agent:
                st.markdown(f"**{agent} Agent**")
            st.write(chat["content"])

            citations = chat.get("citations", [])
            if citations:
                st.markdown("**Sources:**")
                for idx, item in enumerate(citations, start=1):
                    title = item.get("title", "Untitled Source")
                    source = item.get("source", "Unknown Source")
                    st.markdown(f"{idx}. {title} — {source}")

            if chat.get("source_type"):
                st.caption(f"Source type: {chat['source_type']}")


def render_sidebar():
    st.sidebar.title("System Info")
    st.sidebar.write("Frontend: Streamlit")
    st.sidebar.write("Backend: FastAPI")
    st.sidebar.write("Agents: Receptionist + Clinical")
    st.sidebar.write("Database: SQLite")
    st.sidebar.write("Vector Search: FAISS")
    st.sidebar.write("Embeddings: Sentence-Transformers")

    if st.sidebar.button("Start New Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.session_started = False
        st.rerun()


def main():
    initialize_session()
    render_sidebar()

    st.title("Post Discharge Medical AI Assistant")
    st.caption("Simple multi-agent POC for post-discharge nephrology support.")

    st.info("This is an AI assistant for educational purposes only.")
    st.info("Always consult healthcare professionals for medical advice.")

    if not st.session_state.session_started:
        if st.button("Start Chat"):
            start_backend_session()

    render_chat()

    user_input = st.chat_input("Type your message here...")

    if user_input:
        if not st.session_state.session_started:
            st.warning("Please start the session first.")
            return

        st.session_state.chat_history.append({
            "role": "user",
            "agent": "",
            "content": user_input
        })

        result = send_message_to_backend(user_input)

        if result:
            st.session_state.chat_history.append({
                "role": "assistant",
                "agent": result.get("agent", "assistant"),
                "content": result.get("response", ""),
                "citations": result.get("citations", []),
                "source_type": result.get("source_type")
            })

        st.rerun()


if __name__ == "__main__":
    main()