from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class TicketTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    label: str
    price: int
    eligibility_note: str | None = None


class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    visit_date: date
    start_time: time
    end_time: time
    remaining_capacity: int


class FaqOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    question: str
    answer: str


class AttractionCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    slug: str
    name: str
    city: str
    category: str
    short_description: str
    image_url: str | None = None
    starting_price: int


class AttractionDetailOut(AttractionCardOut):
    description: str
    opening_hours: str
    visitor_rules: list[str] = Field(default_factory=list)
    facilities: list[str] = Field(default_factory=list)
    directions_url: str | None = None
    ticket_types: list[TicketTypeOut] = Field(default_factory=list)
    faqs: list[FaqOut] = Field(default_factory=list)
