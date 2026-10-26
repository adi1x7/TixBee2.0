from datetime import date, time
from pydantic import BaseModel


class MyBookingOut(BaseModel):
    id: str
    reference: str
    status: str
    attraction_name: str
    city: str
    visit_date: date
    start_time: time
    total_amount: int
    ticket_code: str | None = None
    ticket_status: str | None = None


class TicketVerificationOut(BaseModel):
    valid: bool
    ticket_code: str
    status: str
    booking_reference: str
    attraction_name: str
    visit_date: date
    start_time: time
