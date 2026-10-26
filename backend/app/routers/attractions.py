from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import Attraction, TimeSlot
from app.schemas.attractions import AttractionCardOut, AttractionDetailOut, SlotOut

router = APIRouter(prefix="/attractions", tags=["attractions"])


@router.get("", response_model=list[AttractionCardOut])
def list_attractions(
    city: str | None = None,
    category: str | None = None,
    search: str | None = Query(default=None, min_length=1, max_length=80),
    db: Session = Depends(get_db),
):
    query: Select = (select(Attraction).options(selectinload(Attraction.ticket_types))
                     .where(Attraction.is_published.is_(True)).order_by(Attraction.city, Attraction.name))
    if city:
        query = query.where(Attraction.city.ilike(city))
    if category:
        query = query.where(Attraction.category == category)
    if search:
        query = query.where(Attraction.name.ilike(f"%{search.strip()}%"))
    return list(db.scalars(query))


@router.get("/{attraction_id}", response_model=AttractionDetailOut)
def get_attraction(attraction_id: str, db: Session = Depends(get_db)):
    query = (select(Attraction)
             .options(selectinload(Attraction.ticket_types), selectinload(Attraction.faqs))
             .where(Attraction.id == attraction_id, Attraction.is_published.is_(True)))
    attraction = db.scalar(query)
    if not attraction:
        raise HTTPException(status_code=404, detail="Attraction not found.")
    return attraction


@router.get("/{attraction_id}/slots", response_model=list[SlotOut])
def get_slots(attraction_id: str, from_date: date | None = None, db: Session = Depends(get_db)):
    minimum_date = from_date or date.today()
    query = (select(TimeSlot).where(TimeSlot.attraction_id == attraction_id,
                                    TimeSlot.is_active.is_(True),
                                    TimeSlot.visit_date >= minimum_date,
                                    TimeSlot.remaining_capacity > 0)
             .order_by(TimeSlot.visit_date, TimeSlot.start_time))
    return list(db.scalars(query))
