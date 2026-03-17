"""
Phase 6: Streamlit Frontend
Chatbot UI with title, funds display, sample questions, and chat interface
"""

import streamlit as st
import os
import sys

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase5'))
from backend.api import ChatbotBackend


# Page configuration
st.set_page_config(
    page_title="Groww Mutual Fund Assistant",
    page_icon="📈",
    layout="centered"
)


def init_session():
    """Initialize session state"""
    if 'backend' not in st.session_state:
        st.session_state.backend = ChatbotBackend()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []


def display_header():
    """Display title and description"""
    st.title("📈 Groww Mutual Fund Information Assistant")
    st.markdown("""
    Get factual information about **Axis Mutual Funds**.
    
    ⚠️ **Note:** I can only provide information, not investment advice.
    """)
    st.divider()


def display_funds(backend: ChatbotBackend):
    """Display available funds as buttons"""
    st.subheader("Available Funds")
    
    funds = backend.get_available_funds()
    cols = st.columns(len(funds))
    
    for col, fund in zip(cols, funds):
        with col:
            if st.button(fund, key=f"fund_{fund}", use_container_width=True):
                st.session_state.selected_fund = fund
                st.session_state.user_input = f"Tell me about {fund}"


def display_sample_questions(backend: ChatbotBackend):
    """Display sample questions"""
    st.subheader("Try asking:")
    
    questions = backend.get_sample_questions()
    
    for q in questions:
        if st.button(q, key=f"q_{q}", use_container_width=True):
            st.session_state.user_input = q


def display_chat_interface(backend: ChatbotBackend):
    """Display chat interface"""
    st.subheader("Chat")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
            if message.get('source_url'):
                st.markdown(f"**Source:** [{message['source_url']}]({message['source_url']})")
            if message.get('last_updated'):
                st.caption(f"Last Updated: {message['last_updated']}")
    
    # User input
    user_input = st.chat_input(
        "Ask about NAV, expense ratio, or fund details...",
        key="chat_input"
    )
    
    # Handle input from session state (from buttons)
    if 'user_input' in st.session_state:
        user_input = st.session_state.user_input
        del st.session_state.user_input
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Get response from backend
        with st.spinner('Thinking...'):
            response = backend.process_query(user_input)
            response = backend.validate_response(response)
        
        # Add assistant message to history
        assistant_message = {
            'role': 'assistant',
            'content': response['answer'],
            'source_url': response.get('source_url'),
            'last_updated': response.get('last_updated')
        }
        st.session_state.chat_history.append(assistant_message)
        
        # Rerun to display updated chat
        st.rerun()


def main():
    """Main Streamlit app"""
    init_session()
    
    display_header()
    
    # Create two columns
    col1, col2 = st.columns([1, 2])
    
    with col1:
        display_funds(st.session_state.backend)
        st.divider()
        display_sample_questions(st.session_state.backend)
    
    with col2:
        display_chat_interface(st.session_state.backend)


if __name__ == "__main__":
    main()
