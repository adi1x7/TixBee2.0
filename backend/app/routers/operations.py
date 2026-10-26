from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import admin_user, staff_user
from app.models import Attraction, Booking, Ticket, TimeSlot, User
from app.models.domain import utcnow
from app.schemas.operations import SlotManagementOut, SlotUpdateIn

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/summary")
def summary(db: Session = Depends(get_db), _: User = Depends(staff_user)):
    return {"issued": db.scalar(select(func.count()).select_from(Ticket).where(Ticket.status == "ISSUED")) or 0,
            "redeemed": db.scalar(select(func.count()).select_from(Ticket).where(Ticket.status == "REDEEMED")) or 0,
            "confirmed_bookings": db.scalar(select(func.count()).select_from(Booking).where(Booking.status == "CONFIRMED")) or 0}


@router.get("/slots", response_model=list[SlotManagementOut])
def managed_slots(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    rows = db.execute(
        select(TimeSlot, Attraction.name)
        .join(Attraction, Attraction.id == TimeSlot.attraction_id)
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
    ticket.status = "REDEEMED"; ticket.redeemed_at = utcnow(); ticket.redeemed_by_user_id = user.id
    db.commit()
    return {"ticket_code": ticket.ticket_code, "status": ticket.status, "redeemed_at": ticket.redeemed_at}
