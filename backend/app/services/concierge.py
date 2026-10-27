import logging

from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models import Attraction, Booking, ChatMessage, Ticket, TimeSlot, User
from app.models.domain import utcnow

logger = logging.getLogger(__name__)


def _catalog_context(db: Session, message: str, attraction_id: str | None = None) -> str:
    attractions = list(db.scalars(
        select(Attraction)
        .options(selectinload(Attraction.ticket_types), selectinload(Attraction.faqs))
        .where(Attraction.is_published.is_(True))
    ))
    message_lower = message.lower()
    selected = next((attraction for attraction in attractions if attraction.id == attraction_id), None)
    named = next((attraction for attraction in attractions if attraction.name.lower() in message_lower), None)
    cities = {"bengaluru", "delhi", "kolkata", "mumbai"}
    mentioned_city = next((city for city in cities if city in message_lower), None)
    relevant = [selected or named] if selected or named else [attraction for attraction in attractions if attraction.city.lower() == mentioned_city] if mentioned_city else attractions
    detailed = bool(selected or named)
    entries = []
    for attraction in relevant:
        tiers = ", ".join(f"{tier.label}: ₹{tier.price}" for tier in attraction.ticket_types if tier.is_active)
        if not detailed:
            entries.append(f"- {attraction.name} | {attraction.city} | {attraction.category} | tickets: {tiers}")
            continue
        facilities = ", ".join(attraction.facilities)
        rules = "; ".join(attraction.visitor_rules)
        faqs = "; ".join(f"{faq.question} — {faq.answer}" for faq in attraction.faqs)
        entries.append(
            f"- {attraction.name} | {attraction.city} | {attraction.category} | "
            f"{attraction.short_description} | hours: {attraction.opening_hours} | tickets: {tiers} | "
            f"facilities: {facilities} | visitor rules: {rules} | FAQs: {faqs}"
        )
    return "\n".join(entries)


def _booking_reply(db: Session, message: str, user: User | None) -> str | None:
    """Answer account questions locally so private booking data never leaves TixBee."""
    booking_phrases = (
        "my booking", "my bookings", "my ticket", "my tickets", "my reservation",
        "my visit", "my trip", "booking status", "ticket status", "cancel my", "refund my",
    )
    if not any(phrase in message.lower() for phrase in booking_phrases):
        return None
    if not user or user.role != "customer":
        return "Please sign in first, then I can look up your own bookings and ticket status securely."
    rows = list(db.execute(
        select(Booking, Attraction, TimeSlot, Ticket)
        .join(Attraction, Attraction.id == Booking.attraction_id)
        .join(TimeSlot, TimeSlot.id == Booking.slot_id)
        .outerjoin(Ticket, Ticket.booking_id == Booking.id)
        .where(Booking.user_id == user.id)
        .order_by(Booking.created_at.desc())
        .limit(5)
    ))
    if not rows:
        return "You do not have any bookings yet. Choose an experience and a visit time to get started."
    booking, attraction, slot, ticket = rows[0]
    ticket_detail = f" Your ticket code is {ticket.ticket_code}." if ticket else " Your ticket has not been issued yet."
    cancellation = ""
    if booking.cancellation_deadline and booking.status == "CONFIRMED":
        if utcnow() < booking.cancellation_deadline:
            cancellation = " This booking is still within its cancellation window; open My bookings to review and proceed."
        else:
            cancellation = " Its 24-hour cancellation window has closed."
    return (
        f"Your most recent booking is {booking.reference}: {booking.status} for {attraction.name}, "
        f"{slot.visit_date.strftime('%d %B %Y')} at {slot.start_time.strftime('%H:%M')}."
        f"{ticket_detail}{cancellation} Open My bookings for the full ticket and visit details."
    )


def answer_concierge(
    db: Session,
    session_id: str,
    message: str,
    attraction_id: str | None = None,
    user: User | None = None,
) -> tuple[str | None, str, str | None]:
    selected_attraction_id = None
    if attraction_id and db.scalar(select(Attraction.id).where(Attraction.id == attraction_id, Attraction.is_published.is_(True))):
        selected_attraction_id = attraction_id
    db.add(ChatMessage(user_id=user.id if user else None, session_id=session_id, attraction_id=selected_attraction_id, role="user", content=message.strip()))
    db.commit()
    local_reply = _booking_reply(db, message, user)
    if local_reply:
        db.add(ChatMessage(user_id=user.id if user else None, session_id=session_id, attraction_id=selected_attraction_id, role="assistant", content=local_reply))
        db.commit()
        return local_reply, "available", "TixBee account"

    settings = get_settings()
    if not settings.gemini_api_key:
        return None, "unavailable", None
    history_query = select(ChatMessage).where(ChatMessage.session_id == session_id)
    history_query = history_query.where(ChatMessage.user_id == user.id) if user else history_query.where(ChatMessage.user_id.is_(None))
    previous = list(db.scalars(history_query.order_by(ChatMessage.created_at.desc()).limit(settings.concierge_history_messages)))
    conversation = "\n".join(f"{item.role.title()}: {item.content}" for item in reversed(previous))
    prompt = f"""You are TixBee Concierge, a concise, warm planning assistant for cultural outings in India.

You may help visitors explore the TixBee catalog, compare venues, understand ticket tiers/hours, and plan a visit. Account-specific booking information is handled by TixBee directly, so never request or infer booking references, ticket codes, payment details, passwords, emails, phone numbers, card information, or UPI details. You must not claim a booking is made, a ticket is held, availability is guaranteed, or payment has occurred. Never invent attractions, fees, slot times, policies, opening hours, discounts, refunds, or booking statuses. If a needed fact is absent, say so briefly and direct the visitor to the attraction page or My bookings. Keep answers under 120 words and ask at most one useful follow-up question.

Live TixBee catalog:
{_catalog_context(db, message, selected_attraction_id)}

Conversation so far:
{conversation}

Reply only with the assistant response; no labels or markdown heading."""
    client = genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=settings.concierge_timeout_ms))
    try:
        response = client.models.generate_content(model=settings.gemini_model, contents=prompt)
        answer = (response.text or "").strip()
        if not answer:
            raise RuntimeError("Gemini returned an empty response")
        db.add(ChatMessage(user_id=user.id if user else None, session_id=session_id, attraction_id=selected_attraction_id, role="assistant", content=answer))
        db.commit()
        return answer, "available", settings.gemini_model
    except Exception as exc:  # Provider errors are exposed only as availability, never as fabricated advice.
        logger.warning("Concierge provider was unavailable: %s", exc)
        return None, "unavailable", None
