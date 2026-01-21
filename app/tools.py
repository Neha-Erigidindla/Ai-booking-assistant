import os
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_booking_email(booking_data, booking_id):
    """
    Send booking confirmation email
    
    Args:
        booking_data: Dictionary containing booking information
        booking_id: The booking ID from database
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get email credentials from Streamlit secrets or environment
        if hasattr(st, 'secrets'):
            smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = st.secrets.get("SMTP_PORT", 587)
            sender_email = st.secrets.get("SENDER_EMAIL", "")
            sender_password = st.secrets.get("SENDER_PASSWORD", "")
        else:
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            sender_email = os.getenv("SENDER_EMAIL", "")
            sender_password = os.getenv("SENDER_PASSWORD", "")
        
        # Check if email credentials are configured
        if not sender_email or not sender_password:
            print("Email credentials not configured. Skipping email send.")
            return False
        
        # Recipient email
        recipient_email = booking_data.get('email')
        
        if not recipient_email:
            print("No recipient email found")
            return False
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Booking Confirmation - ID: {booking_id}"
        message["From"] = sender_email
        message["To"] = recipient_email
        
        # Create email body
        text_content = f"""
Booking Confirmation

Dear {booking_data.get('name', 'Customer')},

Thank you for your booking! Here are your booking details:

Booking ID: {booking_id}
Name: {booking_data.get('name', 'N/A')}
Email: {booking_data.get('email', 'N/A')}
Phone: {booking_data.get('phone', 'N/A')}
Service Type: {booking_data.get('booking_type', 'N/A')}
Date: {booking_data.get('date', 'N/A')}
Time: {booking_data.get('time', 'N/A')}

If you need to make any changes or have questions, please contact us.

Best regards,
AI Booking Assistant Team
"""
        
        html_content = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
      <h2 style="color: #4CAF50; text-align: center;">✅ Booking Confirmation</h2>
      
      <p>Dear <strong>{booking_data.get('name', 'Customer')}</strong>,</p>
      
      <p>Thank you for your booking! Here are your booking details:</p>
      
      <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 8px; font-weight: bold;">Booking ID:</td>
            <td style="padding: 8px;">{booking_id}</td>
          </tr>
          <tr style="background-color: #fff;">
            <td style="padding: 8px; font-weight: bold;">Name:</td>
            <td style="padding: 8px;">{booking_data.get('name', 'N/A')}</td>
          </tr>
          <tr>
            <td style="padding: 8px; font-weight: bold;">Email:</td>
            <td style="padding: 8px;">{booking_data.get('email', 'N/A')}</td>
          </tr>
          <tr style="background-color: #fff;">
            <td style="padding: 8px; font-weight: bold;">Phone:</td>
            <td style="padding: 8px;">{booking_data.get('phone', 'N/A')}</td>
          </tr>
          <tr>
            <td style="padding: 8px; font-weight: bold;">Service Type:</td>
            <td style="padding: 8px;">{booking_data.get('booking_type', 'N/A')}</td>
          </tr>
          <tr style="background-color: #fff;">
            <td style="padding: 8px; font-weight: bold;">Date:</td>
            <td style="padding: 8px;">{booking_data.get('date', 'N/A')}</td>
          </tr>
          <tr>
            <td style="padding: 8px; font-weight: bold;">Time:</td>
            <td style="padding: 8px;">{booking_data.get('time', 'N/A')}</td>
          </tr>
        </table>
      </div>
      
      <p>If you need to make any changes or have questions, please contact us.</p>
      
      <p style="margin-top: 30px;">Best regards,<br>
      <strong>AI Booking Assistant Team</strong></p>
      
      <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
      
      <p style="font-size: 12px; color: #666; text-align: center;">
        This is an automated confirmation email. Please do not reply to this email.
      </p>
    </div>
  </body>
</html>
"""
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        
        print(f"Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def validate_email_format(email):
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone_format(phone):
    """
    Validate phone format (basic validation)
    
    Args:
        phone: Phone string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    # Check if it contains only digits and has reasonable length
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def validate_date_format(date_str):
    """
    Validate date format (YYYY-MM-DD)
    
    Args:
        date_str: Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    from datetime import datetime
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_time_format(time_str):
    """
    Validate time format (HH:MM)
    
    Args:
        time_str: Time string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    from datetime import datetime
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False