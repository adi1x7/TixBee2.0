from datetime import date, datetime, time

from pydantic import BaseModel, Field


class SlotManagementOut(BaseModel):
    id: str
    attraction_id: str
    attraction_name: str
    visit_date: date
    start_time: time
    end_time: time
    capacity: int
    remaining_capacity: int
    is_active: bool


class SlotUpdateIn(BaseModel):
    capacity: int | None = Field(default=None, ge=1, le=500)
    is_active: bool | None = None


class CustomerDirectoryOut(BaseModel):
    id: str
    full_name: str
    email: str
    is_active: bool
    booking_count: int
    confirmed_booking_count: int
    latest_booking_at: datetime | None = None


class OperationActivityOut(BaseModel):
    booking_reference: str
    ticket_code: str | None = None
    ticket_status: str | None = None
    attraction_name: str
    city: str
    visit_date: date
    start_time: time
    customer_name: str | None = None
    total_amount: int
    created_at: datetime
    redeemed_at: datetime | None = None
