from datetime import date, datetime, time, timedelta, timezone
from io import BytesIO
from urllib.parse import urlencode
from uuid import uuid4
from zoneinfo import ZoneInfo

import jwt
import qrcode
import qrcode.image.svg
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import current_user
from app.models import Attraction, Booking, BookingItem, Payment, Ticket, TicketType, TimeSlot, User
from app.models.domain import utcnow
from app.schemas.bookings import BookingItemOut, BookingOut, CreateBookingIn, DemoPayOut
from app.services.email import send_ticket_confirmation

router = APIRouter(prefix="/bookings", tags=["bookings"])


def booking_out(booking: Booking, items: list[BookingItem]) -> BookingOut:
    return BookingOut(id=booking.id, reference=booking.reference, status=booking.status, total_amount=booking.total_amount,
                      hold_expires_at=booking.hold_expires_at,
                      items=[BookingItemOut(ticket_type_code=item.ticket_type_code, quantity=item.quantity, unit_price=item.unit_price) for item in items])


def expire_holds_for_slot(db: Session, slot: TimeSlot) -> None:
    expired = list(db.scalars(select(Booking).where(Booking.slot_id == slot.id, Booking.status == "HOLD", Booking.hold_expires_at < utcnow()).with_for_update()))
    for booking in expired:
        held_items = list(db.scalars(select(BookingItem).where(BookingItem.booking_id == booking.id)))
        slot.remaining_capacity += sum(item.quantity for item in held_items)
        booking.status = "EXPIRED"


def lock_owned_booking_and_slot(db: Session, booking_id: str, user_id: str) -> tuple[Booking, TimeSlot]:
    """Lock slot before booking everywhere to keep concurrent operations deadlock-safe."""
    candidate = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id))
    if not candidate:
        raise HTTPException(status_code=404, detail="Booking not found.")
    slot = db.scalar(select(TimeSlot).where(TimeSlot.id == candidate.slot_id).with_for_update())
    booking = db.scalar(
        select(Booking)
        .where(Booking.id == booking_id, Booking.user_id == user_id)
        .with_for_update()
    )
    if not booking or not slot:
        raise HTTPException(status_code=409, detail="The reservation is no longer available.")
    return booking, slot


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(payload: CreateBookingIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    quantities = {item.ticket_type_code: item.quantity for item in payload.quantities if item.quantity > 0}
    if not quantities:
        raise HTTPException(status_code=422, detail="Choose at least one ticket.")
    if len(quantities) != len([item for item in payload.quantities if item.quantity > 0]):
        raise HTTPException(status_code=422, detail="Each ticket type can be selected once.")
    total_tickets = sum(quantities.values())
    settings = get_settings()
    if total_tickets > settings.max_tickets_per_booking:
        raise HTTPException(status_code=422, detail=f"A booking can contain at most {settings.max_tickets_per_booking} tickets.")
    active_holds = db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.user_id == user.id,
            Booking.status == "HOLD",
            Booking.hold_expires_at >= utcnow(),
        )
    ) or 0
    if active_holds >= settings.max_active_holds_per_user:
        raise HTTPException(status_code=429, detail="You already have three active reservations. Complete or cancel one before starting another.")
    slot = db.scalar(select(TimeSlot).where(TimeSlot.id == payload.slot_id, TimeSlot.attraction_id == payload.attraction_id, TimeSlot.is_active.is_(True), TimeSlot.visit_date >= date.today()).with_for_update())
    if not slot:
        raise HTTPException(status_code=404, detail="That visit time is unavailable.")
    expire_holds_for_slot(db, slot)
    if slot.remaining_capacity < total_tickets:
        raise HTTPException(status_code=409, detail="Not enough places remain for that visit time.")
    ticket_types = list(db.scalars(select(TicketType).where(TicketType.attraction_id == payload.attraction_id, TicketType.is_active.is_(True))))
    prices = {ticket_type.code: ticket_type.price for ticket_type in ticket_types}
    if any(code not in prices for code in quantities):
        raise HTTPException(status_code=422, detail="One or more ticket types are unavailable.")
    items = [BookingItem(ticket_type_code=code, quantity=quantity, unit_price=prices[code]) for code, quantity in quantities.items()]
    total = sum(item.quantity * item.unit_price for item in items)
    booking = Booking(reference=f"TB-{uuid4().hex[:10].upper()}", user_id=user.id, attraction_id=payload.attraction_id, slot_id=slot.id,
                      status="HOLD", hold_expires_at=utcnow() + timedelta(minutes=settings.booking_hold_minutes), total_amount=total,
                      price_snapshot={"currency": "INR", "items": [{"type": item.ticket_type_code, "quantity": item.quantity, "unit_price": item.unit_price} for item in items]})
    db.add(booking); db.flush()
    for item in items:
        item.booking_id = booking.id
        db.add(item)
    slot.remaining_capacity -= total_tickets
    db.commit(); db.refresh(booking)
    return booking_out(booking, items)


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    booking = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.user_id == user.id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    items = list(db.scalars(select(BookingItem).where(BookingItem.booking_id == booking.id)))
    return booking_out(booking, items)


@router.get("/{booking_id}/upi-qr")
def upi_payment_qr(booking_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Generate an amount-specific UPI QR for the current account's active hold."""
    booking = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.user_id == user.id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.status != "HOLD" or not booking.hold_expires_at or booking.hold_expires_at < utcnow():
        raise HTTPException(status_code=409, detail="This payment window is no longer active.")
    settings = get_settings()
    upi_uri = "upi://pay?" + urlencode({
        "pa": settings.upi_payee_id,
        "pn": settings.upi_payee_name,
        "am": f"{booking.total_amount:.2f}",
        "cu": "INR",
        "tn": f"TixBee {booking.reference}",
    })
    image = qrcode.make(upi_uri, image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=2)
    stream = BytesIO()
    image.save(stream)
    return Response(stream.getvalue(), media_type="image/svg+xml", headers={"Cache-Control": "private, no-store"})


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_held_booking(booking_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Cancel an unpaid reservation and return its held capacity exactly once.

    Confirmed tickets intentionally cannot be cancelled in this local demo because
    a refund workflow is not part of the implemented payment simulator.
    """
    booking, slot = lock_owned_booking_and_slot(db, booking_id, user.id)
    if booking.status != "HOLD":
        raise HTTPException(
            status_code=409,
            detail="Only an unpaid reservation can be cancelled in this demo.",
        )

    items = list(db.scalars(select(BookingItem).where(BookingItem.booking_id == booking.id)))
    slot.remaining_capacity = min(slot.capacity, slot.remaining_capacity + sum(item.quantity for item in items))
    booking.status = "CANCELLED"
    booking.hold_expires_at = None
    db.commit()
    db.refresh(booking)
    return booking_out(booking, items)


@router.post("/{booking_id}/demo-pay", response_model=DemoPayOut)
def demo_pay(booking_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Local-only payment simulator. Production confirmation comes from a verified provider webhook."""
    booking, slot = lock_owned_booking_and_slot(db, booking_id, user.id)
    if booking.status == "HOLD" and booking.hold_expires_at and booking.hold_expires_at < utcnow():
        items = list(db.scalars(select(BookingItem).where(BookingItem.booking_id == booking.id)))
        if slot:
            slot.remaining_capacity = min(slot.capacity, slot.remaining_capacity + sum(item.quantity for item in items))
        booking.status = "EXPIRED"; booking.hold_expires_at = None; db.commit()
        raise HTTPException(status_code=409, detail="This reservation expired. Please choose a new time.")
    if booking.status not in {"HOLD", "CONFIRMED"}:
        raise HTTPException(status_code=409, detail="This booking cannot be paid.")
    ticket = db.scalar(select(Ticket).where(Ticket.booking_id == booking.id))
    if not ticket:
        booking.status = "CONFIRMED"; booking.hold_expires_at = None
        booking.cancellation_deadline = datetime.combine(
            slot.visit_date, slot.start_time, tzinfo=ZoneInfo("Asia/Kolkata")
        ) - timedelta(hours=24)
        payment = Payment(booking_id=booking.id, provider="local_demo", provider_order_id=f"demo_order_{uuid4().hex}", provider_payment_id=f"demo_pay_{uuid4().hex}", status="CAPTURED", amount=booking.total_amount)
        attraction = db.scalar(select(Attraction).where(Attraction.id == booking.attraction_id))
        items = list(db.scalars(select(BookingItem).where(BookingItem.booking_id == booking.id)))
        ticket_code = f"TIX-{uuid4().hex[:12].upper()}"
        quantity_labels = {"adult": "Adult", "student": "Student", "child": "Child"}
        quantity_details = [
            {"type": quantity_labels.get(item.ticket_type_code, item.ticket_type_code.title()), "quantity": item.quantity}
            for item in items
        ]
        visit_slot = f"{slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}"
        ticket_expiry = datetime.combine(
            slot.visit_date + timedelta(days=1),
            time.min,
            tzinfo=timezone.utc,
        )
        qr_token = jwt.encode(
            {
                "ticket": booking.reference,
                "booking_id": booking.id,
                "attraction_id": booking.attraction_id,
                "site": attraction.name,
                "visit_date": slot.visit_date.isoformat(),
                "visit_slot": visit_slot,
                "amount_paid": booking.total_amount,
                "visitors": quantity_details,
                "ticket_code": ticket_code,
                "exp": ticket_expiry,
            },
            get_settings().ticket_signing_key,
            algorithm=get_settings().jwt_algorithm,
        )
        ticket = Ticket(booking_id=booking.id, ticket_code=ticket_code, qr_token=qr_token)
        db.add(payment); db.add(ticket); db.commit(); db.refresh(booking)
        ticket.email_delivery_status = send_ticket_confirmation(
            recipient=user.email,
            visitor_name=user.full_name,
            attraction_name=attraction.name,
            booking_reference=booking.reference,
            ticket_code=ticket.ticket_code,
            amount=booking.total_amount,
            visit_date=slot.visit_date.strftime("%d %B %Y"),
            visit_slot=visit_slot,
            quantities=[(detail["type"], detail["quantity"]) for detail in quantity_details],
            qr_payload=qr_token,
        )
        db.commit()
    items = list(db.scalars(select(BookingItem).where(BookingItem.booking_id == booking.id)))
    return DemoPayOut(booking=booking_out(booking, items), ticket_code=ticket.ticket_code, ticket_status=ticket.status, email_delivery_status=ticket.email_delivery_status)
