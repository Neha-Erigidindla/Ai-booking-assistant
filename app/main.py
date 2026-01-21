import streamlit as st
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.rag_pipeline import RAGPipeline
from app.chat_logic import ChatLogic
from app.booking_flow import BookingFlow
from app.admin_dashboard import show_admin_dashboard
from app.config import MAX_MEMORY_MESSAGES


def initialize_session_state():
    """Initialize all session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "rag_pipeline" not in st.session_state:
        st.session_state.rag_pipeline = RAGPipeline()
    
    if "chat_logic" not in st.session_state:
        st.session_state.chat_logic = ChatLogic(st.session_state.rag_pipeline)
    
    if "booking_flow" not in st.session_state:
        st.session_state.booking_flow = BookingFlow(st.session_state.chat_logic)
    
    if "booking_data" not in st.session_state:
        st.session_state.booking_data = {}
    
    if "awaiting_confirmation" not in st.session_state:
        st.session_state.awaiting_confirmation = False
    
    if "pdfs_uploaded" not in st.session_state:
        st.session_state.pdfs_uploaded = False
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "chat"


# def show_welcome_message():
#     """Show welcome message when chat is empty"""
#     if len(st.session_state.messages) == 0:
#         st.markdown("""
#         <div style='padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin: 20px 0; color: white;'>
#             <h2 style='text-align: center; margin-bottom: 15px;'>👋 Welcome to AI Booking Assistant!</h2>
#             <p style='text-align: center; font-size: 16px; margin-bottom: 20px;'>
#                 I'm your intelligent assistant for bookings and information
#             </p>
#             <div style='background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; backdrop-filter: blur(10px);'>
#                 <h3 style='margin-top: 0;'>✨ What I Can Do:</h3>
#                 <ul style='font-size: 14px; line-height: 1.8;'>
#                     <li>📄 <b>Answer questions</b> from your uploaded documents</li>
#                     <li>📅 <b>Make bookings</b> with smart validation and calendar picker</li>
#                     <li>⚡ <b>Instant validation</b> - I'll tell you if something's wrong</li>
#                     <li>📧 <b>Email confirmations</b> sent automatically</li>
#                     <li>💬 <b>Natural conversation</b> - just talk to me!</li>
#                 </ul>
#             </div>
#             <p style='text-align: center; margin-top: 20px; font-style: italic; font-size: 14px;'>
#                 💡 Try: "I want to book a doctor appointment" or upload PDFs to ask questions
#             </p>
#         </div>
#         """, unsafe_allow_html=True)

def show_welcome_message():
    st.markdown("""
    <div style="padding:30px;border-radius:18px;background:var(--gradient);color:white;margin-top:20px;">
        <h2 style="text-align:center;margin:0 0 10px 0;">👋 Hey there!</h2>
        <p style="text-align:center;font-size:16px;margin-bottom:18px;">
            I'm your <b>AI Booking Assistant</b>. I can help you book appointments & answer questions from PDFs.
        </p>
        <div style="padding:18px;background:rgba(255,255,255,0.15);border-radius:14px;">
            <b>✨ Try saying:</b>
            <ul>
                <li>“Book an appointment for tomorrow”</li>
                <li>“How much is the facial treatment?”</li>
                <li>“Upload PDF and ask questions about it”</li>
            </ul>
        </div>
        <p style="text-align:center;margin-top:15px;">
            Upload a PDF or just start chatting 💬
        </p>
    </div>
    """, unsafe_allow_html=True)



def chat_page():
    """Main chat interface with enhanced UI"""
    st.title("🤖 AI Booking Assistant")
    
    # Sidebar
    with st.sidebar:
        st.header("📚 Document Management")
        
        # PDF Upload Section
        with st.container():
            st.markdown("### 📤 Upload Documents")
            uploaded_files = st.file_uploader(
                "Upload PDF documents",
                type=['pdf'],
                accept_multiple_files=True,
                key="pdf_uploader",
                help="Upload service brochures, menus, or information PDFs"
            )
            
            if uploaded_files:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📤 Process", use_container_width=True, type="primary"):
                        with st.spinner("🔄 Processing..."):
                            success, message = st.session_state.rag_pipeline.process_pdfs(uploaded_files)
                            
                            if success:
                                st.success(f"✅ {message}")
                                st.session_state.pdfs_uploaded = True
                                st.balloons()
                            else:
                                st.error(f"❌ {message}")
                
                with col2:
                    if st.session_state.pdfs_uploaded:
                        if st.button("🔄 Clear", use_container_width=True):
                            success, message = st.session_state.rag_pipeline.clear_vector_store()
                            if success:
                                st.success(message)
                                st.session_state.pdfs_uploaded = False
                                st.rerun()
        
        # Status & Suggested Questions
        if st.session_state.pdfs_uploaded:
            st.success("✅ Documents ready")
            
            # Show suggested questions if available
            if hasattr(st.session_state, 'pdf_suggestions') and st.session_state.pdf_suggestions:
                with st.expander("💡 Suggested Questions", expanded=True):
                    st.markdown("**Try asking:**")
                    for q in st.session_state.pdf_suggestions:
                        if st.button(q, key=f"suggest_{q}", use_container_width=True):
                            # Add question to chat
                            st.session_state.messages.append({"role": "user", "content": q})
                            response = generate_response(q)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.rerun()
        else:
            st.info("📄 No documents loaded")
        
        st.markdown("---")
        
        # Chat Controls
        st.markdown("### 🎛️ Controls")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.booking_data = {}
            st.session_state.awaiting_confirmation = False
            if hasattr(st.session_state, 'suggested_date'):
                delattr(st.session_state, 'suggested_date')
            if hasattr(st.session_state, 'suggested_time'):
                delattr(st.session_state, 'suggested_time')
            st.success("Chat cleared!")
            st.rerun()
        
        # Booking Progress
        if st.session_state.booking_data:
            st.markdown("---")
            st.markdown("### 📋 Booking Progress")
            
            # Get only valid required fields (exclude any extra fields)
            required_fields = ['name', 'email', 'phone', 'booking_type', 'date', 'time']
            collected = [k for k in required_fields if k in st.session_state.booking_data and st.session_state.booking_data[k]]
            
            # Calculate progress (ensure it's between 0 and 1)
            progress = min(len(collected) / len(required_fields), 1.0)
            
            st.progress(progress)
            st.caption(f"{len(collected)}/{len(required_fields)} fields collected")
            
            # Show collected fields
            field_emoji = {
                'name': '👤',
                'email': '📧',
                'phone': '📱',
                'booking_type': '🎯',
                'date': '📅',
                'time': '⏰'
            }
            
            for field in collected:
                emoji = field_emoji.get(field, '✓')
                st.text(f"{emoji} {field.replace('_', ' ').title()}")
        
        st.markdown("---")
        
        # Quick Tips & PDF Guidelines
        with st.expander("💡 Quick Tips", expanded=False):
            st.markdown("""
            **📅 Making a Booking:**
            - Say "I want to book"
            - Use calendar/time pickers when they appear
            - I'll validate everything in real-time
            
            **🗓️ Date & Time:**
            - Use YYYY-MM-DD format (2025-01-25)
            - Use HH:MM format (14:30)
            - Can't book past dates/times
            
            **📧 Email Format:** 
            - name@example.com
            
            **📱 Phone:** 
            - 10-15 digits
            """)
        
        with st.expander("📄 PDF Upload Guidelines", expanded=False):
            st.markdown("""
            **✅ Your PDFs should include:**
            - Service descriptions and offerings
            - Pricing information
            - Business hours and availability
            - Contact information (phone, email, address)
            - FAQ or helpful information
            
            **❌ Avoid uploading:**
            - Scanned images (no selectable text)
            - Password-protected files
            - Files with less than 100 characters
            - Only tables/numbers without context
            
            **💡 Best practices:**
            - Use text-based PDFs (not scanned)
            - Include detailed descriptions
            - Organize with clear headings
            - Keep information current
            
            *The system will validate your PDFs and give you specific feedback!*
            """)
        
        # Stats
        st.markdown("---")
        st.markdown("### 📊 Session Stats")
        st.metric("Messages", len(st.session_state.messages))
        if st.session_state.pdfs_uploaded:
            st.metric("Documents", "Active", delta="Ready")
    
    # Main chat area
    if len(st.session_state.messages) == 0:
        show_welcome_message()
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    
    # Chat input
    if prompt := st.chat_input("💬 Type your message here...", key="chat_input"):
        
        # Check if user is using widget selection
        widget_type, widget_value = st.session_state.chat_logic.process_widget_selection(prompt)
        
        if widget_type:
            # Replace message with actual value
            if widget_type == 'date':
                prompt = widget_value
            elif widget_type == 'time':
                prompt = widget_value
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # with st.chat_message("user", avatar="👤"):
        #     st.markdown(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("`typing` <span class='typing-dot'>●</span><span class='typing-dot' style='animation-delay:0.2s;'>●</span><span class='typing-dot' style='animation-delay:0.4s;'>●</span>", unsafe_allow_html=True)
            time.sleep(0.7)


        
        # Generate response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤔 Thinking..."):
                response = generate_response(prompt)
                st.markdown(response)
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Manage memory
        st.session_state.messages = st.session_state.chat_logic.manage_memory(
            st.session_state.messages
        )
        
        st.rerun()


def generate_response(prompt):
    """Generate response based on intent with better error handling"""
    try:
        # Detect intent
        intent = st.session_state.chat_logic.detect_intent(
            prompt,
            st.session_state.messages
        )
        
        # Handle booking flow
        if intent == 'booking' or st.session_state.booking_data or st.session_state.awaiting_confirmation:
            response, updated_data, awaiting, complete = st.session_state.booking_flow.handle_booking_intent(
                prompt,
                st.session_state.booking_data,
                st.session_state.awaiting_confirmation
            )
            
            st.session_state.booking_data = updated_data
            st.session_state.awaiting_confirmation = awaiting
            
            if complete:
                st.session_state.booking_data = {}
                st.session_state.awaiting_confirmation = False
                if hasattr(st.session_state, 'suggested_date'):
                    delattr(st.session_state, 'suggested_date')
                if hasattr(st.session_state, 'suggested_time'):
                    delattr(st.session_state, 'suggested_time')
            
            return response
        
        # Handle RAG query
        elif intent == 'query':
            if st.session_state.pdfs_uploaded:
                return st.session_state.chat_logic.get_rag_response(
                    prompt,
                    st.session_state.messages
                )
            else:
                prompt_lower = prompt.lower().strip()
                
                # If user mentioned upload/document
                if any(word in prompt_lower for word in ['upload', 'document', 'pdf', 'file']):
                    return (
                        "I see you're interested in uploading documents! 📄\n\n"
                        "To upload PDFs:\n"
                        "1. Use the file uploader in the left sidebar\n"
                        "2. Select your PDF files\n"
                        "3. Click '📤 Process PDFs'\n"
                        "4. Then ask me questions about the content!\n\n"
                        "💡 Upload service brochures, menus, pricing lists, etc."
                    )
                
                # If simple yes/no
                if prompt_lower in ['yes', 'no', 'ok', 'sure']:
                    return st.session_state.chat_logic.get_general_response(
                        prompt,
                        st.session_state.messages
                    )
                
                return (
                    "I'd be happy to answer questions about our services! However, I don't have any documents "
                    "uploaded yet.\n\n"
                    "**You can:**\n"
                    "• 📄 Upload PDFs in the sidebar to enable Q&A\n"
                    "• 📅 Say 'I want to book' to make a booking\n"
                    "• 💬 Ask general questions about our booking services"
                )
        
        # General conversation
        else:
            return st.session_state.chat_logic.get_general_response(
                prompt,
                st.session_state.messages
            )
    
    except Exception as e:
        return (
            f"❌ I encountered an error: {str(e)}\n\n"
            "Please try again. If the issue persists:\n"
            "• Clear the chat and start fresh\n"
            "• Try rephrasing your message\n"
            "• Check if PDFs were uploaded correctly"
        )


def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="AI Booking Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': "AI Booking Assistant - Smart bookings with validation"
        }
    )
    
    # Custom CSS
    # st.markdown("""
    #     <style>
    #     .stChatMessage {
    #         padding: 1rem;
    #         border-radius: 0.5rem;
    #         margin-bottom: 1rem;
    #     }
    #     .stButton>button {
    #         border-radius: 0.5rem;
    #         font-weight: 500;
    #     }
    #     .stProgress > div > div {
    #         background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    #     }
    #     </style>
    # """, unsafe_allow_html=True)
        # Custom CSS (Gen-Z aesthetic upgrade)
    st.markdown("""
        <style>
        :root {
            --primary: #6d5dfc;
            --secondary: #4b5dff;
            --gradient: linear-gradient(135deg, #6d5dfc 0%, #4b5dff 100%);
            --glass-bg: rgba(255,255,255,0.08);
            --glass-border: rgba(255,255,255,0.15);
            --radius: 14px;
        }

        /* App background */
        .main {
            background: #0d1117;
            color: white;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: rgba(18, 21, 27, 0.9);
            backdrop-filter: blur(12px);
            border-right: 1px solid rgba(255,255,255,0.05);
        }

        /* Buttons */
        .stButton>button {
            background: var(--gradient);
            color: white;
            border-radius: var(--radius);
            padding: 8px 16px;
            font-weight: 600;
            border: none;
            transition: 0.2s;
        }
        .stButton>button:hover {
            filter: brightness(1.1);
            transform: translateY(-1px);
        }

        /* Chat Input */
        textarea {
            border-radius: var(--radius) !important;
            background: rgba(255,255,255,0.07) !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            color: white !important;
        }

        /* Chat bubbles */
        div[data-testid="stChatMessageContainer"] {
            padding: 0 !important;
        }
        div[data-testid="stChatMessage"] {
            border-radius: var(--radius);
            padding: 12px 16px;
            margin-bottom: 12px;
            backdrop-filter: blur(12px);
        }
        div[data-testid="stChatMessage"].st-chat-message-user {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            margin-left: auto;
            max-width: 80%;
        }
        div[data-testid="stChatMessage"].st-chat-message-assistant {
            background: rgba(109, 93, 252, 0.18);
            border: 1px solid rgba(109, 93, 252, 0.25);
            max-width: 80%;
        }

        /* Typing animation */
        @keyframes typing {
            0% { opacity: 0.2; }
            20% { opacity: 1; }
            100% { opacity: 0.2; }
        }
        .typing-dot {
            animation: typing 1s infinite ease-in-out;
        }
        </style>
    """, unsafe_allow_html=True)

    
    # Initialize
    initialize_session_state()
    
    # Navigation
    with st.sidebar:
        st.title("🎯 Navigation")
        
        page = st.radio(
            "Go to:",
            ["💬 Chat & Booking", "📊 Admin Dashboard"],
            index=0,
            key="page_selector"
        )
        
        st.markdown("---")
    
    # Route
    if page == "💬 Chat & Booking":
        chat_page()
    elif page == "📊 Admin Dashboard":
        show_admin_dashboard()


if __name__ == "__main__":
    main()