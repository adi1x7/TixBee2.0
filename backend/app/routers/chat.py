from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chat import ChatIn, ChatOut
from app.services.concierge import answer_concierge

router = APIRouter(prefix="/chat", tags=["concierge"])


@router.post("/messages", response_model=ChatOut)
def send_message(payload: ChatIn, db: Session = Depends(get_db)):
    answer, state, model = answer_concierge(db, payload.session_id, payload.message, payload.attraction_id)
    return ChatOut(session_id=payload.session_id, answer=answer, status=state, model=model)
