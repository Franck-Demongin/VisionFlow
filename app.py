import ollama
import streamlit as st
import pydantic
from dotenv import load_dotenv

load_dotenv()

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

with st.container(key="container-input"):
    col1, col2 = st.columns([1, 15], vertical_alignment="center")
    with col1:
        st.button(":material/file_download:", type="tertiary", use_container_width=False)
    with col2:
        st.chat_input("Ask me anything...", key="chat_input")

if st.session_state["messages"]:
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
if st.session_state["chat_input"]:
    with st.chat_message("user"):
        user_input = st.session_state["chat_input"]
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.write(user_input)
    with st.chat_message("assistant"):
        st.write("Thinking...")
        st.session_state["messages"].append({"role": "assistant", "content": "Thinking..."})
