import io

import jwt
import qrcode
import qrcode.image.svg
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import current_user, staff_user
from app.models import Attraction, Booking, BookingItem, Payment, Ticket, TimeSlot, User
from app.models.domain import utcnow
from app.schemas.tickets import CancellationOut, MyBookingOut, TicketVerificationOut
from app.services.email import send_cancellation_confirmation

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
        result.append(MyBookingOut(id=booking.id, reference=booking.reference, status=booking.status, attraction_name=attraction.name, city=attraction.city, visit_date=slot.visit_date, start_time=slot.start_time, total_amount=booking.total_amount, ticket_code=ticket.ticket_code if ticket else None, ticket_status=ticket.status if ticket else None, cancellation_deadline=booking.cancellation_deadline))
    return result


@router.get("/tickets/{ticket_code}/qr")
def ticket_qr(ticket_code: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    ticket, booking, _, _ = _ticket_row(ticket_code, db)
    if booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    image = qrcode.make(ticket.qr_token, image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=2)
    stream = io.BytesIO(); image.save(stream)
    return Response(stream.getvalue(), media_type="image/svg+xml", headers={"Cache-Control": "private, no-store"})


@router.post("/bookings/{booking_id}/cancel-confirmed", response_model=CancellationOut)
def cancel_confirmed_booking(booking_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    candidate = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.user_id == user.id))
    if not candidate:
        raise HTTPException(status_code=404, detail="Booking not found.")
    slot = db.scalar(select(TimeSlot).where(TimeSlot.id == candidate.slot_id).with_for_update())
    booking = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.user_id == user.id).with_for_update())
    if not booking or not slot:
        raise HTTPException(status_code=409, detail="This booking is no longer available.")
    if booking.status != "CONFIRMED":
        raise HTTPException(status_code=409, detail="Only confirmed bookings can be cancelled.")
    if not booking.cancellation_deadline or utcnow() >= booking.cancellation_deadline:
        raise HTTPException(status_code=409, detail="Cancellations close 24 hours before the visit start time.")
    ticket = db.scalar(select(Ticket).where(Ticket.booking_id == booking.id).with_for_update())
    payment = db.scalar(select(Payment).where(Payment.booking_id == booking.id).with_for_update())
    if not ticket or ticket.status != "ISSUED" or not payment:
        raise HTTPException(status_code=409, detail="This ticket is not eligible for cancellation.")
    items = list(db.scalars(select(BookingItem).where(BookingItem.booking_id == booking.id)))
    refund_amount = booking.total_amount // 2
    slot.remaining_capacity = min(slot.capacity, slot.remaining_capacity + sum(item.quantity for item in items))
    booking.status = "CANCELLED"
    ticket.status = "CANCELLED"
    payment.status = "REFUND_PENDING"
    payment.refund_amount = refund_amount
    payment.refund_status = "REFUND_PENDING"
    payment.refunded_at = utcnow()
    db.commit()
    delivery = send_cancellation_confirmation(
        recipient=user.email,
        visitor_name=user.full_name,
        attraction_name=db.scalar(select(Attraction.name).where(Attraction.id == booking.attraction_id)),
        visit_date=slot.visit_date.strftime("%d %B %Y"),
        visit_slot=f"{slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}",
        ticket_code=ticket.ticket_code,
        refund_amount=refund_amount,
    )
    return CancellationOut(booking_reference=booking.reference, refund_amount=refund_amount, refund_status=payment.refund_status, email_delivery_status=delivery)


@router.get("/tickets/{ticket_code}/verify", response_model=TicketVerificationOut)
def verify_ticket(ticket_code: str, db: Session = Depends(get_db), user: User = Depends(staff_user)):
    ticket, booking, attraction, slot = _ticket_row(ticket_code, db)
    if user.role == "staff" and user.assigned_attraction_id != attraction.id:
        raise HTTPException(status_code=403, detail="This ticket belongs to a different visit site.")
    try:
        payload = jwt.decode(
            ticket.qr_token,
            get_settings().ticket_signing_key,
            algorithms=[get_settings().jwt_algorithm],
            options={"require": ["booking_id", "ticket", "exp"]},
        )
        if payload.get("booking_id") != booking.id or payload.get("ticket") != booking.reference:
            raise ValueError("Ticket payload does not match")
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Ticket signature is invalid.") from exc
    return TicketVerificationOut(valid=ticket.status == "ISSUED", ticket_code=ticket.ticket_code, status=ticket.status, booking_reference=booking.reference, attraction_name=attraction.name, visit_date=slot.visit_date, start_time=slot.start_time)
