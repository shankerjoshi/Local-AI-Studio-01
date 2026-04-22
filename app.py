# app.py
import streamlit as st
from openai import OpenAI
import utils
import json
import os
import uuid
import time

# --- Configuration & File Paths ---
LOCAL_API_URL = "http://localhost:1234/v1" 
LOCAL_API_KEY = "lm-studio" 
HISTORY_FILE = "data/chat_history.json" 

client = OpenAI(base_url=LOCAL_API_URL, api_key=LOCAL_API_KEY)

# --- Multi-Session History Management ---
def load_all_history():
    """Loads all chat sessions from the JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_all_history(history_dict):
    """Saves all chat sessions to the JSON file."""
    os.makedirs("data", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_dict, f, indent=4)

def get_chat_title(messages):
    """Generates a short title based on the first user message."""
    for msg in messages:
        if msg["role"] == "user":
            # Return first 30 chars of the first user message
            return msg["content"][:30] + "..."
    return "New Chat"

# --- Model Detection Logic ---
@st.cache_data(ttl=5)
def get_loaded_model():
    try:
        models = client.models.list()
        if models and models.data:
            return models.data[0].id 
        return "nvidia/nemotron-3-nano-4b" 
    except Exception:
        return "nvidia/nemotron-3-nano-4b" 

current_model_id = get_loaded_model()

# --- UI Setup ---
st.set_page_config(page_title="AI Coder Studio", layout="wide")
st.title("💻 Local AI Coder Studio")

# --- Session State Initialization ---
if "history" not in st.session_state:
    st.session_state.history = load_all_history()

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.history[st.session_state.current_session_id] = {
        "title": "New Chat",
        "messages": [{"role": "system", "content": "You are a professional Python and C++ coder, AI expert, and great teacher."}]
    }

current_session = st.session_state.current_session_id
messages = st.session_state.history[current_session]["messages"]

# --- Sidebar Controls & Chat History ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.success(f"🟢 **Model:**\n`{current_model_id}`")
    
    # Show/Hide Thoughts Toggle
    show_thoughts = st.toggle("🧠 Show AI Thoughts", value=False, help="Display the model's internal reasoning process while it generates.")
    
    st.divider()
    
    # Action Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Chat", use_container_width=True):
            # Create a brand new session ID and initialize it
            new_id = str(uuid.uuid4())
            st.session_state.current_session_id = new_id
            st.session_state.history[new_id] = {
                "title": "New Chat",
                "messages": [{"role": "system", "content": "You are a professional Python and C++ coder, AI expert, and great teacher."}]
            }
            save_all_history(st.session_state.history)
            st.rerun()
    with col2:
        st.button("⏹️ Interrupt", use_container_width=True, type="primary")
        
    st.divider()
    
    # Token Deciders
    with st.expander("Advanced Settings"):
        max_input_tokens = st.slider("Max Input Context", min_value=512, max_value=8192, value=4096, step=512)
        max_output_tokens = st.slider("Max Output Tokens", min_value=256, max_value=16384, value=2048, step=256)

    st.divider()
    
    # Render Chat History List
    st.subheader("📚 Chat History")
    
    # We iterate over a copy of items to allow deletion during iteration
    for session_id, session_data in list(st.session_state.history.items()):
        # Exclude completely empty new chats from cluttering history
        if len(session_data["messages"]) <= 1 and session_id != current_session:
            continue 
            
        hist_col1, hist_col2 = st.columns([5, 1])
        with hist_col1:
            # Button to load this specific chat
            if st.button(session_data.get("title", "Chat"), key=f"load_{session_id}", use_container_width=True):
                st.session_state.current_session_id = session_id
                st.rerun()
        with hist_col2:
            # Button to delete this specific chat
            if st.button("🗑️", key=f"del_{session_id}"):
                del st.session_state.history[session_id]
                save_all_history(st.session_state.history)
                # If we deleted the active chat, reset to a new one
                if st.session_state.current_session_id == session_id:
                    st.session_state.current_session_id = str(uuid.uuid4())
                    st.session_state.history[st.session_state.current_session_id] = {"title": "New Chat", "messages": [{"role": "system", "content": "You are a professional Python and C++ coder, AI expert, and great teacher."}]}
                st.rerun()

# --- Display Current Chat Messages ---
for msg in messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "time_taken" in msg:
                st.caption(f"⏱️ Generated in {msg['time_taken']:.2f}s")

# --- Chat Input & Processing ---
prompt_data = st.chat_input("Ask anything...(Paste images/docs directly here!)", accept_file="multiple")

if prompt_data:
    prompt_text = prompt_data.text
    uploaded_files = prompt_data.files
    
    context_text = ""
    if uploaded_files:
        for file in uploaded_files:
            extracted = utils.extract_text_from_file(file)
            context_text += f"\n--- Content from {file.name} ---\n{extracted}\n"
            
    full_prompt = prompt_text
    if context_text:
        full_prompt = f"{prompt_text}\n\n[Refer to the attached context:]\n{context_text}"
        
    messages.append({"role": "user", "content": full_prompt})
    
    # Update title based on the first prompt and save
    st.session_state.history[current_session]["title"] = get_chat_title(messages)
    save_all_history(st.session_state.history)
    
    with st.chat_message("user"):
        if prompt_text:
            st.markdown(prompt_text) 
        if context_text:
            st.caption(f"*(Included {len(uploaded_files)} attached documents/images)*")

    # Generate AI Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # We track thoughts and final content separately!
        thoughts_text = ""
        content_text = ""
        
        # Pre-allocate message slot
        messages.append({"role": "assistant", "content": ""})
        
        try:
            start_time = time.time() # Start timer
            
            completion = client.chat.completions.create(
                model=current_model_id,
                messages=messages[:-1], # Send all except the empty one
                temperature=0.6,
                max_tokens=max_output_tokens,
                stream=True,
            )
            
            for chunk in completion:
                # Handle reasoning (thoughts)
                reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
                if reasoning:
                    thoughts_text += reasoning
                
                # Handle actual response
                content = chunk.choices[0].delta.content
                if content:
                    content_text += content
                
                # Render to screen based on toggle
                display_text = ""
                if show_thoughts and thoughts_text:
                    display_text += f"> 🤔 **AI Thoughts:**\n> *{thoughts_text}*\n\n---\n\n"
                display_text += content_text
                
                response_placeholder.markdown(display_text + "▌")
                
                # Save ONLY the final content to history (keeps memory clean)
                messages[-1]["content"] = content_text
            
            end_time = time.time() # End timer
            time_taken = end_time - start_time
            messages[-1]["time_taken"] = time_taken # Save timer to history
            
            # Final render without the cursor
            final_display = f"> 🤔 **AI Thoughts:**\n> *{thoughts_text}*\n\n---\n\n" + content_text if (show_thoughts and thoughts_text) else content_text
            response_placeholder.markdown(final_display)
            st.caption(f"⏱️ Generated in {time_taken:.2f}s")
            
            # Save the completed chat to file
            save_all_history(st.session_state.history)
            
        except Exception as e:
            st.error(f"Failed to connect to local model. Error: {e}")
            messages.pop() 
            save_all_history(st.session_state.history)
