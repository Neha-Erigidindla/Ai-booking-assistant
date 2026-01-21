import sqlite3
import os
from datetime import datetime
from pathlib import Path


class BookingDatabase:
    """Database handler for bookings and customers"""
    
    def __init__(self, db_path="db/bookings.db"):
        """Initialize database connection"""
        self.db_path = db_path
        
        # Ensure db directory exists
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._create_tables()
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Create customers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    phone TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create bookings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    booking_type TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT DEFAULT 'confirmed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
                )
            """)
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error creating tables: {str(e)}")
        finally:
            conn.close()
    
    def create_booking(self, name, email, phone, booking_type, date, time, status='confirmed'):
        """Create a new booking"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if customer exists
            cursor.execute("SELECT customer_id FROM customers WHERE email = ?", (email,))
            customer = cursor.fetchone()
            
            if customer:
                customer_id = customer['customer_id']
                
                # Update customer info if needed
                cursor.execute("""
                    UPDATE customers 
                    SET name = ?, phone = ?
                    WHERE customer_id = ?
                """, (name, phone, customer_id))
            else:
                # Create new customer
                cursor.execute("""
                    INSERT INTO customers (name, email, phone)
                    VALUES (?, ?, ?)
                """, (name, email, phone))
                customer_id = cursor.lastrowid
            
            # Create booking
            cursor.execute("""
                INSERT INTO bookings (customer_id, booking_type, date, time, status)
                VALUES (?, ?, ?, ?, ?)
            """, (customer_id, booking_type, date, time, status))
            
            booking_id = cursor.lastrowid
            
            conn.commit()
            return booking_id
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error creating booking: {str(e)}")
        finally:
            conn.close()
    
    def get_all_bookings(self):
        """Get all bookings with customer information"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    b.id,
                    c.name,
                    c.email,
                    c.phone,
                    b.booking_type,
                    b.date,
                    b.time,
                    b.status,
                    b.created_at
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                ORDER BY b.created_at DESC
            """)
            
            bookings = cursor.fetchall()
            
            # Convert to list of dictionaries
            result = []
            for booking in bookings:
                result.append({
                    'id': booking['id'],
                    'name': booking['name'],
                    'email': booking['email'],
                    'phone': booking['phone'],
                    'booking_type': booking['booking_type'],
                    'date': booking['date'],
                    'time': booking['time'],
                    'status': booking['status'],
                    'created_at': booking['created_at']
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Error fetching bookings: {str(e)}")
        finally:
            conn.close()
    
    def get_booking_by_id(self, booking_id):
        """Get a specific booking by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    b.id,
                    c.name,
                    c.email,
                    c.phone,
                    b.booking_type,
                    b.date,
                    b.time,
                    b.status,
                    b.created_at
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                WHERE b.id = ?
            """, (booking_id,))
            
            booking = cursor.fetchone()
            
            if booking:
                return {
                    'id': booking['id'],
                    'name': booking['name'],
                    'email': booking['email'],
                    'phone': booking['phone'],
                    'booking_type': booking['booking_type'],
                    'date': booking['date'],
                    'time': booking['time'],
                    'status': booking['status'],
                    'created_at': booking['created_at']
                }
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching booking: {str(e)}")
        finally:
            conn.close()
    
    def search_bookings(self, search_term):
        """Search bookings by name, email, or date"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            search_pattern = f"%{search_term}%"
            
            cursor.execute("""
                SELECT 
                    b.id,
                    c.name,
                    c.email,
                    c.phone,
                    b.booking_type,
                    b.date,
                    b.time,
                    b.status,
                    b.created_at
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                WHERE c.name LIKE ? OR c.email LIKE ? OR b.date LIKE ?
                ORDER BY b.created_at DESC
            """, (search_pattern, search_pattern, search_pattern))
            
            bookings = cursor.fetchall()
            
            result = []
            for booking in bookings:
                result.append({
                    'id': booking['id'],
                    'name': booking['name'],
                    'email': booking['email'],
                    'phone': booking['phone'],
                    'booking_type': booking['booking_type'],
                    'date': booking['date'],
                    'time': booking['time'],
                    'status': booking['status'],
                    'created_at': booking['created_at']
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Error searching bookings: {str(e)}")
        finally:
            conn.close()
    
    def update_booking_status(self, booking_id, status):
        """Update booking status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE bookings
                SET status = ?
                WHERE id = ?
            """, (status, booking_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error updating booking status: {str(e)}")
        finally:
            conn.close()
    
    def delete_booking(self, booking_id):
        """Delete a booking"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error deleting booking: {str(e)}")
        finally:
            conn.close()
    
    def get_bookings_by_date(self, date):
        """Get all bookings for a specific date"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    b.id,
                    c.name,
                    c.email,
                    c.phone,
                    b.booking_type,
                    b.date,
                    b.time,
                    b.status,
                    b.created_at
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                WHERE b.date = ?
                ORDER BY b.time
            """, (date,))
            
            bookings = cursor.fetchall()
            
            result = []
            for booking in bookings:
                result.append({
                    'id': booking['id'],
                    'name': booking['name'],
                    'email': booking['email'],
                    'phone': booking['phone'],
                    'booking_type': booking['booking_type'],
                    'date': booking['date'],
                    'time': booking['time'],
                    'status': booking['status'],
                    'created_at': booking['created_at']
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Error fetching bookings by date: {str(e)}")
        finally:
            conn.close()
    
    def get_customer_bookings(self, email):
        """Get all bookings for a specific customer"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    b.id,
                    c.name,
                    c.email,
                    c.phone,
                    b.booking_type,
                    b.date,
                    b.time,
                    b.status,
                    b.created_at
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                WHERE c.email = ?
                ORDER BY b.date DESC, b.time DESC
            """, (email,))
            
            bookings = cursor.fetchall()
            
            result = []
            for booking in bookings:
                result.append({
                    'id': booking['id'],
                    'name': booking['name'],
                    'email': booking['email'],
                    'phone': booking['phone'],
                    'booking_type': booking['booking_type'],
                    'date': booking['date'],
                    'time': booking['time'],
                    'status': booking['status'],
                    'created_at': booking['created_at']
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Error fetching customer bookings: {str(e)}")
        finally:
            conn.close()