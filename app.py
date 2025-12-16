"""
Streamlit Restaurant Crawl Planner — Beautiful UI with Fixed Input
Creates personalized food crawl itineraries based on city, cuisine, and budget
"""

import streamlit as st
import uuid
import time
import traceback
from typing import List, Dict
import streamlit.components.v1 as components

# === Import agent utilities ===
try:
    from agent import create_agent, chat as agent_chat
except Exception as imp_err:
    create_agent = None
    agent_chat = None
    IMPORT_ERROR = imp_err
else:
    IMPORT_ERROR = None

# === Page config and CSS ===
st.set_page_config(
    page_title="🍽️ Restaurant Crawl Planner",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    /* Layout */
    .app-container { max-width: 1200px; margin: 10px auto; }
    .header { display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; }
    .title { font-size:28px; font-weight:700; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { color:#7b8794; font-size:14px; margin-top:5px; }

    /* Chatbox */
    #chatbox {
        border-radius: 16px;
        padding: 24px;
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.04));
        box-shadow: 0 10px 40px rgba(2,6,23,0.08);
        max-height: 65vh;
        overflow-y: auto;
        margin-bottom: 20px;
    }

    /* Message bubbles */
    .msg-user {
        margin-left:auto;
        margin-bottom:16px;
        padding:14px 18px;
        border-radius:18px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        max-width:75%;
        box-shadow: 0 8px 24px rgba(102,126,234,0.25);
        word-wrap:break-word;
        font-size: 15px;
    }
    
    .msg-assistant {
        margin-right:auto;
        margin-bottom:16px;
        padding:14px 18px;
        border-radius:18px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #2d3748;
        max-width:75%;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        word-wrap:break-word;
        font-size: 15px;
        line-height: 1.6;
    }
    
    .meta {
        font-size:11px;
        color: rgba(255,255,255,0.7);
        margin-top:8px;
        font-weight: 500;
    }
    
    .meta-assistant {
        font-size:11px;
        color: #718096;
        margin-top:8px;
        font-weight: 500;
    }

    /* Quick actions */
    .quick-actions {
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
        flex-wrap: wrap;
    }
    
    .quick-btn {
        padding: 8px 16px;
        border-radius: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        cursor: pointer;
        font-size: 13px;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .quick-btn:hover {
        transform: translateY(-2px);
    }

    /* Input area */
    .input-container {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 40px rgba(2,6,23,0.08);
        margin-top: 20px;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .status-ready {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        color: #047857;
    }
    
    .status-loading {
        background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
        color: #92400e;
    }

    /* Responsive */
    @media (max-width: 800px) {
        #chatbox { max-height: 55vh; padding:16px; }
        .msg-user, .msg-assistant { max-width:90%; }
        .title { font-size: 24px; }
    }
    
    /* Scrollbar styling */
    #chatbox::-webkit-scrollbar {
        width: 8px;
    }
    
    #chatbox::-webkit-scrollbar-track {
        background: rgba(0,0,0,0.05);
        border-radius: 10px;
    }
    
    #chatbox::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# === Cached agent initializer ===
@st.cache_resource(show_spinner=False)
def get_agent_executor_cached():
    if create_agent is None:
        raise RuntimeError(f"agent.create_agent import failed: {IMPORT_ERROR}")
    return create_agent()

def ensure_agent_ready():
    if st.session_state.get("agent_ready") and st.session_state.get("agent_executor"):
        return st.session_state["agent_executor"]
    agent_exec = get_agent_executor_cached()
    st.session_state["agent_executor"] = agent_exec
    st.session_state["agent_ready"] = True
    return agent_exec

# === Session state init ===
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_ready" not in st.session_state:
    st.session_state.agent_ready = False

if "last_error" not in st.session_state:
    st.session_state.last_error = None

# === Header ===
st.markdown('<div class="app-container">', unsafe_allow_html=True)

col1, col2 = st.columns([5, 1])
with col1:
    st.markdown(
        """
        <div class="header">
            <div>
                <div class="title">🍽️ Restaurant Crawl Planner</div>
                <div class="subtitle">AI-powered personalized food crawl itineraries • City, Cuisine & Budget based</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"<div style='text-align:right; color:#718096; font-size:11px; margin-top:10px;'>Session: {st.session_state.session_id[:8]}</div>",
        unsafe_allow_html=True
    )

st.markdown("<hr style='margin: 15px 0; border: none; border-top: 2px solid #e2e8f0;'>", unsafe_allow_html=True)

# === Status indicator ===
if st.session_state.agent_ready:
    st.markdown("<span class='status-badge status-ready'>✓ Agent Ready</span>", unsafe_allow_html=True)
else:
    st.markdown("<span class='status-badge status-loading'>⟳ Initializing...</span>", unsafe_allow_html=True)

# === Quick action examples ===
st.markdown("<div class='quick-actions'>", unsafe_allow_html=True)
col_a, col_b, col_c = st.columns(3)

with col_a:
    if st.button("🌮 Mumbai Street Food", use_container_width=True):
        st.session_state.quick_query = "Plan a half-day street food crawl in Mumbai with low budget"

with col_b:
    if st.button("🍕 Delhi Fine Dining", use_container_width=True):
        st.session_state.quick_query = "Plan a full-day fine dining experience in Delhi with high budget"

with col_c:
    if st.button("🥗 Bangalore Vegan", use_container_width=True):
        st.session_state.quick_query = "Plan a half-day vegan food tour in Bangalore with medium budget"

st.markdown("</div>", unsafe_allow_html=True)

# === Main chat container ===
chatbox_placeholder = st.empty()

# Initialize agent lazily
if not st.session_state.agent_ready:
    try:
        with st.spinner("🔄 Initializing Restaurant Crawl AI Agent..."):
            ensure_agent_ready()
            st.session_state.agent_ready = True
            st.rerun()
    except Exception:
        st.session_state.last_error = traceback.format_exc()
        st.error("❌ Agent initialization failed. Check your API keys in .env file.")
        chat_html = "<div id='chatbox'><div style='color:#e53e3e; padding:20px; text-align:center;'>Agent initialization failed. Please check your GROQ_API_KEY and TAVILY_API_KEY in .env file.</div></div>"
        chatbox_placeholder.markdown(chat_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

# Function to render chat HTML
def render_chat_html(messages):
    if not messages:
        html_parts = [
            "<div id='chatbox'>",
            "<div style='text-align:center; padding:60px 20px; color:#718096;'>",
            "<div style='font-size:48px; margin-bottom:20px;'>🍽️</div>",
            "<div style='font-size:18px; font-weight:600; margin-bottom:10px;'>Welcome to Restaurant Crawl Planner!</div>",
            "<div style='font-size:14px;'>Tell me your city, cuisine preference, and budget to get started.</div>",
            "<div style='font-size:13px; margin-top:15px; color:#a0aec0;'>Example: 'Plan a half-day street food crawl in Mumbai with low budget'</div>",
            "</div>",
            "</div>"
        ]
        return "\n".join(html_parts)
    
    html_parts = ["<div id='chatbox'>"]
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        ts = msg.get("ts", time.time())
        ts_str = time.strftime("%H:%M", time.localtime(ts))
        
        # Convert newlines to <br> and preserve formatting
        safe_content = content.replace("\n", "<br>")
        
        if role == "user":
            html_parts.append(
                f"<div style='display:flex; justify-content:flex-end;'>"
                f"<div class='msg-user'>{safe_content}"
                f"<div class='meta'>You • {ts_str}</div></div></div>"
            )
        else:
            html_parts.append(
                f"<div style='display:flex; justify-content:flex-start;'>"
                f"<div class='msg-assistant'>{safe_content}"
                f"<div class='meta-assistant'>AI Chef • {ts_str}</div></div></div>"
            )
    html_parts.append("</div>")
    return "\n".join(html_parts)

# Render current messages
chatbox_placeholder.markdown(render_chat_html(st.session_state.messages), unsafe_allow_html=True)

# === Input area ===
st.markdown("<div class='input-container'>", unsafe_allow_html=True)

# Handle quick query if set
quick_query = st.session_state.get("quick_query", "")
if quick_query:
    default_text = quick_query
    st.session_state.quick_query = ""
else:
    default_text = ""

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Your Food Crawl Request:",
        key="user_input_field",
        height=100,
        placeholder="Example: 'Plan a half-day street food crawl in Mumbai with low budget'\n\nInclude:\n• City name\n• Cuisine type (street food, vegan, fine dining, etc.)\n• Budget (low/medium/high)\n• Duration (half-day or full-day)",
        value=default_text
    )
    
    col_send, col_clear = st.columns([4, 1])
    with col_send:
        submit = st.form_submit_button("🚀 Plan My Food Crawl", use_container_width=True, type="primary")
    with col_clear:
        clear = st.form_submit_button("🗑️ Clear", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Handle clear
if clear:
    st.session_state.messages = []
    chatbox_placeholder.markdown(render_chat_html([]), unsafe_allow_html=True)
    st.rerun()

# Handle submit
if submit and user_input and user_input.strip():
    text = user_input.strip()
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": text, "ts": time.time()})
    chatbox_placeholder.markdown(render_chat_html(st.session_state.messages), unsafe_allow_html=True)
    
    # Add thinking placeholder
    st.session_state.messages.append({"role": "assistant", "content": "🤔 Planning your perfect food crawl...", "ts": time.time()})
    chatbox_placeholder.markdown(render_chat_html(st.session_state.messages), unsafe_allow_html=True)
    
    try:
        agent_exec = st.session_state.get("agent_executor") or ensure_agent_ready()
        start = time.time()
        
        # Call agent
        try:
            response = agent_chat(text, agent_exec)
            if response is None:
                response = "I didn't receive a response. Please try again with your city, cuisine preference, and budget."
            elif not isinstance(response, str):
                response = str(response)
        except Exception as e:
            response = f"I encountered an error: {str(e)}. Please try again."
        
        # Update last assistant message
        for i in range(len(st.session_state.messages) - 1, -1, -1):
            if st.session_state.messages[i]["role"] == "assistant":
                st.session_state.messages[i]["content"] = response
                st.session_state.messages[i]["ts"] = time.time()
                break
        
        chatbox_placeholder.markdown(render_chat_html(st.session_state.messages), unsafe_allow_html=True)
        elapsed = time.time() - start
        
        st.markdown(
            f"<div style='text-align:right; color:#a0aec0; font-size:12px; margin-top:10px;'>⚡ Response time: {elapsed:.2f}s</div>",
            unsafe_allow_html=True
        )
        
    except Exception:
        tb = traceback.format_exc()
        st.session_state.last_error = tb
        
        for i in range(len(st.session_state.messages) - 1, -1, -1):
            if st.session_state.messages[i]["role"] == "assistant":
                st.session_state.messages[i]["content"] = "⚠️ I encountered an error. Please check your API keys and try again."
                st.session_state.messages[i]["ts"] = time.time()
                break
        
        chatbox_placeholder.markdown(render_chat_html(st.session_state.messages), unsafe_allow_html=True)
        
        with st.expander("🔍 Error Details"):
            st.code(tb)
    
    # Auto-scroll to bottom
    components.html(
        """
        <script>
        const cb = document.getElementById('chatbox');
        if (cb) { cb.scrollTop = cb.scrollHeight; }
        </script>
        """,
        height=0,
    )

# Initial scroll
components.html(
    """
    <script>
    const cb = document.getElementById('chatbox');
    if (cb) { cb.scrollTop = cb.scrollHeight; }
    </script>
    """,
    height=0,
)

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown(
    """
    <div style='text-align:center; margin-top:30px; padding:20px; color:#a0aec0; font-size:12px;'>
        <div style='margin-bottom:8px;'>🔐 Keep API keys secure in .env file • Powered by LangChain + Groq + Tavily</div>
        <div style='font-size:11px;'>Made with ❤️ for food lovers • Discover the best culinary experiences</div>
    </div>
    """,
    unsafe_allow_html=True
)