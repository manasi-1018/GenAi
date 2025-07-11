import streamlit as st
from utils import get_openai_response

st.set_page_config(page_title="GenAI Chatbot", page_icon="🤖")
st.title("🧠 Generative AI Chatbot")

# Initialize session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "input_key" not in st.session_state:
    st.session_state.input_key = 0

# Display chat history first
if st.session_state.chat_history:
    st.subheader("💬 Conversation History")
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant"):
                st.write(message['content'])
else:
    st.info("👋 Welcome! Start a conversation by typing a message below.")

# Chat interface with form to handle submission properly
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("💭 Type your message here:", placeholder="Ask me anything...", key=f"input_{st.session_state.input_key}")
    submit_button = st.form_submit_button("Send 🚀")

if submit_button and user_input and user_input.strip():
    with st.spinner("🤔 Thinking..."):
        try:
            response, updated_history = get_openai_response(user_input, st.session_state.chat_history)
            st.session_state.chat_history = updated_history
            st.session_state.input_key += 1  # Change the key to clear the input
            st.rerun()  # Refresh the page to show the new messages
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.error("Please check your OpenAI API key and internet connection.")