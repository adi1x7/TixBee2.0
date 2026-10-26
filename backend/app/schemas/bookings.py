from datetime import datetime
from pydantic import BaseModel, Field


class BookingQuantityIn(BaseModel):
    ticket_type_code: str = Field(pattern="^(adult|student|child)$")
    quantity: int = Field(ge=0, le=10)


class CreateBookingIn(BaseModel):
    attraction_id: str
    slot_id: str
    quantities: list[BookingQuantityIn] = Field(min_length=1, max_length=3)


class BookingItemOut(BaseModel):
    ticket_type_code: str
    quantity: int
    unit_price: int


class BookingOut(BaseModel):
    id: str
    reference: str
    status: str
    total_amount: int
    hold_expires_at: datetime | None
    items: list[BookingItemOut]


class DemoPayOut(BaseModel):
    booking: BookingOut
    ticket_code: str
    ticket_status: str
    email_delivery_status: str
