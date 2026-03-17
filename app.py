# -*- coding: utf-8 -*-
"""
FundWise AI - RAG Chatbot for Groww Mutual Funds
Streamlit Deployment Entry Point

This is the main entry point for Streamlit Cloud deployment.
All phases are integrated here for a complete chatbot experience.
"""

import streamlit as st
import os
import sys
import json
import re
from datetime import datetime

# Add all phase paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'phase4'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'phase4', 'backend'))

from backend.api import ChatbotBackend
from config.csv_loader import CSVSourceManager

# Page configuration
st.set_page_config(
    page_title="FundWise AI",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# All available funds
ALL_FUNDS = [
    "Axis Large Cap Fund",
    "Axis Small Cap Fund", 
    "Axis Nifty 500 Index Fund",
    "Axis ELSS Tax Saver"
]

# Load structured fund data from JSON
def load_fund_data():
    """Load NAV, SIP, expense ratio, exit load from fund values JSON"""
    json_path = os.path.join(os.path.dirname(__file__), 'shared', 'data', 'fund_values.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


# Load document links from CSV
def load_document_links():
    """Load KIM, SID, Leaflet links from the CSV file"""
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'mutual_funds_sheet1.csv')
    
    docs = {fund: {} for fund in ALL_FUNDS}
    
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        
        # KIM row (index 8)
        if len(df) > 8:
            row = df.iloc[8]
            docs["Axis Large Cap Fund"]["KIM"] = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            docs["Axis Small Cap Fund"]["KIM"] = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
            docs["Axis Nifty 500 Index Fund"]["KIM"] = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ""
            docs["Axis ELSS Tax Saver"]["KIM"] = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else ""
        
        # SID and Leaflet in row 9 (index 9)
        if len(df) > 9:
            row = df.iloc[9]
            for fund, col_idx in [("Axis Large Cap Fund", 0), ("Axis Small Cap Fund", 3), 
                                   ("Axis Nifty 500 Index Fund", 6), ("Axis ELSS Tax Saver", 9)]:
                val = str(row.iloc[col_idx]).strip() if pd.notna(row.iloc[col_idx]) else ""
                if val:
                    if 'sid' in val.lower():
                        docs[fund]["SID"] = val
                    elif 'leaflet' in val.lower() or 'factsheets' in val.lower():
                        docs[fund]["Leaflet"] = val
        
    except Exception as e:
        st.error(f"Error loading documents: {e}")
    
    return docs


def load_css():
    """Load CSS"""
    st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {display: none !important;}
    .main, .stApp {background: #f0f2f5 !important;}
    .block-container {padding: 1rem !important; max-width: 800px !important;}
    
    .app-header {text-align: center; padding: 0.5rem 0;}
    .app-header h1 {color: #1a1a1a; font-size: 1.75rem; font-weight: 600; margin: 0 0 0.25rem 0;}
    .app-header p {color: #666; font-size: 0.9rem; margin: 0;}
    
    .disclaimer {background: #fff3e0; border-left: 4px solid #ff9800; padding: 0.75rem 1rem; 
                 border-radius: 0 8px 8px 0; margin: 1rem 0; font-size: 0.8rem; color: #e65100;}
    
    .funds-box {background: white; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; border: 1px solid #e0e0e0;}
    .funds-box h4 {margin: 0 0 0.5rem 0; color: #333; font-size: 0.95rem;}
    .fund-tags {display: flex; flex-wrap: wrap; gap: 0.5rem;}
    .fund-tag {background: #e3f2fd; color: #1976d2; padding: 0.3rem 0.75rem; border-radius: 20px; font-size: 0.8rem;}
    
    .suggestions {display: flex; gap: 0.75rem; margin: 1rem 0; flex-wrap: wrap;}
    
    .suggestions-title {color: #666; font-size: 0.9rem; margin-bottom: 0.5rem; text-align: center;}
    
    .msg {display: flex; margin: 0.75rem 0; align-items: flex-start;}
    .msg-avatar {width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; 
                 justify-content: center; font-size: 0.85rem; margin-right: 0.5rem; flex-shrink: 0;}
    .msg-avatar.user {background: #e0e0e0;}
    .msg-avatar.bot {background: #00c853; color: white;}
    .msg-content {background: white; padding: 0.75rem 1rem; border-radius: 12px; font-size: 0.9rem; 
                  line-height: 1.5; max-width: 85%; border: 1px solid #e0e0e0;}
    .msg-content.user {background: #e3f2fd; border-color: #bbdefb;}
    .msg-source {margin-top: 0.5rem; font-size: 0.8rem;}
    .msg-source a {color: #1976d2; text-decoration: none;}
    .msg-source a:hover {text-decoration: underline;}
    .msg-time {margin-top: 0.25rem; font-size: 0.75rem; color: #999;}
    
    .chat-box {background: white; border-radius: 12px; padding: 1rem; margin: 1rem 0; 
               border: 1px solid #e0e0e0; min-height: 200px; max-height: 400px; overflow-y: auto;}
    
    .stButton>button {border-radius: 8px !important; font-size: 0.85rem !important;}
    
    .fund-docs {background: white; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; border: 1px solid #e0e0e0;}
    .fund-docs h4 {margin: 0 0 0.75rem 0; color: #333; font-size: 0.95rem;}
    .doc-grid {display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem;}
    .doc-btn {padding: 0.5rem; background: #1976d2; color: white; border: none; border-radius: 8px; 
              font-size: 0.8rem; cursor: pointer; text-align: center; text-decoration: none; display: block;}
    .doc-btn:hover {background: #1565c0;}
    .doc-btn.disabled {background: #e0e0e0; color: #999; cursor: not-allowed;}
    </style>
    """, unsafe_allow_html=True)


def init_session():
    """Initialize session"""
    if 'backend' not in st.session_state:
        st.session_state.backend = ChatbotBackend()
    if 'csv_manager' not in st.session_state:
        st.session_state.csv_manager = CSVSourceManager()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'docs' not in st.session_state:
        st.session_state.docs = load_document_links()
    if 'fund_data' not in st.session_state:
        st.session_state.fund_data = load_fund_data()
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0


def detect_funds_in_query(query: str) -> list:
    """Detect all funds mentioned in query"""
    query_lower = query.lower()
    detected = []
    
    for fund in ALL_FUNDS:
        if fund.lower() in query_lower:
            detected.append(fund)
    
    if any(phrase in query_lower for phrase in ['all funds', 'all axis funds', 'each fund', 'every fund']):
        return ALL_FUNDS
    
    return detected if detected else [None]


def detect_data_type(query: str) -> str:
    """Detect what data type user is asking about"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['nav', 'net asset value']):
        return 'NAV'
    elif any(word in query_lower for word in ['sip', 'minimum investment', 'min sip']):
        return 'MIN SIP'
    elif any(word in query_lower for word in ['expense', 'expense ratio', 'ter']):
        return 'expense_ratio'
    elif any(word in query_lower for word in ['exit load', 'exit', 'redemption']):
        return 'exit_load'
    elif any(word in query_lower for word in ['risk', 'riskometer']):
        return 'riskometer'
    elif any(word in query_lower for word in ['benchmark']):
        return 'benchmark'
    
    return 'general'


def is_document_query(query: str) -> bool:
    """Check if query is asking for documents"""
    query_lower = query.lower()
    return any(doc in query_lower for doc in ['kim', 'sid', 'leaflet', 'document', 'pdf'])


def get_document_response(fund: str, doc_type: str, docs: dict) -> dict:
    """Get document link response"""
    url = docs.get(fund, {}).get(doc_type, "")
    if url and url.startswith("http"):
        return {
            'answer': f"Here is the {doc_type} for {fund}.",
            'source_url': url,
            'source_name': 'AxisMF.com'
        }
    return {
        'answer': f"Sorry, {doc_type} document is not available for {fund}.",
        'source_url': None,
        'source_name': None
    }


def get_explicit_value(fund: str, data_type: str, fund_data: dict) -> str:
    """Get explicit numerical value from structured data"""
    fund_info = fund_data.get(fund, {})
    
    if data_type == 'NAV':
        return fund_info.get('NAV')
    elif data_type == 'MIN SIP':
        return fund_info.get('MIN_SIP')
    elif data_type == 'expense_ratio':
        return fund_info.get('expense_ratio')
    elif data_type == 'exit_load':
        return fund_info.get('exit_load')
    return None


def process_query(query: str, backend, csv_manager, docs, fund_data) -> list:
    """Process query and return list of responses (for multi-fund support)"""
    responses = []
    query_lower = query.lower()
    
    # Check if fund name is missing
    funds = detect_funds_in_query(query)
    
    # If no fund detected and query is about data (not documents), ask for clarification
    if not funds[0] and not is_document_query(query):
        data_keywords = ['nav', 'sip', 'expense', 'exit load', 'risk', 'minimum', 'benchmark']
        if any(kw in query_lower for kw in data_keywords):
            return [{
                'answer': "Which mutual fund are you referring to? Please specify the fund name from: Axis Large Cap Fund, Axis Small Cap Fund, Axis Nifty 500 Index Fund, or Axis ELSS Tax Saver.",
                'source_url': None,
                'source_name': None,
                'fund': None
            }]
    
    # Check if document query
    if is_document_query(query):
        doc_type = 'KIM'
        if 'sid' in query_lower: doc_type = 'SID'
        elif 'leaflet' in query_lower: doc_type = 'Leaflet'
        
        # If no fund specified for document query, ask clarification
        if not funds[0]:
            return [{
                'answer': f"Which fund's {doc_type} document would you like? Please specify the fund name.",
                'source_url': None,
                'source_name': None,
                'fund': None
            }]
        
        for fund in funds:
            if fund:
                resp = get_document_response(fund, doc_type, docs)
                resp['fund'] = fund
                responses.append(resp)
        return responses
    
    # Regular data query
    data_type = detect_data_type(query)
    
    for fund in funds:
        if not fund:
            continue
            
        # Get from CSV first (highest priority)
        url = csv_manager.get_source_for_answer(fund, data_type)
        source_name = ""
        if url:
            source_name = "Groww.in" if "groww.in" in url else "AxisMF.com"
        
        # Get explicit value from structured data first
        explicit_value = get_explicit_value(fund, data_type, fund_data)
        
        # Get answer from backend
        full_query = f"{query} for {fund}" if fund not in query else query
        resp = backend.process_query(full_query)
        
        # Override with CSV source if available
        if url:
            resp['source_url'] = url
            resp['source_name'] = source_name
        
        # Use explicit value if available, otherwise use backend response
        if explicit_value:
            data_type_display = data_type.replace('_', ' ').title()
            if data_type == 'NAV':
                nav_date = fund_data.get(fund, {}).get('NAV_Date', '')
                resp['answer'] = f"NAV is Rs.{explicit_value} (as of {nav_date})"
            elif data_type == 'MIN SIP':
                resp['answer'] = f"The minimum SIP amount is Rs.{explicit_value}."
            elif data_type == 'expense_ratio':
                resp['answer'] = f"The expense ratio is {explicit_value}."
            elif data_type == 'exit_load':
                resp['answer'] = f"The exit load details: {explicit_value}."
            else:
                resp['answer'] = f"The {data_type_display} is {explicit_value}."
        
        # Add last_updated from fund data
        last_updated = fund_data.get(fund, {}).get('last_updated', '')
        if last_updated:
            try:
                date_part = last_updated.split()[0:3]
                resp['last_updated'] = ' '.join(date_part)
            except:
                resp['last_updated'] = last_updated
        
        resp['fund'] = fund
        responses.append(resp)
    
    return responses


def main():
    """Main app"""
    load_css()
    init_session()
    
    backend = st.session_state.backend
    csv_manager = st.session_state.csv_manager
    docs = st.session_state.docs
    fund_data = st.session_state.fund_data
    
    # Header
    st.markdown('<div class="app-header"><h1>📊 Welcome to FundWise AI</h1><p>Your Mutual Fund Assistant for Axis Funds</p></div>', unsafe_allow_html=True)
    
    # Disclaimer
    st.markdown('<div class="disclaimer"><strong>⚠️ Disclaimer:</strong> This chatbot provides information only. Not SEBI registered. No investment advice.</div>', unsafe_allow_html=True)
    
    # Funds box
    st.markdown('<div class="funds-box"><h4>Supported Funds:</h4><div class="fund-tags">' + 
                ''.join([f'<span class="fund-tag">{f}</span>' for f in ALL_FUNDS]) + 
                '</div></div>', unsafe_allow_html=True)
    
    # Fund Documents section
    st.markdown('<div class="fund-docs"><h4>📄 Fund Documents</h4><p style="font-size:0.8rem;color:#666;margin-bottom:0.75rem;">Click to view official documents:</p>', unsafe_allow_html=True)
    
    for fund in ALL_FUNDS:
        st.markdown(f"<p style='font-size:0.85rem;margin:0.5rem 0 0.25rem 0;font-weight:500;'>{fund}</p>", unsafe_allow_html=True)
        doc_cols = st.columns(3)
        fund_docs = docs.get(fund, {})
        
        for idx, (doc_type, icon) in enumerate([('KIM', '📋'), ('SID', '📄'), ('Leaflet', '📑')]):
            with doc_cols[idx]:
                url = fund_docs.get(doc_type, "")
                if url and url.startswith("http"):
                    st.markdown(f'<a href="{url}" target="_blank" class="doc-btn">{icon} {doc_type}</a>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<button class="doc-btn disabled" disabled>{icon} {doc_type}</button>', unsafe_allow_html=True)
    
    st.divider()
    
    # Suggestions with heading
    st.markdown('<p class="suggestions-title">💡 Ask AI About Your Funds</p>', unsafe_allow_html=True)
    st.markdown('<div class="suggestions">', unsafe_allow_html=True)
    cols = st.columns(3)
    suggestions = [
        "What is the NAV of Axis Large Cap Fund?",
        "Show me the expense ratio of all funds",
        "What is the minimum SIP for Axis ELSS?"
    ]
    
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                st.session_state.current_input = suggestion
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Messages
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f'<div class="msg"><div class="msg-avatar user">👤</div><div class="msg-content user">{msg["content"]}</div></div>', unsafe_allow_html=True)
        else:
            fund_label = f"<strong>{msg.get('fund', '')}</strong><br>" if msg.get('fund') else ""
            src = f'<div class="msg-source"><a href="{msg["source_url"]}" target="_blank">🔗 View Source on {msg.get("source_name", "Source")} ↗</a></div>' if msg.get('source_url') else ""
            last_updated = f'<div class="msg-time">Last updated: {msg.get("last_updated", "")}</div>' if msg.get('last_updated') else ""
            st.markdown(f'<div class="msg"><div class="msg-avatar bot">🤖</div><div class="msg-content">{fund_label}<strong>Answer:</strong> {msg["content"]}{src}{last_updated}</div></div>', unsafe_allow_html=True)
    
    # Input with dynamic key for clearing
    c1, c2 = st.columns([6, 1])
    with c1:
        current_input = st.session_state.get('current_input', '')
        inp = st.text_input("Msg", key=f"inp_{st.session_state.input_key}", 
                           value=current_input, 
                           placeholder="Type your question...", 
                           label_visibility="collapsed")
        if current_input:
            st.session_state.current_input = ''
    with c2:
        send = st.button("➤", key="snd", type="primary")
    
    if send and inp:
        # Add user message
        st.session_state.chat_history.append({'role': 'user', 'content': inp})
        
        # Process query (supports multi-fund)
        with st.spinner(''):
            responses = process_query(inp, backend, csv_manager, docs, fund_data)
        
        # Add bot responses
        for resp in responses:
            st.session_state.chat_history.append({
                'role': 'bot',
                'content': resp['answer'],
                'source_url': resp.get('source_url'),
                'source_name': resp.get('source_name'),
                'fund': resp.get('fund'),
                'last_updated': resp.get('last_updated')
            })
        
        # Clear input by incrementing key
        st.session_state.input_key += 1
        st.rerun()


if __name__ == "__main__":
    main()
