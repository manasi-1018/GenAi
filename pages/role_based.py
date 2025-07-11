import streamlit as st
import sys
import os
from dotenv import load_dotenv

#Load Environemtn Variable
load_dotenv()

#add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_openai_response

#Role-Based System Prompts 
ROLE_PROMPTS = {
    "Default": "You are a helpful assistant",
    "Teacher" : "You are an experienced and patient school teacher who explain concepts clearly with examples and encourage learning. Use simple language and break down complex topics into easy-to-understand parts",
    "Doctor": "You are a professional medical doctor who provides advice based on symptoms. Always remind users to consult with a real healthcare provider for serious concerns. Be informative but responsible.",
    "Lawyer": "You are a legal expert who explains laws and rights in simple terms. Provide general legal information but always advise users to consult with a qualified attorney for specific legal matters.",
    "Fitness Coach": "You are a motivating fitness coach who gives health and exercise guidance. Be encouraging, provide practical tips, and always emphasize safety and gradual progress.",
    "Career Advisor": "You are a career advisor helping people choose jobs and build resumes. Provide practical advice about career development, job searching, and professional growth."
}


def get_role_response(prompt, chat_history, role):
    """Get Response with role-specific system prompt"""
    messages = [{"role": "system", "content": ROLE_PROMPTS[role]}]
    #Add Chat History
    if chat_history:
        messages.extend(chat_history)

    messages.append({"role": "user", "content": prompt})

    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4",
        messages= messages
    )

    reply = response.choices[0].message.content

    #Update Chat History
    update_history = chat_history if chat_history else []
    update_history.append({"role":"user", "content": prompt})
    update_history.append({"role":"assistant", "content": reply})

    return reply, update_history

#Streamlit
st.set_page_config(page_title="Role_based AI Assistant", page_icon="-", layout="wide")

#Custom CSS For Better Styling

st.markdown("""
<style>
    .role-card {
            padding: 1rem;
            border-radius: 10px;
            border: 2px solid #e0e0e0;
            margin: 0.5rem 0;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
    .selected-role {
        border-color: #4CAF50;
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    }
    .stSelectbox > div > div {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

st.title("Role-Based AI Assistant")
st.markdown("---")

#Initialise the session state
if "role_chat_history" not in st.session_state:
    st.session_state.role_chat_history = []
if "selected_role" not in st.session_state:
    st.session_state.selected_role = "Default"
if "role_input_key" not in st.session_state:
    st.session_state.role_input_key = 0


#sidebar For Role Selection

with st.sidebar:
    st.header("Choose Your AI Assistant Role")

    #Role Selection
    selected_role = st.selectbox(
        "Select a role:", 
        list(ROLE_PROMPTS.keys()),
        index=list(ROLE_PROMPTS.keys()).index(st.session_state.selected_role),
        key="role_selector"
    )

    #if role Changed 
    if selected_role != st.session_state.selected_role:
        st.session_state.role_chat_history = []
        st.session_state.selected_role = selected_role
        st.session_state.role_input_key += 1
        st.rerun()
    
    #Display Current role info
    st.markdown(f"""
            <div class="role-card selected-role">
                <h4> Current Role: {selected_role}</h4>
                <p><em> {ROLE_PROMPTS[selected_role]}</em></p>
            </div>
            """, unsafe_allow_html=True)
    #Role Description

    st.markdown("Available Roles")
    for role, description in ROLE_PROMPTS.items():
        emoji = {
            "Default":"✌️",
            "Teacher":"👩🏻‍🏫",
            "Doctor": "👩🏻‍⚕️",
            "Lawyer":"🧑🏻‍💼",
            "Fitness Coach": "🏋🏻",
            "Career Advisor": "🧑🏻‍💼",
        }.get(role, "--")

        st.markdown(f"**{emoji} {role}**")
        st.caption(description[:80] + "..." if len(description)>80 else description)
        st.markdown("---")

    #Clear Conversation Button
    if st.button("Clear Conversation", type="secondary"):
        st.session_state.role_chat_history = []
        st.session_state.role_input_key += 1
        st.rerun()

#Main Chat Interface
col1, col2 = st.columns([3, 1])

with col1:
    #Display Current role prominently
    role_emoji = {
        "Default" : "✌️",
        "Teacher" : "👩🏻‍🏫",
        "Doctor" : "👩🏻‍⚕️",
        "Lawyer": "🧑🏻‍💼",
        "Fitness Coach": "🏋🏻",
        "Career Advisor": "🧑🏻‍💼"
    }.get(selected_role, "++")

    st.markdown(f"### {role_emoji} Chatting with: **{selected_role}**")

    #Display Chat History

    if st.session_state.role_chat_history:
        st.markdown("## Conversation")

        for i, message in enumerate(st.session_state.role_chat_history):
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message['content'])
            else:
                with st.chat_message("assistant"):
                    st.write(message['content'])
    else:
        st.info(f"Hello! I am your {selected_role} assistant. How can I help you today?")

    #Chat Input Form 
    with st.form(key="role_chat_form", clear_on_submit=True):
        user_input = st.text_area(
            f"Ask Your {selected_role}:", 
            placeholder=f"Type your question for the {selected_role}...",
            key=f"role_input_{st.session_state.role_input_key}",
            height=100
        )
        submit_button = st.form_submit_button("Send")

    if submit_button and user_input and user_input.strip():
        with st.spinner(f"....{selected_role} is thinking..."):
            try:
                response, updated_history = get_role_response(
                    user_input,
                    st.session_state.role_chat_history,
                    selected_role
                )
                st.session_state.role_chat_history = updated_history
                st.session_state.role_input_key += 1
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.error("Please check your OpenAI API key and internet connection.")

with col2:
    st.markdown("Session Stats")

    total_messages = len(st.session_state.role_chat_history)
    user_message = sum(1 for m in st.session_state.role_chat_history if m["role"] == "user")

    st.metric("Total Messages", total_messages)
    st.metric("Your Messages", user_message)

    

          


        