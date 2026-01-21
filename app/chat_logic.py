import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.config import MAX_MEMORY_MESSAGES


class ChatLogic:
    """Enhanced chat logic with better intent detection"""
    
    def __init__(self, rag_pipeline):
        self.rag_pipeline = rag_pipeline
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM model"""
        try:
            if hasattr(st, 'secrets') and 'GROQ_API_KEY' in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
            else:
                api_key = os.getenv("GROQ_API_KEY", "")
            
            if not api_key:
                raise ValueError("GROQ_API_KEY not found")
            
            return ChatGroq(
                api_key=api_key,
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=2048,
            )
        except Exception as e:
            st.error(f"Failed to initialize LLM: {str(e)}")
            raise
    
    def detect_intent(self, user_message, conversation_history):
        """Detect user intent with improved recognition"""
        
        user_message_lower = user_message.lower().strip()
        
        # Exclude phrases that are NOT booking intents
        non_booking_phrases = [
            'upload', 'uploaded', 'document', 'pdf', 'file',
            'hi', 'hello', 'hey', 'good morning', 'good afternoon',
            'how are you', 'what can you do', 'help',
            'thank', 'thanks', 'bye', 'goodbye'
        ]
        
        # Check if message is clearly NOT a booking intent
        if any(phrase in user_message_lower for phrase in non_booking_phrases):
            # Exception: if conversation context shows we're in booking flow
            if conversation_history:
                recent_assistant_msg = None
                for msg in reversed(conversation_history[-3:]):
                    if msg['role'] == 'assistant':
                        recent_assistant_msg = msg['content'].lower()
                        break
                
                # If assistant just asked for booking info, continue booking flow
                if recent_assistant_msg and any(q in recent_assistant_msg for q in 
                    ['your name', 'your email', 'your phone', 'what date', 'what time', 
                     'type of service', 'confirm your booking', 'is this correct']):
                    return 'booking'
            
            # Otherwise, it's a general/query intent
            return 'query' if user_message_lower not in ['hi', 'hello', 'hey'] else 'general'
        
        # Check for date/time widget usage
        if any(phrase in user_message_lower for phrase in ['use selected date', 'use selected time', 'selected date', 'selected time']):
            return 'booking'
        
        # Explicit booking keywords
        booking_keywords = [
            'book a', 'make a booking', 'make an appointment', 
            'schedule a', 'reserve a', 'i want to book',
            'i need to book', 'i would like to book',
            'book appointment', 'make reservation',
            'can i book', 'can i schedule'
        ]
        
        # Check for explicit booking intent
        if any(keyword in user_message_lower for keyword in booking_keywords):
            return 'booking'
        
        # Check conversation context for ongoing booking
        if conversation_history:
            recent_messages = conversation_history[-3:]
            for msg in recent_messages:
                if msg['role'] == 'assistant':
                    content_lower = msg['content'].lower()
                    # Check if we're in the middle of collecting booking info
                    if any(indicator in content_lower for indicator in [
                        'information collected so far',
                        'your name?',
                        'your email',
                        'your phone',
                        'what date',
                        'what time',
                        'type of service',
                        'confirm your booking'
                    ]):
                        return 'booking'
        
        # Default to query
        return 'query'
    
    def get_rag_response(self, query, conversation_history):
        """Get response using RAG with relevance checking"""
        try:
            # Check if query is too vague for RAG
            vague_queries = ['yes', 'no', 'ok', 'okay', 'sure', 'nope', 'yeah', 'yep']
            if query.lower().strip() in vague_queries:
                return self.get_general_response(query, conversation_history)
            
            context = self.rag_pipeline.query(query)
            
            if not context:
                return "I couldn't find relevant information in the uploaded documents. Could you ask a more specific question? Or say 'I want to book' to make a booking!"
            
            memory_context = self._build_memory_context(conversation_history)
            
            prompt = f"""You are a helpful booking assistant. Answer the user's question using ONLY the context provided from uploaded documents.

Context from documents:
{context}

Conversation history:
{memory_context}

User question: {query}

CRITICAL RULES:
1. ONLY use information from the context above
2. If the context is NOT relevant to the question, say: "I don't see information about that in the uploaded documents. Could you ask something else or upload more relevant PDFs?"
3. If context seems unrelated to booking/services, say: "The uploaded document doesn't seem to contain service/booking information. Could you upload service brochures or menus?"
4. DO NOT make up information
5. DO NOT talk about topics unrelated to the user's services
6. Keep answers focused on bookings and services
7. Be concise and helpful

Answer:"""
            
            messages = [
                SystemMessage(content="You are a booking assistant. Only answer from provided context. Never make up information."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            result = response.content
            
            # Check if response seems to be hallucinating
            hallucination_indicators = [
                'fake image', 'detection', 'ai-generated', 'e-commerce refund',
                'binary classification', 'visual explanation'
            ]
            
            if any(indicator in result.lower() for indicator in hallucination_indicators):
                return (
                    "It looks like the uploaded PDF might not contain booking or service information. "
                    "Please upload PDFs with:\n"
                    "• Service descriptions\n"
                    "• Pricing\n"
                    "• Business hours\n"
                    "• Contact information\n\n"
                    "Or I can help you make a booking! Just say 'I want to book' 😊"
                )
            
            return result
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def get_general_response(self, user_message, conversation_history):
        """Get general conversational response with better handling"""
        try:
            user_message_lower = user_message.lower().strip()
            
            # Handle simple yes/no responses based on context
            if user_message_lower in ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay']:
                # Check recent conversation
                if conversation_history:
                    last_bot_msg = None
                    for msg in reversed(conversation_history[-3:]):
                        if msg['role'] == 'assistant':
                            last_bot_msg = msg['content'].lower()
                            break
                    
                    if last_bot_msg:
                        if 'want to book' in last_bot_msg or 'make a booking' in last_bot_msg:
                            return "Great! Let's start your booking. What's your name?"
                        elif 'upload' in last_bot_msg:
                            return "Perfect! Please use the file uploader in the sidebar to upload your PDF documents. 📄"
                
                return "Great! What would you like to do? I can help you with questions about our services or make a booking. Just say 'I want to book' to get started! 😊"
            
            elif user_message_lower in ['no', 'nope', 'nah', 'not really']:
                return "No problem! Is there anything else I can help you with? Feel free to ask questions or say 'I want to book' if you'd like to make a booking later! 😊"
            
            # Handle greetings
            greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
            if user_message_lower in greetings:
                return (
                    "Hello! 👋 Welcome to our booking assistant. I'm here to help you!\n\n"
                    "I can:\n"
                    "• Answer questions about our services (upload PDFs first)\n"
                    "• Help you make bookings\n"
                    "• Provide information and assistance\n\n"
                    "What would you like to do today?"
                )
            
            # Handle thank you
            if any(word in user_message_lower for word in ['thank', 'thanks', 'thx']):
                return "You're welcome! 😊 Is there anything else I can help you with?"
            
            # Handle goodbye
            if any(word in user_message_lower for word in ['bye', 'goodbye', 'see you']):
                return "Goodbye! Have a great day! Feel free to come back anytime you need help. 👋"
            
            # Handle document upload mentions
            if any(word in user_message_lower for word in ['upload', 'uploaded', 'document', 'pdf', 'file']):
                return (
                    "Great! To upload documents:\n"
                    "1. Look for the 📄 file uploader in the sidebar\n"
                    "2. Select your PDF files\n"
                    "3. Click '📤 Process PDFs'\n"
                    "4. Then you can ask me questions about the content!\n\n"
                    "📋 Your PDFs should contain service info, pricing, hours, etc."
                )
            
            # General conversation
            memory_context = self._build_memory_context(conversation_history)
            
            system_prompt = """You are a friendly and professional booking assistant. 

Key behaviors:
- Be warm, friendly, and helpful
- Keep responses concise (2-3 sentences max)
- If unclear what user wants, offer specific options
- Never make up information about services
- Guide users toward either asking questions (if PDFs uploaded) or making bookings

Available services:
- Doctor Appointment, Salon Service, Hotel Reservation
- Event Booking, Fitness Class, Restaurant Reservation
- Travel Booking, Spa Treatment, Consultation

NEVER discuss topics like "fake images", "AI detection", "e-commerce" or anything unrelated to booking services."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Recent conversation:\n{memory_context}\n\nUser: {user_message}\n\nRespond helpfully and concisely:")
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _build_memory_context(self, conversation_history):
        """Build context string from conversation history"""
        if not conversation_history:
            return "No previous conversation."
        
        recent_messages = conversation_history[-MAX_MEMORY_MESSAGES:]
        
        context_parts = []
        for msg in recent_messages:
            role = "User" if msg['role'] == 'user' else "Assistant"
            context_parts.append(f"{role}: {msg['content'][:200]}")
        
        return "\n".join(context_parts)
    
    def manage_memory(self, messages):
        """Manage conversation memory to keep only recent messages"""
        if len(messages) > MAX_MEMORY_MESSAGES:
            return messages[-MAX_MEMORY_MESSAGES:]
        return messages
    
    def process_widget_selection(self, user_message):
        """Check if user is referencing a widget selection"""
        user_lower = user_message.lower()
        
        # Check for date selection
        if 'use selected date' in user_lower or 'selected date' in user_lower:
            if hasattr(st.session_state, 'suggested_date'):
                return 'date', st.session_state.suggested_date
        
        # Check for time selection
        if 'use selected time' in user_lower or 'selected time' in user_lower:
            if hasattr(st.session_state, 'suggested_time'):
                return 'time', st.session_state.suggested_time
        
        return None, None