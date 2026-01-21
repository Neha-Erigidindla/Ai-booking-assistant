import os
import re
import streamlit as st
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from db.database import BookingDatabase
from app.tools import send_booking_email


class BookingFlow:
    """Complete booking flow with pricing and service-specific messages"""
    
    def __init__(self, chat_logic):
        self.chat_logic = chat_logic
        self.db = BookingDatabase()
        self.llm = self._initialize_llm()
        self.required_fields = ['name', 'email', 'phone', 'booking_type', 'date', 'time']
        
        # Service types with pricing
        self.service_pricing = {
            'Doctor Appointment': {'price': 100, 'icon': '🏥', 'message': 'Your health is our priority!'},
            'Salon Service': {'price': 50, 'icon': '💇', 'message': 'Get ready to look fabulous!'},
            'Hotel Reservation': {'price': 150, 'icon': '🏨', 'message': 'Enjoy your comfortable stay!'},
            'Event Booking': {'price': 200, 'icon': '🎉', 'message': "Let's make your event memorable!"},
            'Fitness Class': {'price': 30, 'icon': '💪', 'message': 'Time to get fit and healthy!'},
            'Restaurant Reservation': {'price': 0, 'icon': '🍽️', 'message': 'Bon appétit! Enjoy your meal!'},
            'Travel Booking': {'price': 500, 'icon': '✈️', 'message': 'Have an amazing journey!'},
            'Spa Treatment': {'price': 120, 'icon': '🧖', 'message': 'Relax and rejuvenate!'},
            'Consultation': {'price': 80, 'icon': '📋', 'message': 'We look forward to helping you!'}
        }
    
    def _initialize_llm(self):
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
                temperature=0.3,
                max_tokens=150,
            )
        except Exception as e:
            st.error(f"Failed to initialize LLM: {str(e)}")
            raise
    
    def handle_booking_intent(self, user_message, booking_data, awaiting_confirmation):
        if awaiting_confirmation:
            return self._handle_confirmation(user_message, booking_data)
        
        extracted_data = self._extract_booking_info(user_message, booking_data)
        validation_errors = self._validate_extracted_data(extracted_data, booking_data)
        
        if validation_errors:
            error_response = "⚠️ I found some issues:\n\n"
            for field, error in validation_errors.items():
                error_response += f"• **{field.replace('_', ' ').title()}**: {error}\n"
            error_response += f"\nPlease provide the correct {list(validation_errors.keys())[0].replace('_', ' ')}."
            return error_response, booking_data, False, False
        
        booking_data.update(extracted_data)
        
        # Auto-fill pricing when booking_type is selected
        if 'booking_type' in booking_data and 'pricing' not in booking_data:
            service_info = self.service_pricing.get(booking_data['booking_type'], {})
            price = service_info.get('price', 0)
            if price > 0:
                booking_data['pricing'] = f"${price}"
            else:
                booking_data['pricing'] = "Free"
        
        missing_fields = [field for field in self.required_fields 
                         if field not in booking_data or not booking_data[field]]
        
        if missing_fields:
            response = self._ask_for_missing_info(missing_fields, booking_data)
            return response, booking_data, False, False
        else:
            response = self._generate_confirmation_message(booking_data)
            return response, booking_data, True, False
    
    def _validate_extracted_data(self, extracted_data, existing_data):
        errors = {}
        
        if 'email' in extracted_data:
            email = extracted_data['email']
            if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', email):
                errors['email'] = f"'{email}' is not valid. Use format: name@example.com"
        
        if 'phone' in extracted_data:
            phone = re.sub(r'[\s\-\(\)\+]', '', extracted_data['phone'])
            if not phone.isdigit() or len(phone) < 10 or len(phone) > 15:
                errors['phone'] = f"'{extracted_data['phone']}' is not valid. Provide 10-15 digits"
        
        if 'date' in extracted_data:
            date_str = extracted_data['date']
            try:
                booking_date = datetime.strptime(date_str, '%Y-%m-%d')
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                
                if booking_date < today:
                    days_past = (today - booking_date).days
                    errors['date'] = f"'{date_str}' is {days_past} day(s) in the past. Choose a future date"
                
                max_future = today + timedelta(days=365)
                if booking_date > max_future:
                    errors['date'] = f"'{date_str}' is too far ahead. Book within the next year"
                    
            except ValueError:
                errors['date'] = f"'{date_str}' is invalid. Use YYYY-MM-DD (e.g., 2025-01-25)"
        
        if 'time' in extracted_data:
            time_str = extracted_data['time']
            try:
                # Fix: Ensure time is in HH:MM format
                if ':' in time_str:
                    parts = time_str.split(':')
                    hours = int(parts[0])
                    mins = int(parts[1])
                    
                    if hours < 0 or hours > 23:
                        errors['time'] = f"'{time_str}' has invalid hours. Use 00-23"
                    elif mins < 0 or mins > 59:
                        errors['time'] = f"'{time_str}' has invalid minutes. Use 00-59"
                    else:
                        # Reformat to ensure HH:MM
                        extracted_data['time'] = f"{hours:02d}:{mins:02d}"
                        
                        booking_time = datetime.strptime(extracted_data['time'], '%H:%M')
                        
                        if 'date' in extracted_data or 'date' in existing_data:
                            date_str = extracted_data.get('date') or existing_data.get('date')
                            try:
                                booking_date = datetime.strptime(date_str, '%Y-%m-%d')
                                today = datetime.now().date()
                                
                                if booking_date.date() == today:
                                    current_time = datetime.now().time()
                                    if booking_time.time() < current_time:
                                        errors['time'] = f"'{extracted_data['time']}' has passed. Choose a future time"
                            except:
                                pass
                else:
                    errors['time'] = f"'{time_str}' is invalid. Use HH:MM (e.g., 14:30)"
                        
            except (ValueError, IndexError):
                errors['time'] = f"'{time_str}' is invalid. Use HH:MM format (e.g., 14:30)"
        
        if 'name' in extracted_data:
            name = extracted_data['name'].strip()
            if len(name) < 2:
                errors['name'] = "Name is too short. Provide your full name"
            elif len(name) > 100:
                errors['name'] = "Name is too long"
        
        return errors
    
    def _extract_booking_info(self, user_message, existing_data):
        extracted = {}
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_message)
        if emails and 'email' not in existing_data:
            extracted['email'] = emails[0]
        
        phone_pattern = r'\b\d{10,15}\b'
        phones = re.findall(phone_pattern, user_message)
        if phones and 'phone' not in existing_data:
            extracted['phone'] = phones[0]
        
        date_pattern = r'\b\d{4}-\d{2}-\d{2}\b'
        dates = re.findall(date_pattern, user_message)
        if dates and 'date' not in existing_data:
            extracted['date'] = dates[0]
        
        # Improved time extraction - handle both H:MM and HH:MM
        time_pattern = r'\b\d{1,2}:\d{2}\b'
        times = re.findall(time_pattern, user_message)
        if times and 'time' not in existing_data:
            time_parts = times[0].split(':')
            extracted['time'] = f"{int(time_parts[0]):02d}:{time_parts[1]}"
        
        if 'name' not in existing_data and len(user_message.split()) <= 5:
            clean_msg = user_message.strip()
            if clean_msg and not any(char in clean_msg for char in ['@', '.com', ':', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
                booking_phrases = ['book', 'appointment', 'reservation', 'schedule', 'want', 'need', 'service']
                if not any(phrase in clean_msg.lower() for phrase in booking_phrases):
                    if len(clean_msg) < 50 and clean_msg.replace(' ', '').replace('-', '').isalpha():
                        extracted['name'] = clean_msg.title()
        
        if 'booking_type' not in existing_data:
            booking_type = self._extract_booking_type(user_message)
            if booking_type:
                extracted['booking_type'] = booking_type
        
        return extracted
    
    def _extract_booking_type(self, text):
        text_lower = text.lower().strip()
        
        service_keywords = {
            'Doctor Appointment': ['doctor', 'medical', 'physician', 'healthcare', 'clinic', 'checkup', 'consultation', 'appointment'],
            'Salon Service': ['salon', 'haircut', 'hair', 'beauty', 'manicure', 'pedicure', 'styling'],
            'Hotel Reservation': ['hotel', 'room', 'accommodation', 'stay', 'resort', 'lodge'],
            'Event Booking': ['event', 'party', 'celebration', 'wedding', 'conference', 'meeting'],
            'Fitness Class': ['fitness', 'gym', 'workout', 'exercise', 'yoga', 'training', 'class'],
            'Restaurant Reservation': ['restaurant', 'dining', 'dinner', 'lunch', 'table', 'food', 'eat'],
            'Travel Booking': ['travel', 'trip', 'tour', 'vacation', 'flight', 'ticket', 'journey'],
            'Spa Treatment': ['spa', 'massage', 'treatment', 'therapy', 'relaxation', 'wellness'],
            'Consultation': ['consult', 'advice', 'guidance', 'counseling']
        }
        
        for service_type, keywords in service_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return service_type
        
        return self._extract_with_llm(text, 'booking_type')
    
    def _extract_with_llm(self, text, field):
        try:
            if field == 'booking_type':
                prompt = f"""Extract service type from: "{text}"
Available: {', '.join(self.service_pricing.keys())}
Reply with ONLY the exact service name or "NOT_FOUND".
Service:"""
            else:
                prompt = f"""Extract {field} from: "{text}"
Reply ONLY the value or "NOT_FOUND".
{field}:"""
            
            messages = [
                SystemMessage(content="You are a data extraction assistant."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            result = response.content.strip().strip('"').strip("'")
            
            if result and result != 'NOT_FOUND' and len(result) < 100:
                return result
            return None
        except:
            return None
    
    def _ask_for_missing_info(self, missing_fields, booking_data):
        if len(missing_fields) == len(self.required_fields):
            return "Great! Let's make a booking. What's your name?"
        
        field = missing_fields[0]
        
        # Skip pricing field (auto-filled)
        if field == 'pricing':
            return self._ask_for_missing_info([f for f in missing_fields if f != 'pricing'], booking_data)
        
        collected = [f for f in self.required_fields if f in booking_data and booking_data[f] and f != 'pricing']
        
        if collected:
            summary = "✅ **Information collected:**\n"
            for f in collected:
                field_name = f.replace('_', ' ').title()
                value = booking_data[f]
                
                emoji_map = {
                    'name': '👤',
                    'email': '📧',
                    'phone': '📱',
                    'booking_type': '🎯',
                    'date': '📅',
                    'time': '⏰',
                    'pricing': '💰'
                }
                emoji = emoji_map.get(f, '•')
                summary += f"{emoji} {field_name}: **{value}**\n"
            summary += "\n"
        else:
            summary = ""
        
        if field == 'name':
            question = "What's your name?"
        elif field == 'email':
            question = "What's your email address?\n📧 *Example: john.doe@gmail.com*"
        elif field == 'phone':
            question = "What's your phone number?\n📱 *Example: 9876543210*"
        elif field == 'booking_type':
            question = "What service would you like?\n\n**Available Services:**\n"
            for service, info in self.service_pricing.items():
                price_str = f"${info['price']}" if info['price'] > 0 else "Free"
                question += f"{info['icon']} **{service}** - {price_str}\n"
            question += "\n💡 *Type the service name (e.g., 'Doctor', 'Salon')*"
        elif field == 'date':
            today = datetime.now()
            tomorrow = today + timedelta(days=1)
            question = f"What date?\n\n📅 **Format:** YYYY-MM-DD\n"
            question += f"**Quick picks:**\n• Today: `{today.strftime('%Y-%m-%d')}`\n• Tomorrow: `{tomorrow.strftime('%Y-%m-%d')}`\n"
            
            with st.sidebar:
                st.markdown("### 📅 Date Picker")
                selected_date = st.date_input(
                    "Choose date",
                    min_value=today.date(),
                    max_value=(today + timedelta(days=365)).date(),
                    value=today.date(),
                    key="booking_date_picker"
                )
                if st.button("Use This Date", key="use_date"):
                    st.session_state.suggested_date = selected_date.strftime('%Y-%m-%d')
                    st.success(f"✓ {selected_date.strftime('%Y-%m-%d')}")
        elif field == 'time':
            question = "What time?\n\n⏰ **Format:** HH:MM (24-hour)\n"
            question += "**Examples:** `09:00`, `14:30`, `18:00`\n"
            
            with st.sidebar:
                st.markdown("### ⏰ Time Picker")
                selected_time = st.time_input(
                    "Choose time",
                    value=datetime.now().replace(hour=9, minute=0),
                    key="booking_time_picker"
                )
                if st.button("Use This Time", key="use_time"):
                    st.session_state.suggested_time = selected_time.strftime('%H:%M')
                    st.success(f"✓ {selected_time.strftime('%H:%M')}")
        else:
            question = f"Please provide {field.replace('_', ' ')}."
        
        return summary + question
    
    def _generate_confirmation_message(self, booking_data):
        service_info = self.service_pricing.get(booking_data.get('booking_type', ''), {})
        icon = service_info.get('icon', '🎯')
        
        message = f"{icon} **Perfect! Confirm your booking:**\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"👤 **Name:** {booking_data.get('name')}\n"
        message += f"📧 **Email:** {booking_data.get('email')}\n"
        message += f"📱 **Phone:** {booking_data.get('phone')}\n"
        message += f"{icon} **Service:** {booking_data.get('booking_type')}\n"
        message += f"💰 **Price:** {booking_data.get('pricing')}\n"
        message += f"📅 **Date:** {booking_data.get('date')}\n"
        message += f"⏰ **Time:** {booking_data.get('time')}\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += "✅ Reply **'yes'** to confirm\n"
        message += "❌ Reply **'no'** to restart"
        
        return message
    
    def _handle_confirmation(self, user_message, booking_data):
        user_lower = user_message.lower().strip()
        
        if any(word in user_lower for word in ['yes', 'confirm', 'correct', 'ok', 'okay', 'sure', 'yep', 'yeah']):
            success, result = self._save_booking(booking_data)
            
            if success:
                booking_id = result
                email_sent = send_booking_email(booking_data, booking_id)
                
                # Get service-specific message
                service_type = booking_data.get('booking_type', '')
                service_info = self.service_pricing.get(service_type, {})
                icon = service_info.get('icon', '🎯')
                special_msg = service_info.get('message', 'Thank you for booking!')
                
                response = f"🎉 **BOOKING CONFIRMED!**\n\n"
                response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                response += f"📋 **Booking ID:** `{booking_id}`\n"
                response += f"{icon} **Service:** {service_type}\n"
                response += f"📅 **Date:** {booking_data.get('date')} at {booking_data.get('time')}\n"
                response += f"💰 **Total:** {booking_data.get('pricing')}\n\n"
                response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                
                if email_sent:
                    response += f"✅ **Confirmation email sent to:**\n   {booking_data.get('email')}\n\n"
                else:
                    response += f"⚠️ *Email could not be sent, but booking is saved*\n\n"
                
                response += f"💫 **{special_msg}**\n\n"
                response += "🌟 *Your booking is confirmed. You're all set! No hassle, everything handled.*\n\n"
                response += "Need anything else? Just ask! 😊"
                
                return response, {}, False, True
            else:
                return f"❌ Error: {result}\n\nPlease try again.", {}, False, True
        
        elif any(word in user_lower for word in ['no', 'cancel', 'stop', 'restart', 'nope']):
            return "No problem! Let's start fresh. What service would you like to book?", {}, False, False
        
        else:
            return "Please reply **'yes'** to confirm or **'no'** to restart.", booking_data, True, False
    
    def _save_booking(self, booking_data):
        try:
            for field in ['name', 'email', 'phone', 'booking_type', 'date', 'time']:
                if field not in booking_data or not booking_data[field]:
                    return False, f"Missing: {field}"
            
            if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', booking_data['email']):
                return False, "Invalid email"
            
            try:
                datetime.strptime(booking_data['date'], '%Y-%m-%d')
            except ValueError:
                return False, "Invalid date"
            
            booking_id = self.db.create_booking(
                name=booking_data['name'],
                email=booking_data['email'],
                phone=booking_data['phone'],
                booking_type=booking_data['booking_type'],
                date=booking_data['date'],
                time=booking_data['time']
            )
            
            return True, booking_id
        except Exception as e:
            return False, str(e)