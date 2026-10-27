from datetime import date, datetime, time, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default="customer", index=True)
    assigned_attraction_id: Mapped[str | None] = mapped_column(
        ForeignKey("attractions.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Attraction(Base):
    __tablename__ = "attractions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    city: Mapped[str] = mapped_column(String(80), index=True)
    category: Mapped[str] = mapped_column(String(30), index=True)
    short_description: Mapped[str] = mapped_column(String(320))
    description: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    opening_hours: Mapped[str] = mapped_column(String(200))
    visitor_rules: Mapped[list] = mapped_column(JSON, default=list)
    facilities: Mapped[list] = mapped_column(JSON, default=list)
    directions_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    faqs: Mapped[list["AttractionFaq"]] = relationship(back_populates="attraction", cascade="all, delete-orphan")
    ticket_types: Mapped[list["TicketType"]] = relationship(back_populates="attraction", cascade="all, delete-orphan")
    slots: Mapped[list["TimeSlot"]] = relationship(back_populates="attraction", cascade="all, delete-orphan")

    @property
    def starting_price(self) -> int:
        """Lowest active ticket price, exposed on discovery cards."""
        active_prices = [ticket.price for ticket in self.ticket_types if ticket.is_active]
        return min(active_prices) if active_prices else 0


class AttractionFaq(Base):
    __tablename__ = "attraction_faqs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    attraction_id: Mapped[str] = mapped_column(ForeignKey("attractions.id", ondelete="CASCADE"), index=True)
    question: Mapped[str] = mapped_column(String(300))
    answer: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    attraction: Mapped[Attraction] = relationship(back_populates="faqs")


class TimeSlot(Base):
    __tablename__ = "time_slots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    attraction_id: Mapped[str] = mapped_column(ForeignKey("attractions.id", ondelete="CASCADE"), index=True)
    visit_date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    capacity: Mapped[int] = mapped_column(Integer)
    remaining_capacity: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    attraction: Mapped[Attraction] = relationship(back_populates="slots")
    __table_args__ = (UniqueConstraint("attraction_id", "visit_date", "start_time", name="uq_slot_attraction_date_time"),)


class TicketType(Base):
    __tablename__ = "ticket_types"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    attraction_id: Mapped[str] = mapped_column(ForeignKey("attractions.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(20))
    label: Mapped[str] = mapped_column(String(50))
    price: Mapped[int] = mapped_column(Integer)
    eligibility_note: Mapped[str | None] = mapped_column(String(250), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    attraction: Mapped[Attraction] = relationship(back_populates="ticket_types")
    __table_args__ = (UniqueConstraint("attraction_id", "code", name="uq_ticket_type_attraction_code"),)


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    reference: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    attraction_id: Mapped[str] = mapped_column(ForeignKey("attractions.id"), index=True)
    slot_id: Mapped[str] = mapped_column(ForeignKey("time_slots.id"), index=True)
    status: Mapped[str] = mapped_column(String(24), default="DRAFT", index=True)
    hold_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_amount: Mapped[int] = mapped_column(Integer, default=0)
    price_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    cancellation_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class BookingItem(Base):
    __tablename__ = "booking_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), index=True)
    ticket_type_code: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[int] = mapped_column(Integer)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(30), default="razorpay_test")
    provider_order_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="PENDING", index=True)
    amount: Mapped[int] = mapped_column(Integer)
    webhook_event_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    refund_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    refund_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True, index=True)
    ticket_code: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    qr_token: Mapped[str] = mapped_column(Text, unique=True)
    status: Mapped[str] = mapped_column(String(24), default="ISSUED", index=True)
    email_delivery_status: Mapped[str] = mapped_column(String(24), default="PENDING")
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    redeemed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    attraction_id: Mapped[str | None] = mapped_column(ForeignKey("attractions.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(12))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
