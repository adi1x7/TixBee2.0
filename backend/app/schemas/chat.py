from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    session_id: str = Field(min_length=12, max_length=80)
    message: str = Field(min_length=1, max_length=1000)
    attraction_id: str | None = None


class ChatOut(BaseModel):
    session_id: str
    answer: str | None
    status: str
    model: str | None = None
