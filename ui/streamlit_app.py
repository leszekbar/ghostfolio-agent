import os
import uuid

import httpx
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


def get_server_data_source() -> str:
    try:
        response = httpx.get(f"{BACKEND_URL}/health", timeout=2.0)
        response.raise_for_status()
        return response.json().get("data_source", "mock")
    except Exception:
        return "unknown"


st.set_page_config(page_title="Ghostfolio AI Agent", page_icon=":chart_with_upwards_trend:")
st.title("Ghostfolio AI Agent")
st.caption("Portfolio Q&A with verification and disclaimer enforcement.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_connected" not in st.session_state:
    st.session_state.session_connected = False

with st.sidebar:
    st.subheader("Settings")
    data_source = get_server_data_source()
    st.caption(f"Server data source: {data_source}")
    st.code(f"Session: {st.session_state.session_id}")

    if data_source == "ghostfolio_api":
        token = st.text_input("Ghostfolio security token", type="password")
        if st.button("Connect session"):
            try:
                response = httpx.post(
                    f"{BACKEND_URL}/session/start",
                    json={
                        "session_id": st.session_state.session_id,
                        "access_token": token,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                st.session_state.session_connected = True
                st.success("Session connected.")
            except Exception as exc:
                st.session_state.session_connected = False
                st.error(f"Connection failed: {exc}")
        if not st.session_state.session_connected:
            st.warning("Connect the session before sending chat requests.")
    else:
        st.session_state.session_connected = True

    if st.button("New Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.session_connected = False
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("meta"):
            st.caption(message["meta"])

prompt = st.chat_input("Ask about your portfolio...")
if prompt:
    if not st.session_state.session_connected:
        st.error("Session is not connected. Provide token and click Connect session.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {
        "message": prompt,
        "session_id": st.session_state.session_id,
    }

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = httpx.post(f"{BACKEND_URL}/chat", json=payload, timeout=20.0)
                response.raise_for_status()
                body = response.json()
                answer = body["response"]
                meta = (
                    f"Tools: {', '.join(body.get('tool_calls', [])) or 'none'} | "
                    f"Confidence: {body.get('confidence', 0.0):.2f}"
                )
                st.markdown(answer)
                st.caption(meta)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "meta": meta}
                )
            except Exception as exc:
                error_msg = f"Request failed: {exc}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
