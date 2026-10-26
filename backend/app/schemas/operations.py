from datetime import date, time

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
