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
        df = pd.read_csv(csv_path, header=None)
        
        # KIM row (index 8) - columns 0, 3, 6, 9 (URL, type, empty, URL, type, empty, URL, type, empty, URL)
        if len(df) > 8:
            row = df.iloc[8]
            docs["Axis Large Cap Fund"]["KIM"] = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            docs["Axis Small Cap Fund"]["KIM"] = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
            docs["Axis Nifty 500 Index Fund"]["KIM"] = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ""
            docs["Axis ELSS Tax Saver"]["KIM"] = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else ""
        
        # SID row (index 9) - columns 0, 3, 6, 9
        if len(df) > 9:
            row = df.iloc[9]
            docs["Axis Large Cap Fund"]["SID"] = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            docs["Axis Small Cap Fund"]["SID"] = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
            docs["Axis Nifty 500 Index Fund"]["SID"] = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ""
            docs["Axis ELSS Tax Saver"]["SID"] = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else ""
        
        # Leaflet row (index 10) - columns 0, 3, 6, 9
        if len(df) >= 11:
            row = df.iloc[10]
            docs["Axis Large Cap Fund"]["Leaflet"] = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            docs["Axis Small Cap Fund"]["Leaflet"] = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
            docs["Axis Nifty 500 Index Fund"]["Leaflet"] = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ""
            docs["Axis ELSS Tax Saver"]["Leaflet"] = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else ""
        
    except Exception as e:
        st.error(f"Error loading documents: {e}")
    
    return docs


def load_css():
    """Load CSS - Dark Theme"""
    st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {display: none !important;}
    
    /* Dark background for entire app */
    .main, .stApp {background: #1a1a2e !important;}
    .block-container {padding: 1rem !important; max-width: 800px !important; background: #1a1a2e !important;}
    
    /* App Header - Light text on dark */
    .app-header {text-align: center; padding: 0.5rem 0;}
    .app-header h1 {color: #ffffff; font-size: 1.75rem; font-weight: 600; margin: 0 0 0.25rem 0;}
    .app-header p {color: #b8b8d1; font-size: 0.9rem; margin: 0;}
    
    /* Disclaimer - Dark orange warning */
    .disclaimer {background: #2d2d44; border-left: 4px solid #ff9800; padding: 0.75rem 1rem; 
                 border-radius: 0 8px 8px 0; margin: 1rem 0; font-size: 0.85rem; color: #ffb74d;}
    .disclaimer strong {color: #ff9800;}
    
    /* Available Funds Section - Dark card */
    .funds-box {background: #252542; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid #3a3a5c;}
    .funds-box h4 {margin: 0 0 0.75rem 0; color: #ffffff; font-size: 1rem; display: flex; align-items: center; gap: 0.5rem;}
    .funds-box p {color: #b8b8d1; font-size: 0.9rem; margin: 0 0 0.75rem 0;}
    .fund-tags {display: flex; flex-wrap: wrap; gap: 0.5rem;}
    .fund-tag {background: #667eea; color: #ffffff; padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.85rem; border: none;}
    
    /* Suggestions */
    .suggestions {display: flex; gap: 0.75rem; margin: 1rem 0; flex-wrap: wrap;}
    .suggestions-title {color: #b8b8d1; font-size: 0.9rem; margin-bottom: 0.5rem; text-align: center;}
    
    /* Chat Messages - Dark theme */
    .msg {display: flex; margin: 0.75rem 0; align-items: flex-start;}
    .msg-avatar {width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; 
                 justify-content: center; font-size: 0.85rem; margin-right: 0.5rem; flex-shrink: 0;}
    .msg-avatar.user {background: #6a6a8a; color: #ffffff;}
    .msg-avatar.bot {background: #00c853; color: white;}
    .msg-content {background: #252542; color: #ffffff; padding: 0.75rem 1rem; border-radius: 12px; font-size: 0.9rem; 
                  line-height: 1.5; max-width: 85%; border: 1px solid #3a3a5c;}
    .msg-content.user {background: #667eea; border-color: #5a6fd6; color: #ffffff;}
    .msg-source {margin-top: 0.5rem; font-size: 0.8rem;}
    .msg-source a {color: #64b5f6; text-decoration: none;}
    .msg-source a:hover {text-decoration: underline; color: #90caf9;}
    .msg-time {margin-top: 0.25rem; font-size: 0.75rem; color: #8888a8;}
    
    /* Chat box - Dark */
    .chat-box {background: #252542; border-radius: 12px; padding: 1rem; margin: 1rem 0; 
               border: 1px solid #3a3a5c; min-height: 200px; max-height: 400px; overflow-y: auto;}
    
    /* Buttons - Dark theme */
    .stButton>button {border-radius: 8px !important; font-size: 0.85rem !important; background: #667eea !important; color: white !important; border: none !important;}
    .stButton>button:hover {background: #5a6fd6 !important;}
    
    /* Fund Documents Section - Dark */
    .fund-docs {background: #252542; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid #3a3a5c;}
    .fund-docs h4 {margin: 0 0 0.5rem 0; color: #ffffff; font-size: 1rem; display: flex; align-items: center; gap: 0.5rem;}
    .fund-docs .subtitle {color: #b8b8d1; font-size: 0.85rem; margin: 0 0 1rem 0;}
    .fund-docs .fund-name {font-size: 0.9rem; font-weight: 500; color: #ffffff; margin: 1rem 0 0.5rem 0;}
    .fund-docs .fund-name:first-of-type {margin-top: 0;}
    
    /* Document buttons - Purple/blue gradient style */
    .doc-btn {padding: 0.6rem 1rem; background: #667eea; color: #ffffff !important; border: none; border-radius: 8px; 
              font-size: 0.85rem; cursor: pointer; text-align: center; text-decoration: none; display: inline-block;
              font-weight: 500;}
    .doc-btn:hover {background: #5a6fd6; color: #ffffff !important;}
    .doc-btn:visited {color: #ffffff !important;}
    .doc-btn.disabled {background: #3a3a5c; color: #666688 !important; cursor: not-allowed;}
    
    /* Input styling - Dark */
    .stTextInput > div > div > input {
        border: 2px solid #667eea !important;
        border-radius: 25px !important;
        padding: 0.75rem 1.25rem !important;
        font-size: 0.95rem !important;
        background: #252542 !important;
        color: #ffffff !important;
    }
    .stTextInput > div > div > input::placeholder {color: #8888a8 !important;}
    
    /* Expander - White background for Fund Documents */
    .streamlit-expanderHeader {font-size: 0.9rem !important; font-weight: 600 !important; color: #333333 !important; background: #ffffff !important; border-radius: 8px !important; border: 1px solid #e0e0e0 !important;}
    .streamlit-expanderContent {background: #ffffff !important; border: 1px solid #e0e0e0 !important; border-top: none !important; border-radius: 0 0 8px 8px !important;}
    .streamlit-expanderHeader:hover {background: #f5f5f5 !important;}
    
    /* Divider - Dark */
    hr {border-color: #3a3a5c !important;}
    
    /* Scrollbar - Dark */
    ::-webkit-scrollbar {width: 8px;}
    ::-webkit-scrollbar-track {background: #1a1a2e;}
    ::-webkit-scrollbar-thumb {background: #4a4a6a; border-radius: 4px;}
    ::-webkit-scrollbar-thumb:hover {background: #5a5a7a;}
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
    """Detect all funds mentioned in query with flexible matching"""
    query_lower = query.lower()
    detected = []
    
    # Direct full name match
    for fund in ALL_FUNDS:
        if fund.lower() in query_lower:
            detected.append(fund)
    
    # If no full match, check for partial/fund type matches
    if not detected:
        # Large Cap Fund detection
        if any(term in query_lower for term in ['large cap', 'largecap']):
            detected.append("Axis Large Cap Fund")
        # Small Cap Fund detection
        elif any(term in query_lower for term in ['small cap', 'smallcap']):
            detected.append("Axis Small Cap Fund")
        # Nifty 500 detection
        elif any(term in query_lower for term in ['nifty 500', 'nifty500', 'index fund']):
            detected.append("Axis Nifty 500 Index Fund")
        # ELSS detection
        elif any(term in query_lower for term in ['elss', 'tax saver', 'tax saver fund']):
            detected.append("Axis ELSS Tax Saver")
    
    if any(phrase in query_lower for phrase in ['all funds', 'all axis funds', 'each fund', 'every fund']):
        return ALL_FUNDS
    
    return detected if detected else [None]


def detect_data_types(query: str) -> list:
    """Detect all data types user is asking about (for multi-data queries)"""
    query_lower = query.lower()
    data_types = []
    
    if any(word in query_lower for word in ['nav', 'net asset value']):
        data_types.append('NAV')
    if any(word in query_lower for word in ['sip', 'minimum investment', 'min sip']):
        data_types.append('MIN SIP')
    if any(word in query_lower for word in ['expense', 'expense ratio', 'ter']):
        data_types.append('expense_ratio')
    if any(word in query_lower for word in ['exit load', 'exit', 'redemption']):
        data_types.append('exit_load')
    if any(word in query_lower for word in ['risk', 'riskometer']):
        data_types.append('riskometer')
    if any(word in query_lower for word in ['benchmark']):
        data_types.append('benchmark')
    
    return data_types if data_types else ['general']


def detect_doc_types(query: str) -> list:
    """Detect all document types user is asking about (for multi-doc queries)"""
    query_lower = query.lower()
    doc_types = []
    
    if 'kim' in query_lower:
        doc_types.append('KIM')
    if 'sid' in query_lower:
        doc_types.append('SID')
    if 'leaflet' in query_lower:
        doc_types.append('Leaflet')
    
    return doc_types


def is_document_query(query: str) -> bool:
    """Check if query is asking for documents"""
    query_lower = query.lower()
    return any(doc in query_lower for doc in ['kim', 'sid', 'leaflet', 'document', 'pdf'])


def get_document_response(fund: str, doc_type: str, docs: dict) -> dict:
    """Get document link response"""
    url = docs.get(fund, {}).get(doc_type, "")
    if url and url.startswith("http"):
        return {
            'answer': f"You can access the {doc_type} here.",
            'source_url': url,
            'source_name': 'AxisMF.com',
            'hide_last_updated': True
        }
    return {
        'answer': f"Sorry, {doc_type} document is not available for {fund}.",
        'source_url': None,
        'source_name': None,
        'hide_last_updated': True
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


def is_out_of_scope(query: str) -> bool:
    """Check if query is out of scope (investment advice, general questions, etc.)"""
    query_lower = query.lower()
    
    # Out of scope keywords
    out_of_scope = [
        'suggestion', 'suggest', 'advice', 'advise', 'recommend', 'should i', 
        'investment advice', 'good investment', 'bad investment', 'buy', 'sell',
        'general', 'what is mutual fund', 'how to invest', 'investment strategy',
        'portfolio', 'diversify', 'allocation', 'tips', 'tricks', 'best fund',
        'worst fund', 'top performing', 'bottom performing'
    ]
    
    return any(keyword in query_lower for keyword in out_of_scope)


def process_query(query: str, backend, csv_manager, docs, fund_data) -> list:
    """Process query and return list of responses (for multi-fund support)"""
    responses = []
    query_lower = query.lower()
    
    # Check if query is out of scope
    if is_out_of_scope(query):
        return [{
            'answer': "I am a factual mutual fund assistant and can only help with data provided in my knowledge base. For investment advice or general questions, please consult a financial advisor.",
            'source_url': None,
            'source_name': None,
            'fund': None,
            'hide_last_updated': True
        }]
    
    # Check if it's a general greeting or non-fund query
    general_queries = ['hi', 'hello', 'hey', 'how are you', 'what can you do', 'help']
    if any(q in query_lower for q in general_queries):
        return [{
            'answer': "Hello! I'm FundWise AI, your mutual fund assistant. I can help you with information about Axis Mutual Funds including NAV, expense ratio, minimum SIP, and official documents (KIM, SID, Leaflet). What would you like to know?",
            'source_url': None,
            'source_name': None,
            'fund': None,
            'hide_last_updated': True
        }]
    
    # Detect funds
    funds = detect_funds_in_query(query)
    
    # Check for multi-document query (e.g., "KIM, SID, Leaflet for ELSS")
    doc_types = detect_doc_types(query)
    
    # Handle multi-document query for single/multiple funds
    if doc_types and funds[0]:
        for fund in funds:
            if not fund:
                continue
            
            # Build multi-document response
            doc_links = []
            for doc_type in doc_types:
                url = docs.get(fund, {}).get(doc_type, "")
                if url and url.startswith("http"):
                    doc_links.append(f"{doc_type}: {url}")
            
            if doc_types:
                if len(doc_types) == 1:
                    # Single document type
                    url = docs.get(fund, {}).get(doc_types[0], "")
                    if url and url.startswith("http"):
                        responses.append({
                            'answer': f"You can access the {doc_types[0]} here.",
                            'source_url': url,
                            'source_name': 'AxisMF.com',
                            'fund': fund,
                            'hide_last_updated': True
                        })
                else:
                    # Multiple documents - just show fund name, links will be displayed below
                    answer_text = f"{fund}:"
                    
                    # Store all document URLs for the response
                    doc_urls = {}
                    for doc_type in doc_types:
                        url = docs.get(fund, {}).get(doc_type, "")
                        if url and url.startswith("http"):
                            doc_urls[doc_type] = url
                    
                    responses.append({
                        'answer': answer_text,
                        'source_url': None,
                        'source_name': None,
                        'fund': fund,
                        'hide_last_updated': True,
                        'doc_urls': doc_urls  # Store multiple URLs for display below
                    })
        return responses
    
    # Single document query
    if is_document_query(query) and funds[0]:
        doc_type = 'KIM'
        if 'sid' in query_lower: doc_type = 'SID'
        elif 'leaflet' in query_lower: doc_type = 'Leaflet'
        
        for fund in funds:
            if fund:
                resp = get_document_response(fund, doc_type, docs)
                resp['fund'] = fund
                responses.append(resp)
        return responses
    
    # If no fund detected and query is about data (not documents), ask for clarification
    if not funds[0]:
        data_keywords = ['nav', 'sip', 'expense', 'exit load', 'risk', 'minimum', 'benchmark']
        if any(kw in query_lower for kw in data_keywords):
            return [{
                'answer': "Which mutual fund are you referring to? Please specify the fund name from: Axis Large Cap Fund, Axis Small Cap Fund, Axis Nifty 500 Index Fund, or Axis ELSS Tax Saver.",
                'source_url': None,
                'source_name': None,
                'fund': None
            }]
        # Document query without fund
        if is_document_query(query):
            return [{
                'answer': "Which fund's document would you like? Please specify the fund name.",
                'source_url': None,
                'source_name': None,
                'fund': None
            }]
    
    # Regular data query - handle multiple data types
    data_types = detect_data_types(query)
    
    for fund in funds:
        if not fund:
            continue
        
        # Handle multiple data types for same fund
        if len(data_types) > 1:
            answer_lines = [f"{fund}:", ""]
            for data_type in data_types:
                url = csv_manager.get_source_for_answer(fund, data_type)
                explicit_value = get_explicit_value(fund, data_type, fund_data)
                
                if data_type == 'NAV':
                    nav_date = fund_data.get(fund, {}).get('NAV_Date', '')
                    answer_lines.append(f"NAV: Rs.{explicit_value} (as of {nav_date})")
                elif data_type == 'MIN SIP':
                    answer_lines.append(f"Minimum SIP: Rs.{explicit_value}")
                elif data_type == 'expense_ratio':
                    answer_lines.append(f"Expense Ratio: {explicit_value}")
                elif data_type == 'exit_load':
                    answer_lines.append(f"Exit Load: {explicit_value}")
            
            # Add source link for first data type
            url = csv_manager.get_source_for_answer(fund, data_types[0])
            source_name = "Groww.in" if url and "groww.in" in url else "AxisMF.com"
            
            last_updated = fund_data.get(fund, {}).get('last_updated', '')
            if last_updated:
                try:
                    date_part = last_updated.split()[0:3]
                    last_updated_str = ' '.join(date_part)
                except:
                    last_updated_str = last_updated
            else:
                last_updated_str = ""
            
            responses.append({
                'answer': "\n".join(answer_lines),
                'source_url': url,
                'source_name': source_name,
                'fund': fund,
                'last_updated': last_updated_str
            })
        else:
            # Single data type
            data_type = data_types[0]
            url = csv_manager.get_source_for_answer(fund, data_type)
            source_name = ""
            if url:
                source_name = "Groww.in" if "groww.in" in url else "AxisMF.com"
            
            explicit_value = get_explicit_value(fund, data_type, fund_data)
            
            full_query = f"{query} for {fund}" if fund not in query else query
            resp = backend.process_query(full_query)
            
            if url:
                resp['source_url'] = url
                resp['source_name'] = source_name
            
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


def handle_suggestion_click(suggestion: str):
    """Handle suggestion button click - process immediately"""
    backend = st.session_state.backend
    csv_manager = st.session_state.csv_manager
    docs = st.session_state.docs
    fund_data = st.session_state.fund_data
    
    # Add user message
    st.session_state.chat_history.append({'role': 'user', 'content': suggestion})
    
    # Process query immediately
    responses = process_query(suggestion, backend, csv_manager, docs, fund_data)
    
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
    st.markdown('<div class="disclaimer">⚠️ <strong>Disclaimer:</strong> This chatbot provides factual information only, not investment advice. Please consult a SEBI-registered financial advisor before investing.</div>', unsafe_allow_html=True)
    
    # Available Funds
    tags_html = "".join([f'<span class="fund-tag">{f}</span>' for f in ALL_FUNDS])
    st.markdown(f'<div class="funds-box"><h4 style="color: #00d4ff;">📋 Available Funds</h4><p style="color:#a0e7ff;font-size:0.85rem;margin:0 0 0.5rem 0;">Get instant answers about NAV, Expense Ratio, Minimum SIP, Risk Level, and Benchmark.</p><div class="fund-tags">{tags_html}</div></div>', unsafe_allow_html=True)
    
    # Fund Documents - Dropdown style
    with st.expander("📄 Fund Documents"):
        for fund, links in docs.items():
            st.markdown(f'<p style="color: #333333; font-weight: 700; font-size: 1.1rem; margin: 1.5rem 0 0.75rem 0;">{fund}</p>', unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (doc_type, icon) in enumerate([("KIM", "📄"), ("SID", "📋"), ("Leaflet", "📑")]):
                with cols[i]:
                    url = links.get(doc_type, "")
                    if url and url.startswith("http"):
                        st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%;padding:0.5rem;background:#667eea;color:white;border:none;border-radius:8px;cursor:pointer;font-size:0.85rem;">{icon} {doc_type}</button></a>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<button style="width:100%;padding:0.5rem;background:#e0e0e0;color:#999;border:none;border-radius:8px;font-size:0.85rem;" disabled>{icon} {doc_type}</button>', unsafe_allow_html=True)
            st.divider()
    
    # Suggestions with heading
    st.markdown('<p class="suggestions-title">💡 Ask AI About Your Funds</p>', unsafe_allow_html=True)
    st.markdown('<div class="suggestions">', unsafe_allow_html=True)
    cols = st.columns(3)
    suggestions = [
        "What is the NAV of Axis Large Cap Fund?",
        "What is the expense ratio of Axis ELSS Tax Saver Fund?",
        "What is the minimum SIP for Axis Small Cap Fund?"
    ]
    for i, s in enumerate(suggestions):
        with cols[i]:
            if st.button(s, key=f"s_{i}", use_container_width=True):
                st.session_state.pending = s
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat Section
    st.markdown('<h4 style="margin: 1.5rem 0 1rem 0; color: #00d4ff;">💬 Chat with FundWise AI</h4>', unsafe_allow_html=True)
    
    # Messages
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f'<div class="msg"><div class="msg-avatar user">👤</div><div class="msg-content user">{msg["content"]}</div></div>', unsafe_allow_html=True)
        else:
            fund_label = f"<strong>{msg.get('fund', '')}</strong><br>" if msg.get('fund') else ""
            
            # Handle multiple document URLs
            src = ""
            if msg.get('doc_urls'):
                # Multiple document links
                for doc_type, url in msg['doc_urls'].items():
                    src += f'<div class="msg-source"><a href="{url}" target="_blank">🔗 View {doc_type} on AxisMF.com ↗</a></div>'
            elif msg.get('source_url'):
                src = f'<div class="msg-source"><a href="{msg["source_url"]}" target="_blank">🔗 View Source on {msg.get("source_name", "Source")} ↗</a></div>'
            
            # Hide last_updated for out-of-scope responses or when flag is set
            hide_last_updated = msg.get('hide_last_updated', False)
            last_updated = f'<div class="msg-time">Last updated: {msg.get("last_updated", "")}</div>' if (msg.get('last_updated') and not hide_last_updated) else ""
            st.markdown(f'<div class="msg"><div class="msg-avatar bot">🤖</div><div class="msg-content">{fund_label}<strong>Answer:</strong> {msg["content"]}{src}{last_updated}</div></div>', unsafe_allow_html=True)
    
    # Input with dynamic key for clearing
    c1, c2 = st.columns([6, 1])
    with c1:
        inp = st.text_input("Msg", key=f"inp_{st.session_state.input_key}", placeholder="Type your question...", label_visibility="collapsed")
    with c2:
        send = st.button("➤", key="snd", type="primary")
    
    # Handle pending from suggestions
    if 'pending' in st.session_state:
        inp = st.session_state.pending
        del st.session_state.pending
        send = True
    
    if send and inp:
        # Add user message
        st.session_state.chat_history.append({'role': 'user', 'content': inp})
        
        # Process query (supports multi-fund)
        responses = process_query(inp, backend, csv_manager, docs, fund_data)
        
        # Add bot responses
        for resp in responses:
            msg = {
                'role': 'assistant',
                'content': resp['answer'],
                'source_url': resp.get('source_url'),
                'source_name': resp.get('source_name'),
                'fund': resp.get('fund'),
                'last_updated': resp.get('last_updated', datetime.now().strftime("%Y-%m-%d")),
                'hide_last_updated': resp.get('hide_last_updated', False)
            }
            # Add doc_urls if present (for multi-document queries)
            if 'doc_urls' in resp:
                msg['doc_urls'] = resp['doc_urls']
            st.session_state.chat_history.append(msg)
        
        # Clear input by incrementing key
        st.session_state.input_key += 1
        st.rerun()


if __name__ == "__main__":
    main()
