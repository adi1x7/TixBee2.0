import io

import jwt
import qrcode
import qrcode.image.svg
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import current_user
from app.models import Attraction, Booking, Ticket, TimeSlot, User
from app.schemas.tickets import MyBookingOut, TicketVerificationOut

router = APIRouter(tags=["tickets"])


def _ticket_row(ticket_code: str, db: Session) -> tuple[Ticket, Booking, Attraction, TimeSlot]:
    ticket = db.scalar(select(Ticket).where(Ticket.ticket_code == ticket_code))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    booking = db.scalar(select(Booking).where(Booking.id == ticket.booking_id))
    slot = db.scalar(select(TimeSlot).where(TimeSlot.id == booking.slot_id))
    attraction = db.scalar(select(Attraction).where(Attraction.id == booking.attraction_id))
    return ticket, booking, attraction, slot


@router.get("/me/bookings", response_model=list[MyBookingOut])
def my_bookings(db: Session = Depends(get_db), user: User = Depends(current_user)):
    bookings = list(db.scalars(select(Booking).where(Booking.user_id == user.id).order_by(Booking.created_at.desc())))
    result = []
    for booking in bookings:
        slot = db.scalar(select(TimeSlot).where(TimeSlot.id == booking.slot_id))
        attraction = db.scalar(select(Attraction).where(Attraction.id == booking.attraction_id))
        ticket = db.scalar(select(Ticket).where(Ticket.booking_id == booking.id))
        result.append(MyBookingOut(id=booking.id, reference=booking.reference, status=booking.status, attraction_name=attraction.name, city=attraction.city, visit_date=slot.visit_date, start_time=slot.start_time, total_amount=booking.total_amount, ticket_code=ticket.ticket_code if ticket else None, ticket_status=ticket.status if ticket else None))
    return result


@router.get("/tickets/{ticket_code}/qr")
def ticket_qr(ticket_code: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    ticket, booking, _, _ = _ticket_row(ticket_code, db)
    if booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    image = qrcode.make(ticket.qr_token, image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=2)
    stream = io.BytesIO(); image.save(stream)
    return Response(stream.getvalue(), media_type="image/svg+xml", headers={"Cache-Control": "private, no-store"})


@router.get("/tickets/{ticket_code}/verify", response_model=TicketVerificationOut)
def verify_ticket(ticket_code: str, db: Session = Depends(get_db)):
    ticket, booking, attraction, slot = _ticket_row(ticket_code, db)
    try:
        payload = jwt.decode(ticket.qr_token, get_settings().jwt_secret_key, algorithms=[get_settings().jwt_algorithm])
        if payload.get("booking_id") != booking.id or payload.get("ticket") != booking.reference:
            raise ValueError("Ticket payload does not match")
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Ticket signature is invalid.") from exc
    return TicketVerificationOut(valid=ticket.status == "ISSUED", ticket_code=ticket.ticket_code, status=ticket.status, booking_reference=booking.reference, attraction_name=attraction.name, visit_date=slot.visit_date, start_time=slot.start_time)
