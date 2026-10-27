from datetime import date, datetime

import jwt
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import admin_user, staff_user
from app.models import Attraction, Booking, Ticket, TimeSlot, User
from app.models.domain import utcnow
from app.schemas.operations import CustomerDirectoryOut, OperationActivityOut, SlotManagementOut, SlotUpdateIn

router = APIRouter(prefix="/operations", tags=["operations"])


def staff_scope(user: User, db: Session) -> tuple[str | None, str]:
    """Return the attraction a staff member may operate, or all sites for admin."""
    if user.role == "admin":
        return None, "All TixBee attractions"
    if not user.assigned_attraction_id:
        raise HTTPException(status_code=403, detail="This staff account is not assigned to a visit site.")
    attraction = db.scalar(
        select(Attraction).where(
            Attraction.id == user.assigned_attraction_id,
            Attraction.is_published.is_(True),
        )
    )
    if not attraction:
        raise HTTPException(status_code=403, detail="This staff account's visit-site assignment is unavailable.")
    return attraction.id, attraction.name


@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(staff_user)):
    attraction_id, scope_name = staff_scope(user, db)
    ticket_query = select(func.count()).select_from(Ticket).join(Booking, Booking.id == Ticket.booking_id)
    booking_query = select(func.count()).select_from(Booking)
    if attraction_id:
        ticket_query = ticket_query.where(Booking.attraction_id == attraction_id)
        booking_query = booking_query.where(Booking.attraction_id == attraction_id)
    return {
        "issued": db.scalar(ticket_query.where(Ticket.status == "ISSUED")) or 0,
        "redeemed": db.scalar(ticket_query.where(Ticket.status == "REDEEMED")) or 0,
        "confirmed_bookings": db.scalar(booking_query.where(Booking.status == "CONFIRMED")) or 0,
        "scope": scope_name,
        "scope_type": "all_attractions" if attraction_id is None else "single_attraction",
    }


@router.get("/activity", response_model=list[OperationActivityOut])
def operation_activity(
    kind: Literal["issued", "redeemed", "confirmed"] = Query(),
    db: Session = Depends(get_db),
    user: User = Depends(staff_user),
):
    """Return only the operational records covered by the caller's site scope."""
    attraction_id, _ = staff_scope(user, db)
    query = (
        select(
            Booking.reference,
            Ticket.ticket_code,
            Ticket.status.label("ticket_status"),
            Attraction.name.label("attraction_name"),
            Attraction.city,
            TimeSlot.visit_date,
            TimeSlot.start_time,
            User.full_name.label("customer_name"),
            Booking.total_amount,
            Booking.created_at,
            Ticket.redeemed_at,
        )
        .join(Attraction, Attraction.id == Booking.attraction_id)
        .join(TimeSlot, TimeSlot.id == Booking.slot_id)
        .outerjoin(Ticket, Ticket.booking_id == Booking.id)
        .outerjoin(User, User.id == Booking.user_id)
    )
    if attraction_id:
        query = query.where(Booking.attraction_id == attraction_id)
    if kind == "issued":
        query = query.where(Ticket.status == "ISSUED").order_by(Booking.created_at.desc())
    elif kind == "redeemed":
        query = query.where(Ticket.status == "REDEEMED").order_by(Ticket.redeemed_at.desc())
    else:
        query = query.where(Booking.status == "CONFIRMED").order_by(Booking.created_at.desc())
    rows = db.execute(query.limit(100)).all()
    return [
        OperationActivityOut(
            booking_reference=row.reference,
            ticket_code=row.ticket_code,
            ticket_status=row.ticket_status,
            attraction_name=row.attraction_name,
            city=row.city,
            visit_date=row.visit_date,
            start_time=row.start_time,
            customer_name=row.customer_name,
            total_amount=row.total_amount,
            created_at=row.created_at,
            redeemed_at=row.redeemed_at,
        )
        for row in rows
    ]


@router.get("/slots", response_model=list[SlotManagementOut])
def managed_slots(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    rows = db.execute(
        select(TimeSlot, Attraction.name)
        .join(Attraction, Attraction.id == TimeSlot.attraction_id)
        .where(TimeSlot.visit_date >= date.today(), Attraction.is_published.is_(True))
        .order_by(TimeSlot.visit_date, TimeSlot.start_time)
    ).all()
    return [
        SlotManagementOut(
            id=slot.id,
            attraction_id=slot.attraction_id,
            attraction_name=attraction_name,
            visit_date=slot.visit_date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            capacity=slot.capacity,
            remaining_capacity=slot.remaining_capacity,
            is_active=slot.is_active,
        )
        for slot, attraction_name in rows
    ]


@router.get("/customers", response_model=list[CustomerDirectoryOut])
def managed_customers(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    """Return operational customer information only; credentials are never exposed."""
    rows = db.execute(
        select(
            User.id,
            User.full_name,
            User.email,
            User.is_active,
            func.count(Booking.id).label("booking_count"),
            func.coalesce(
                func.sum(case((Booking.status == "CONFIRMED", 1), else_=0)),
                0,
            ).label("confirmed_booking_count"),
            func.max(Booking.created_at).label("latest_booking_at"),
        )
        .outerjoin(Booking, Booking.user_id == User.id)
        .where(User.role == "customer")
        .group_by(User.id, User.full_name, User.email, User.is_active)
        .order_by(User.created_at.desc())
    ).all()
    return [
        CustomerDirectoryOut(
            id=row.id,
            full_name=row.full_name,
            email=row.email,
            is_active=row.is_active,
            booking_count=row.booking_count,
            confirmed_booking_count=row.confirmed_booking_count,
            latest_booking_at=row.latest_booking_at,
        )
        for row in rows
    ]


@router.patch("/slots/{slot_id}", response_model=SlotManagementOut)
def update_slot(slot_id: str, payload: SlotUpdateIn, db: Session = Depends(get_db), _: User = Depends(admin_user)):
    slot = db.scalar(select(TimeSlot).where(TimeSlot.id == slot_id).with_for_update())
    if not slot:
        raise HTTPException(status_code=404, detail="Visit slot not found.")
    reserved_count = slot.capacity - slot.remaining_capacity
    if payload.capacity is not None:
        if payload.capacity < reserved_count:
            raise HTTPException(
                status_code=409,
                detail=f"Capacity cannot be lower than the {reserved_count} already reserved places.",
            )
        slot.remaining_capacity = payload.capacity - reserved_count
        slot.capacity = payload.capacity
    if payload.is_active is not None:
        slot.is_active = payload.is_active
    db.commit()
    db.refresh(slot)
    attraction = db.scalar(select(Attraction).where(Attraction.id == slot.attraction_id))
    return SlotManagementOut(
        id=slot.id,
        attraction_id=slot.attraction_id,
        attraction_name=attraction.name,
        visit_date=slot.visit_date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        capacity=slot.capacity,
        remaining_capacity=slot.remaining_capacity,
        is_active=slot.is_active,
    )


@router.post("/tickets/{ticket_code}/redeem")
def redeem(ticket_code: str, db: Session = Depends(get_db), user: User = Depends(staff_user)):
    ticket = db.scalar(select(Ticket).where(Ticket.ticket_code == ticket_code).with_for_update())
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    if ticket.status == "REDEEMED":
        raise HTTPException(status_code=409, detail="This ticket has already been redeemed.")
    if ticket.status != "ISSUED":
        raise HTTPException(status_code=409, detail="This ticket cannot be redeemed.")
    booking = db.scalar(select(Booking).where(Booking.id == ticket.booking_id))
    slot = db.scalar(select(TimeSlot).where(TimeSlot.id == booking.slot_id)) if booking else None
    if not booking or booking.status != "CONFIRMED" or not slot:
        raise HTTPException(status_code=409, detail="The ticket is not linked to a valid confirmed booking.")
    assigned_attraction_id, _ = staff_scope(user, db)
    if assigned_attraction_id and booking.attraction_id != assigned_attraction_id:
        raise HTTPException(status_code=403, detail="This ticket belongs to a different visit site.")
    try:
        payload = jwt.decode(
            ticket.qr_token,
            get_settings().ticket_signing_key,
            algorithms=[get_settings().jwt_algorithm],
            options={"require": ["booking_id", "ticket", "exp"]},
        )
        if payload.get("booking_id") != booking.id or payload.get("ticket") != booking.reference:
            raise ValueError("Ticket payload does not match the booking")
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(status_code=409, detail="This ticket has an invalid or expired signature.") from exc
    if slot.visit_date != date.today():
        raise HTTPException(status_code=409, detail="This ticket is valid only on its booked visit date.")
    ticket.status = "REDEEMED"; ticket.redeemed_at = utcnow(); ticket.redeemed_by_user_id = user.id
    db.commit()
    return {"ticket_code": ticket.ticket_code, "status": ticket.status, "redeemed_at": ticket.redeemed_at}
