"""
TalentScout Hiring Assistant - Main Streamlit Application
A chatbot for initial candidate screening and technical assessment.
"""

import streamlit as st
import uuid
import os
from datetime import datetime
from src.chatbot import HiringChatbot, ConversationPhase
from config.settings import settings

# Page configuration
st.set_page_config(
    page_title="TalentScout Hiring Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI


def initialize_session_state():
    """Initialize session state variables."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'chatbot' not in st.session_state:
        # Get API key
        api_key = os.getenv('GITHUB_TOKEN') or settings.GITHUB_TOKEN
        if not api_key:
            st.error("⚠️ OpenAI API key not found. Please set GITHUB_TOKEN environment variable.")
            st.stop()
        
        st.session_state.chatbot = HiringChatbot(api_key, settings.MODEL_NAME)
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        # Add initial greeting
        initial_message = "Hello! Welcome to TalentScout. Please type anything to begin the screening process."
        st.session_state.messages.append({"role": "assistant", "content": initial_message})
    
    if 'conversation_ended' not in st.session_state:
        st.session_state.conversation_ended = False
    
    if 'start_time' not in st.session_state:
        st.session_state.start_time = datetime.now()



def get_phase_description(phase):
    """Get user-friendly description of current phase."""
    phase_descriptions = {
        ConversationPhase.GREETING: "Getting Started",
        ConversationPhase.INFO_GATHERING: "Collecting Information",
        ConversationPhase.TECH_STACK: "Technical Skills Assessment",
        ConversationPhase.TECHNICAL_QUESTIONS: "Technical Interview",
        ConversationPhase.CLOSING: "Wrapping Up",
        ConversationPhase.ENDED: "Completed"
    }
    return phase_descriptions.get(phase, "In Progress")

def display_sidebar():
    """Display sidebar with conversation status and information."""
    with st.sidebar:
        # Header with better styling
        st.markdown("""
        <div class="sidebar-header">
            <h1>🤖 TalentScout</h1>
            <p>Hiring Assistant</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Current status with improved styling
        if hasattr(st.session_state.chatbot, 'phase'):
            phase_desc = get_phase_description(st.session_state.chatbot.phase)
            status_class = "status-info" if st.session_state.conversation_ended else "status-active"
            status_icon = "✓" if st.session_state.conversation_ended else "●"
            
            st.markdown(f"""
            <div class="status-badge {status_class}">
                {status_icon} {phase_desc}
            </div>
            """, unsafe_allow_html=True)
        
        # Enhanced progress tracking
        if hasattr(st.session_state.chatbot, 'candidate_data'):
            completion = st.session_state.chatbot.data_handler.get_completion_percentage(
                st.session_state.chatbot.candidate_data
            )
            
            st.markdown("""
            <div class="progress-container">
                <div class="progress-text">Interview Progress</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {}%"></div>
                </div>
                <div class="progress-percentage">{:.0f}% Complete</div>
            </div>
            """.format(completion, completion), unsafe_allow_html=True)
        
        # Information collected with better styling
        if hasattr(st.session_state.chatbot, 'candidate_data') and st.session_state.chatbot.candidate_data:
            st.markdown("### 📋 Information Collected")
            data = st.session_state.chatbot.data_handler.sanitize_data(
                st.session_state.chatbot.candidate_data
            )
            
            info_items = []
            if data.get('full_name'):
                info_items.append(f"👤 {data['full_name']}")
            if data.get('email'):
                info_items.append(f"📧 {data['email']}")
            if data.get('experience_years'):
                info_items.append(f"💼 {data['experience_years']} years experience")
            if data.get('desired_positions'):
                positions = data['desired_positions']
                if isinstance(positions, list):
                    positions = ', '.join(positions[:2])
                info_items.append(f"🎯 {positions}")
            if data.get('tech_stack'):
                tech_count = sum(len(techs) for techs in data['tech_stack'].values())
                info_items.append(f"⚡ {tech_count} technologies")
            
            for item in info_items:
                st.markdown(f'<div class="info-item">{item}</div>', unsafe_allow_html=True)
        
        # Enhanced help section
        st.markdown("---")
        st.markdown("### 💡 Quick Tips")
        st.markdown("""
        <div class="info-cards">
            <strong>📝 During the Interview:</strong><br>
              • Be specific and detailed<br>
              • Share real examples<br>
              • Ask questions if unclear<br><br>
        </div>
        <div class="info-cards">
            <strong>⏱️ Time Management:</strong><br>
              • Process takes 10-15 minutes<br>
              • Take time to think<br>
              • Type 'quit' to end early
        </div>
        """, unsafe_allow_html=True)
        
        # Session timer
        if hasattr(st.session_state, 'start_time'):
            elapsed = datetime.now() - st.session_state.start_time
            minutes = int(elapsed.total_seconds() // 60)
            seconds = int(elapsed.total_seconds() % 60)
            st.markdown(f"""
            <div class="info-item">
                ⏰ Session Time: {minutes:02d}:{seconds:02d}
            </div>
            """, unsafe_allow_html=True)
        
        # Enhanced reset button
        st.markdown("---")
        if st.button("🔄 Start New Session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def load_css():
    """Load custom CSS from external file."""
    try:
        # Try the assets folder first
        with open('assets/styles.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        try:
            # Try the root directory as fallback
            with open('styles.css', 'r', encoding='utf-8') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except FileNotFoundError:
            # Inline minimal styles as last resort
            st.markdown("""
            <style>
            .stApp {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #f8fafc;
            }
            .main .block-container {
                background: white;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                padding: 1.5rem;
                margin: 1rem auto;
            }
            </style>
            """, unsafe_allow_html=True)
            st.warning("⚠️ CSS file not found. Using basic styling.")

def display_chat_message(message):
    """Display a chat message with proper bubble styling."""
    role = message["role"]
    content = message["content"]
    timestamp = datetime.now().strftime("%H:%M")
    
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="message-bubble">
                <div class="message-header">👤 You</div>
                <div class="message-content">{content}</div>
                <div class="message-time">{timestamp}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <div class="message-bubble">
                <div class="message-header">🤖 TalentScout Assistant</div>
                <div class="message-content">{content}</div>
                <div class="message-time">{timestamp}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_chat_in_container():
    """Display all chat messages in a properly contained scrollable area."""
    
    # Create the main chat container
    st.markdown("""
    <div class="chat-container-wrapper">
        <div class="chat-messages-area" id="chat-messages">
    """, unsafe_allow_html=True)
    
    # Display all messages
    for message in st.session_state.messages:
        display_chat_message(message)
    
    # Close the container
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-scroll to bottom JavaScript
    st.markdown("""
    <script>
    setTimeout(function() {
        var chatArea = document.getElementById('chat-messages');
        if (chatArea) {
            chatArea.scrollTop = chatArea.scrollHeight;
        }
    }, 100);
    </script>
    """, unsafe_allow_html=True)

def enhanced_chat_input():
    """Enhanced chat input with better styling."""
    if not st.session_state.conversation_ended:
        st.markdown("---")
        st.markdown("### 💬 Your Message")
        
        with st.form(key="chat_form", clear_on_submit=True):
            col_input, col_button = st.columns([5, 1])
            
            with col_input:
                user_input = st.text_input(
                    "Type your message:",
                    placeholder="Share your thoughts, experiences, or ask questions...",
                    label_visibility="collapsed",
                    key="chat_input"
                )
            
            with col_button:
                st.markdown("<br>", unsafe_allow_html=True)  # Align button with input
                submit_button = st.form_submit_button("Send 📤", use_container_width=True)
            
            return user_input, submit_button
    
    return None, False

# Updated main function section for chat handling
def main():
    """Main application function with improved layout."""
    load_css()
    initialize_session_state()
    
    # Enhanced header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 TalentScout Hiring Assistant</h1>
        <p>Intelligent screening for technology positions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Warning for API key with better styling
    if not os.getenv('GITHUB_TOKEN') and not settings.GITHUB_TOKEN:
        st.markdown("""
        <div class="warning-card">
            <strong>⚠️ Setup Required:</strong><br>
            Please set your OpenAI API key as an environment variable:<br>
            <code>export GITHUB_TOKEN="your-api-key-here"</code>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Display sidebar
    display_sidebar()
    
    # Main chat area with improved layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat container with better styling
        st.markdown("### 💬 Live Conversation")
        
        # Display chat messages in the fixed container
        display_chat_in_container()
        
        # Enhanced input handling
        user_input, submit_button = enhanced_chat_input()
        
        if submit_button and user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get chatbot response with loading animation
            with st.spinner("🤔 TalentScout is thinking..."):
                try:
                    response, conversation_ended = st.session_state.chatbot.process_message(
                        user_input, 
                        st.session_state.session_id
                    )
                    
                    # Add assistant response
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Update conversation status
                    if conversation_ended:
                        st.session_state.conversation_ended = True
                        st.balloons()  # Celebration animation
                        st.success("🎉 Screening completed successfully!")
                    
                except Exception as e:
                    st.error(f"Sorry, there was an error: {str(e)}")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "I apologize for the technical difficulty. Please try again or start a new session if the problem persists."
                    })
            
            st.rerun()
    
    # Rest of the main function remains the same...
    with col2:
        # Enhanced tips section
        st.markdown("### 🎯 Interview Guide")
        st.markdown("""
        <div class="info-card">
            <strong>📋 Information Phase:</strong><br>
            • Provide accurate contact details<br>
            • Be specific about desired roles<br>
            • Mention years of experience<br><br>
        </div>
        <div class="info-card">
            <strong>🔧 Technical Skills:</strong><br>
            • List technologies you've used<br>
            • Mention proficiency levels<br>
            • Include frameworks & tools<br><br>
        </div>
        <div class="info-card">
            <strong>💡 Technical Questions:</strong><br>
            • Give detailed explanations<br>
            • Share real project examples<br>
            • Explain your thought process<br>
            • Ask for clarification if needed<br><br>
        </div>
        <div class="info-card">
            <strong>✅ Best Practices:</strong><br>
            • Take time to think thoroughly<br>
            • Be honest about your skills<br>
            • Show problem-solving approach<br>
            • Demonstrate communication skills
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()