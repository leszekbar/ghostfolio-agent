import os
import uuid

import httpx
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Ghostfolio AI Agent", page_icon=":chart_with_upwards_trend:")
st.title("Ghostfolio AI Agent")
st.caption("Portfolio Q&A with verification and disclaimer enforcement.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Settings")
    data_source = st.selectbox("Data source", options=["mock", "ghostfolio_api"], index=0)
    st.code(f"Session: {st.session_state.session_id}")
    if st.button("New Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("meta"):
            st.caption(message["meta"])

prompt = st.chat_input("Ask about your portfolio...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {
        "message": prompt,
        "session_id": st.session_state.session_id,
        "data_source": data_source,
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
