from google import genai
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models import Attraction, ChatMessage


def _catalog_context(db: Session) -> str:
    attractions = list(db.scalars(select(Attraction).options(selectinload(Attraction.ticket_types), selectinload(Attraction.slots)).where(Attraction.is_published.is_(True))))
    entries = []
    for attraction in attractions:
        tiers = ", ".join(f"{tier.label}: ₹{tier.price}" for tier in attraction.ticket_types if tier.is_active)
        entries.append(f"- {attraction.name} | {attraction.city} | {attraction.category} | {attraction.short_description} | hours: {attraction.opening_hours} | tickets: {tiers}")
    return "\n".join(entries)


def answer_concierge(db: Session, session_id: str, message: str, attraction_id: str | None = None) -> tuple[str | None, str, str | None]:
    settings = get_settings()
    db.add(ChatMessage(session_id=session_id, attraction_id=attraction_id, role="user", content=message.strip()))
    db.commit()
    if not settings.gemini_api_key:
        return None, "unavailable", None
    previous = list(db.scalars(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc()).limit(8)))
    conversation = "\n".join(f"{item.role.title()}: {item.content}" for item in reversed(previous))
    prompt = f"""You are TixBee Concierge, a concise, warm planning assistant for cultural outings in India.

You may help visitors explore the TixBee catalog, compare venues, understand ticket tiers/hours, and plan a visit. You must not claim a booking is made, a ticket is held, availability is guaranteed, or payment has occurred. Never invent attractions, fees, slot times, policies, opening hours, or discounts. If a needed fact is absent, say so briefly and direct the visitor to the attraction page. Keep answers under 120 words and ask at most one useful follow-up question.

Live TixBee catalog:
{_catalog_context(db)}

Conversation so far:
{conversation}

Reply only with the assistant response; no labels or markdown heading."""
    client = genai.Client(api_key=settings.gemini_api_key)
    last_error: Exception | None = None
    for model in (settings.gemini_model, settings.gemini_fallback_model):
        if not model:
            continue
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            answer = (response.text or "").strip()
            if not answer:
                raise RuntimeError("Gemini returned an empty response")
            db.add(ChatMessage(session_id=session_id, attraction_id=attraction_id, role="assistant", content=answer))
            db.commit()
            return answer, "available", model
        except Exception as exc:  # Provider errors are exposed only as availability, never as fabricated advice.
            last_error = exc
    return None, "unavailable", None
