# 🤖 AI Booking Assistant

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com)

> An intelligent AI-powered booking assistant with RAG (Retrieval-Augmented Generation), conversational booking flow, real-time validation, email confirmations, and comprehensive admin dashboard.

## 🌟 Live Demo

🔗 **[Try it Live on Streamlit Cloud](https://ai-booking-assistant-neo.streamlit.app)**

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Deployment](#-deployment)
- [Challenges & Solutions](#-challenges--solutions)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🎯 Core Features

- **📄 RAG-Powered Q&A**: Upload PDFs and ask questions with intelligent document retrieval
- **📅 Conversational Booking**: Natural language booking flow with multi-turn dialogue
- **✅ Real-Time Validation**: Instant validation with helpful error messages
- **📧 Email Confirmations**: Automatic booking confirmation emails
- **📊 Admin Dashboard**: Comprehensive booking management interface
- **🧠 Conversation Memory**: Maintains context for last 25 messages
- **📅 Interactive Widgets**: Calendar and time picker for easy selection

### 🔍 Advanced Features

- **PDF Content Validation**: Detects document type (service info vs tickets/research papers)
- **Suggested Questions**: Auto-generates relevant questions based on PDF content
- **Smart Intent Detection**: Distinguishes between queries and booking requests
- **Service-Specific Messages**: Customized confirmation messages per service type
- **Past Date/Time Prevention**: Blocks booking in the past
- **Progress Tracking**: Visual progress bar for booking completion

### 💼 Supported Services

- 🏥 Doctor Appointment
- 💇 Salon Service
- 🏨 Hotel Reservation
- 🎉 Event Booking
- 💪 Fitness Class
- 🍽️ Restaurant Reservation
- ✈️ Travel Booking
- 🧖 Spa Treatment
- 📋 Consultation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface (Streamlit)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Chat Widget  │  │ PDF Upload   │  │ Admin Panel  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Chat Logic   │  │ Booking Flow │  │ RAG Pipeline │      │
│  │ - Intent     │  │ - Validation │  │ - Embeddings │      │
│  │ - Memory     │  │ - Extraction │  │ - Retrieval  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────┐
    │   Groq LLM   │ │ ChromaDB │ │ SQLite   │
    │   (Llama)    │ │ (Vectors)│ │ (Data)   │
    └──────────────┘ └──────────┘ └──────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ SMTP Email   │
                    │   Service    │
                    └──────────────┘
```

### 📊 Data Flow

1. **User Input** → Chat Interface
2. **Intent Detection** → Determines query vs booking
3. **RAG Query Path**:
   - PDF → Text Extraction → Chunking → Embeddings → ChromaDB
   - User Query → Similarity Search → Context Retrieval → LLM Response
4. **Booking Path**:
   - User Input → Field Extraction → Validation → Confirmation → Database → Email
5. **Admin Dashboard** → SQLite Query → Display & Management

---

## 🛠️ Tech Stack

### Core Technologies

| Technology | Purpose | Version |
|-----------|---------|---------|
| **Python** | Backend Language | 3.10+ |
| **Streamlit** | Web Framework | 1.31.0 |
| **LangChain** | LLM Framework | 0.1.9 |
| **Groq (Llama 3.3)** | LLM Provider | Latest |
| **ChromaDB** | Vector Database | 0.4.22 |
| **SQLite** | Relational Database | Built-in |

### Libraries & Tools

- **langchain-groq**: LLM integration
- **sentence-transformers**: Text embeddings
- **pypdf**: PDF text extraction
- **pandas**: Data manipulation
- **smtplib**: Email sending

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Git
- Gmail account (for email confirmations)
- Groq API key ([Get it here](https://console.groq.com))

### Step 1: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-booking-assistant.git
cd ai-booking-assistant
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Configuration

Create `.streamlit/secrets.toml`:

```toml
# Required
GROQ_API_KEY = "your_groq_api_key_here"

# Optional (for email confirmations)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
```

**Note**: For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (optional, alternative to secrets.toml):

```env
GROQ_API_KEY=your_groq_api_key
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Customization Options

Edit `app/config.py` to customize:

```python
# Booking Types
BOOKING_TYPES = [
    "Doctor Appointment",
    "Salon Service",
    # Add your custom types
]

# Memory Settings
MAX_MEMORY_MESSAGES = 25

# RAG Settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
```

---

## 🚀 Usage Guide

### Running Locally

```bash
streamlit run app/main.py
```

The app will open at `http://localhost:8501`

### Using the Application

#### 📄 For Document Q&A:

1. **Upload PDFs**: Click the file uploader in sidebar
2. **Process**: Click "📤 Process PDFs"
3. **View Suggestions**: See auto-generated questions
4. **Ask Questions**: Type or click suggested questions

#### 📅 For Making Bookings:

1. **Start**: Say "I want to book"
2. **Provide Info**: Answer each question
   - Name
   - Email
   - Phone
   - Service type
   - Date (YYYY-MM-DD)
   - Time (HH:MM)
3. **Use Widgets** (optional): Use calendar/time pickers in sidebar
4. **Confirm**: Review details and type "yes"
5. **Done**: Receive booking ID and email confirmation

#### 📊 For Admin:

1. **Navigate**: Go to "Admin Dashboard" in sidebar
2. **View**: See all bookings, search, filter
3. **Manage**: Confirm, cancel, or delete bookings
4. **Export**: Download bookings as CSV

---

## 📁 Project Structure

```
ai-booking-assistant/
│
├── app/
│   ├── main.py                 # Streamlit entry point
│   ├── chat_logic.py          # Intent detection & memory
│   ├── booking_flow.py        # Booking conversation flow
│   ├── rag_pipeline.py        # PDF processing & RAG
│   ├── admin_dashboard.py     # Admin interface
│   ├── tools.py               # Email & validation tools
│   └── config.py              # Configuration settings
│
├── db/
│   ├── database.py            # SQLite operations
│   ├── bookings.db           # Database (auto-created)
│   └── chroma_db/            # Vector store (auto-created)
│
├── .streamlit/
│   └── secrets.toml          # API keys & credentials
│
├── requirements.txt          # Python dependencies
├── README.md                # This file
└── .gitignore              # Git ignore rules
```

---

## 📡 API Reference

### BookingFlow Class

```python
class BookingFlow:
    def handle_booking_intent(user_message, booking_data, awaiting_confirmation):
        """Main booking flow handler"""
        
    def _validate_extracted_data(extracted_data, existing_data):
        """Validates user input with detailed errors"""
        
    def _save_booking(booking_data):
        """Saves booking to database"""
```

### RAGPipeline Class

```python
class RAGPipeline:
    def process_pdfs(pdf_files):
        """Process and index PDFs"""
        
    def query(question, k=4):
        """Retrieve relevant context"""
        
    def detect_pdf_type(text):
        """Detect PDF content type"""
        
    def get_suggested_questions(pdf_content):
        """Generate question suggestions"""
```

### Database Schema

```sql
-- Customers Table
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bookings Table
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    booking_type TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

---

## ☁️ Deployment

### Deploy to Streamlit Cloud

1. **Push to GitHub**:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Go to Streamlit Cloud**:
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository
   - Main file: `app/main.py`

3. **Add Secrets**:
   In Advanced settings, add:
   ```toml
   GROQ_API_KEY = "your_key"
   SENDER_EMAIL = "your_email"
   SENDER_PASSWORD = "your_password"
   ```

4. **Deploy**: Click "Deploy" and wait!

### Custom Domain (Optional)

After deployment, you can add a custom domain in Streamlit Cloud settings.

---

## 🎯 Challenges & Solutions

### Challenge 1: Intent Detection Accuracy
**Problem**: Questions like "How do I make an appointment?" triggered booking instead of answering from PDFs.

**Solution**: 
- Expanded non-booking phrase list
- Made booking detection more strict
- Only explicit phrases like "I want to book" trigger booking flow

### Challenge 2: Email Time Format
**Problem**: Times like "1:00" caused email template errors.

**Solution**: 
- Enforced HH:MM format: `f"{hours:02d}:{mins:02d}"`
- All times now properly formatted (01:00, 09:30, etc.)

### Challenge 3: PDF Content Relevance
**Problem**: Users uploaded irrelevant PDFs (tickets, research papers).

**Solution**:
- Built PDF type detection system
- Warns users when wrong type detected
- Suggests what content should be in PDFs

### Challenge 4: Past Date/Time Bookings
**Problem**: Users could book appointments in the past.

**Solution**:
- Real-time date validation against current date
- Time validation for same-day bookings
- Clear error messages with days/hours past

### Challenge 5: No Guidance on Questions
**Problem**: Users didn't know what to ask after uploading PDFs.

**Solution**:
- Auto-generate suggested questions from PDF content
- Clickable question buttons in sidebar
- Context-aware suggestions based on content type

---

## 🚀 Future Improvements

### Short Term (1-3 months)

- [ ] **Voice Input/Output (STT/TTS)**: Enable voice-based interactions
- [ ] **Multi-language Support**: Translate interface to Spanish, French, Hindi
- [ ] **SMS Notifications**: Send booking confirmations via SMS
- [ ] **Calendar Integration**: Sync with Google Calendar/Outlook

### Medium Term (3-6 months)

- [ ] **Payment Integration**: Accept payments via Stripe/PayPal
- [ ] **User Authentication**: Login system for customers
- [ ] **Booking Modifications**: Allow users to reschedule/cancel
- [ ] **Advanced Analytics**: Revenue tracking, popular services, peak times
- [ ] **Mobile App**: React Native mobile version

### Long Term (6-12 months)

- [ ] **Multi-tenant System**: Support multiple businesses
- [ ] **AI Chatbot Training**: Fine-tune on specific business data
- [ ] **Video Consultations**: Integrate Zoom/Meet for virtual appointments
- [ ] **Recommendation Engine**: Suggest services based on history
- [ ] **Automated Reminders**: Send reminders 24h before appointments

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Add docstrings to all functions
- Include type hints where possible
- Write descriptive commit messages

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Neha-Erigidindla** - *Initial work* - [Github](https://github.com/Neha-Erigidindla)

---

## 🙏 Acknowledgments

- Groq for providing fast LLM inference
- Anthropic for Claude API inspiration
- LangChain community for excellent documentation
- Streamlit team for the amazing framework
- Open source community for various libraries

---

## 📞 Support

For issues, questions, or suggestions:

- 📧 Email: nehaerigidindla@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/Neha-Erigidindla/Ai-booking-assistant/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/Neha-Erigidindla/Ai-booking-assistant/discussions)

---

## 📊 Project Status

![GitHub last commit](https://img.shields.io/github/last-commit/Neha-Erigidindla/Ai-booking-assistant)
![GitHub issues](https://img.shields.io/github/issues/Neha-Erigidindla/Ai-booking-assistant)
![GitHub stars](https://img.shields.io/github/stars/Neha-Erigidindla/Ai-booking-assistant)
![GitHub forks](https://img.shields.io/github/forks/Neha-Erigidindla/Ai-booking-assistant)

---

<div align="center">

**⭐ Star this repo if you found it helpful!**

Made with ❤️ and ☕ by [Neha Erigidindla]

[Report Bug](https://github.com/Neha-Erigidindla/Ai-booking-assistant/issues) · [Request Feature](https://github.com/Neha-Erigidindla/Ai-booking-assistant/issues)

</div>

