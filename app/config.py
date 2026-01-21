import os
import streamlit as st

# ============================================================================
# LLM Configuration
# ============================================================================
# Get API key from Streamlit secrets or environment
if hasattr(st, 'secrets') and 'GROQ_API_KEY' in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# IMPORTANT: Use current supported model (llama-3.1-70b-versatile is DECOMMISSIONED)
GROQ_MODEL = "llama-3.3-70b-versatile"

# ============================================================================
# Email Configuration
# ============================================================================
if hasattr(st, 'secrets'):
    SMTP_SERVER = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = st.secrets.get("SMTP_PORT", 587)
    SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "")
    SENDER_PASSWORD = st.secrets.get("SENDER_PASSWORD", "")
else:
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

# ============================================================================
# Database Configuration
# ============================================================================
# SQLite Configuration (default)
SQLITE_DB_PATH = "db/bookings.db"

# Optional: Supabase Configuration (if you want to use it instead)
USE_SUPABASE = False
if hasattr(st, 'secrets'):
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
else:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ============================================================================
# RAG Configuration
# ============================================================================
CHROMA_PERSIST_DIR = "db/chroma_db"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Number of relevant chunks to retrieve for RAG
RAG_K_CHUNKS = 4

# ============================================================================
# Chat Configuration
# ============================================================================
# Maximum number of messages to keep in conversation memory
MAX_MEMORY_MESSAGES = 25

# ============================================================================
# Booking Configuration
# ============================================================================
BOOKING_TYPES = [
    "Doctor Appointment",
    "Salon Service",
    "Hotel Reservation",
    "Event Booking",
    "Fitness Class",
    "Restaurant Reservation",
    "Spa Treatment",
    "Consultation"
]

BOOKING_STATUSES = [
    "confirmed",
    "pending",
    "cancelled",
    "completed"
]

# ============================================================================
# System Prompts
# ============================================================================
SYSTEM_PROMPT = """You are a helpful and friendly AI booking assistant. Your role is to:

1. **Answer questions** about services using information from uploaded documents (RAG)
2. **Help users make bookings** by collecting necessary information through conversation
3. **Be professional, friendly, and efficient** in all interactions

When a user wants to make a booking, you need to collect:
- Customer name
- Email address (valid format)
- Phone number (10-15 digits)
- Type of service/booking
- Preferred date (YYYY-MM-DD format)
- Preferred time (HH:MM format)

Always:
- Confirm all details before finalizing the booking
- Be patient and ask one question at a time
- Validate formats for email, date, and time
- Provide helpful error messages if information is incorrect
- Thank the user after completing a booking

Keep your responses concise and friendly."""

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided context.

Instructions:
- Use ONLY the information from the provided context to answer questions
- If the context doesn't contain the answer, politely say you don't have that information
- Be concise but complete in your answers
- If asked about booking, guide the user to say "I want to book" to start the booking process
- Cite sources when relevant (e.g., "According to the service menu...")"""

BOOKING_SYSTEM_PROMPT = """You are a booking assistant helping users make reservations.

Your task:
- Extract booking information from user messages
- Ask for missing required fields ONE AT A TIME
- Validate information formats
- Show empathy and patience
- Confirm all details before saving

Required fields:
1. Name
2. Email (format: user@example.com)
3. Phone (format: 10-15 digits)
4. Service type
5. Date (format: YYYY-MM-DD)
6. Time (format: HH:MM)"""

# ============================================================================
# Required Booking Fields
# ============================================================================
BOOKING_FIELDS = {
    "name": {
        "label": "Customer Name",
        "question": "What's your name?",
        "validation": "length",
        "min_length": 2,
        "max_length": 100
    },
    "email": {
        "label": "Email Address",
        "question": "What's your email address?",
        "validation": "email",
        "pattern": r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
    },
    "phone": {
        "label": "Phone Number",
        "question": "What's your phone number?",
        "validation": "phone",
        "min_length": 10,
        "max_length": 15
    },
    "booking_type": {
        "label": "Service Type",
        "question": "What type of service would you like to book?",
        "validation": "choice",
        "choices": BOOKING_TYPES
    },
    "date": {
        "label": "Preferred Date",
        "question": "What date would you prefer? (Please use YYYY-MM-DD format, e.g., 2025-01-25)",
        "validation": "date",
        "format": "%Y-%m-%d"
    },
    "time": {
        "label": "Preferred Time",
        "question": "What time works best for you? (Please use HH:MM format, e.g., 14:30)",
        "validation": "time",
        "format": "%H:%M"
    }
}

# ============================================================================
# UI Configuration
# ============================================================================
PAGE_TITLE = "AI Booking Assistant"
PAGE_ICON = "🤖"
LAYOUT = "wide"

# Chat avatars
USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

# Status emojis
SUCCESS_EMOJI = "✅"
ERROR_EMOJI = "❌"
WARNING_EMOJI = "⚠️"
INFO_EMOJI = "ℹ️"
LOADING_EMOJI = "🔄"

# ============================================================================
# Validation Messages
# ============================================================================
VALIDATION_MESSAGES = {
    "email_invalid": "Please provide a valid email address (e.g., user@example.com)",
    "phone_invalid": "Please provide a valid phone number (10-15 digits)",
    "date_invalid": "Please provide a valid date in YYYY-MM-DD format (e.g., 2025-01-25)",
    "time_invalid": "Please provide a valid time in HH:MM format (e.g., 14:30)",
    "field_required": "This field is required. Please provide the information.",
    "field_too_short": "This field is too short. Please provide more information.",
    "field_too_long": "This field is too long. Please provide less information."
}

# ============================================================================
# Success Messages
# ============================================================================
SUCCESS_MESSAGES = {
    "booking_confirmed": "✅ Booking confirmed successfully! Your booking ID is #{booking_id}",
    "email_sent": "📧 A confirmation email has been sent to {email}",
    "pdfs_processed": "✅ Successfully processed {count} PDF(s) with {chunks} text chunks",
    "chat_cleared": "🗑️ Chat history cleared successfully",
    "docs_cleared": "🗑️ All documents cleared successfully"
}

# ============================================================================
# Error Messages
# ============================================================================
ERROR_MESSAGES = {
    "no_pdfs": "📄 Please upload PDF documents first to enable Q&A",
    "booking_failed": "❌ Sorry, there was an error saving your booking. Please try again.",
    "email_failed": "⚠️ Your booking was saved, but we couldn't send the confirmation email.",
    "pdf_processing_failed": "❌ Failed to process PDFs. Please try again.",
    "general_error": "❌ An error occurred. Please try again or contact support."
}