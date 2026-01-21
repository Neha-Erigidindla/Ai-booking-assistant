from datetime import datetime
from typing import Optional

class Customer:
    def __init__(self, customer_id: Optional[int], name: str, email: str, phone: str):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.phone = phone

class Booking:
    def __init__(
        self,
        id: Optional[int],
        customer_id: int,
        booking_type: str,
        date: str,
        time: str,
        status: str = "confirmed",
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.customer_id = customer_id
        self.booking_type = booking_type
        self.date = date
        self.time = time
        self.status = status
        self.created_at = created_at or datetime.now()