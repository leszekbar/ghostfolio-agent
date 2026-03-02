import os
import uuid

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


def get_server_info() -> dict[str, str]:
    try:
        response = httpx.get(f"{BACKEND_URL}/health", timeout=2.0)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"data_source": "unknown", "ghostfolio_url": "unknown", "llm_model": "unknown"}


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
    server_info = get_server_info()
    data_source = server_info.get("data_source", "unknown")
    st.caption(f"Data source: **{data_source}**")
    st.caption(f"Ghostfolio Instance: **{server_info.get('ghostfolio_url', 'unknown')}**")
    st.caption(f"LLM: **{server_info.get('llm_model', 'unknown')}**")
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

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "Welcome! I'm your Ghostfolio portfolio assistant. "
            "I can help you explore your portfolio data. Try asking:\n\n"
            '- **"What\'s my portfolio worth?"** — portfolio value and top holdings\n'
            '- **"How has my portfolio performed this year?"** — YTD returns\n'
            '- **"Show me my recent transactions"** — latest buy/sell activity\n'
            '- **"Analyze my allocation"** — sector, region, and asset class breakdown\n'
            '- **"Check my portfolio risk"** — concentration and diversification checks\n'
            '- **"What are my account balances?"** — linked accounts overview\n'
        )

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

    with st.chat_message("assistant"), st.spinner("Thinking..."):
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
            st.session_state.messages.append({"role": "assistant", "content": answer, "meta": meta})
        except Exception as exc:
            error_msg = f"Request failed: {exc}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
