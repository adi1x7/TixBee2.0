from datetime import date, time, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.config import get_settings
from app.core.security import hash_password
from app.models import Attraction, AttractionFaq, TicketType, TimeSlot, User


CATALOG = [
    {
        "slug": "visvesvaraya-museum", "name": "Visvesvaraya Museum", "city": "Bengaluru", "category": "museum",
        "short_description": "Hands-on science and engineering exhibits for curious minds.",
        "description": "A lively science museum with interactive galleries that make engineering, space, and physics approachable for every age.",
        "opening_hours": "10:00 AM – 5:30 PM, Tuesday to Sunday",
        "visitor_rules": ["Large bags must be deposited at the cloakroom.", "Photography is permitted without flash.", "Children must be accompanied by an adult."],
        "facilities": ["Wheelchair access", "Cloakroom", "Café", "Accessible washrooms"],
        "directions_url": "https://maps.google.com/?q=Visvesvaraya+Industrial+and+Technological+Museum",
        "faqs": [("Is it suitable for children?", "Yes. The interactive galleries are especially popular with school-age visitors."), ("Can I take photographs?", "Yes, as long as flash is not used inside the galleries.")],
    },
    {
        "slug": "bangalore-palace", "name": "Bangalore Palace", "city": "Bengaluru", "category": "heritage",
        "short_description": "A Tudor-inspired royal residence with grand interiors and gardens.",
        "description": "Explore the ornate rooms, painted ceilings, and landscaped grounds of one of Bengaluru’s best-known heritage landmarks.",
        "opening_hours": "10:00 AM – 5:30 PM, daily",
        "visitor_rules": ["Entry is valid only for the booked time slot.", "Professional shoots require prior permission.", "Food is not permitted inside the palace."],
        "facilities": ["Audio guide", "Cloakroom", "Parking", "Washrooms"],
        "directions_url": "https://maps.google.com/?q=Bangalore+Palace",
        "faqs": [("How long should I plan for?", "Most visitors spend about 90 minutes exploring the palace."), ("Is there parking?", "Limited paid parking is available near the entrance.")],
    },
    {
        "slug": "national-museum", "name": "National Museum", "city": "Delhi", "category": "museum",
        "short_description": "Indian art, archaeology, and history across millennia.",
        "description": "A considered journey through Indian cultural history, from ancient artefacts to decorative arts and miniature paintings.",
        "opening_hours": "10:00 AM – 6:00 PM, Tuesday to Sunday",
        "visitor_rules": ["Flash photography is not allowed.", "Security screening is required at entry.", "Please keep a respectful distance from displays."],
        "facilities": ["Wheelchair access", "Café", "Bookshop", "Lockers"],
        "directions_url": "https://maps.google.com/?q=National+Museum+New+Delhi",
        "faqs": [("Is the museum open on Mondays?", "No. The museum is closed on Mondays."), ("Are lockers available?", "Yes, small personal items can be stored at the visitor lockers.")],
    },
    {
        "slug": "csmvs-museum", "name": "CSMVS Museum", "city": "Mumbai", "category": "gallery",
        "short_description": "Art, archaeology, and design in a landmark Indo-Saracenic building.",
        "description": "Spend an unhurried afternoon with Indian miniature painting, sculpture, decorative arts, and changing exhibitions.",
        "opening_hours": "10:15 AM – 6:00 PM, daily",
        "visitor_rules": ["Silent mode is required in galleries.", "Food and beverages are not permitted inside.", "Photography rules vary by exhibition."],
        "facilities": ["Museum shop", "Wheelchair access", "Café", "Washrooms"],
        "directions_url": "https://maps.google.com/?q=Chhatrapati+Shivaji+Maharaj+Vastu+Sangrahalaya",
        "faqs": [("Does my ticket include temporary exhibitions?", "Most temporary exhibitions are included unless noted on the attraction page."), ("Can students receive a discount?", "Yes. Bring a valid student ID with your ticket.")],
    },
    {"slug":"hawa-mahal","name":"Hawa Mahal","city":"Jaipur","category":"heritage","short_description":"The iconic Palace of Winds in Jaipur’s old city.","description":"Step into Jaipur’s famous pink sandstone landmark and explore the historic heart of the city.","opening_hours":"9:00 AM – 5:00 PM, daily","visitor_rules":["Respect heritage spaces.","Photography without flash is welcome."],"facilities":["Audio guide","Nearby parking","Washrooms"],"directions_url":"https://maps.google.com/?q=Hawa+Mahal+Jaipur","image_url":"https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80","faqs":[("How long should I plan for?","Most visitors spend 45–60 minutes here.")]},
    {"slug":"gateway-of-india","name":"Gateway of India","city":"Mumbai","category":"heritage","short_description":"A waterfront landmark at the edge of the Arabian Sea.","description":"Take in Mumbai’s classic harbour-front monument and the energy of Colaba.","opening_hours":"Open all day","visitor_rules":["Keep the promenade clean.","Follow local security instructions."],"facilities":["Nearby cafés","Public transport","Accessible promenade"],"directions_url":"https://maps.google.com/?q=Gateway+of+India+Mumbai","image_url":"https://www.seascanner.co.uk/images/10021/1/d6aac7d3-0c30-4cb6-8edb-1a2a9c8faf0e_Gateway-of-India-Mumbai.jpg?auto=compress%2Cformat&fit=crop&h=500&q=50&rect=77%2C0%2C600%2C600&w=500","faqs":[("Do I need a ticket?","The public monument and promenade are open to visitors.")]},
    {"slug":"salar-jung-museum","name":"Salar Jung Museum","city":"Hyderabad","category":"museum","short_description":"An eclectic collection of art, clocks, sculpture, and decorative objects.","description":"Spend an afternoon with one of India’s most wide-ranging museum collections.","opening_hours":"10:00 AM – 5:00 PM, Friday to Wednesday","visitor_rules":["No flash photography.","Large bags must be deposited."],"facilities":["Cloakroom","Café","Accessible washrooms"],"directions_url":"https://maps.google.com/?q=Salar+Jung+Museum+Hyderabad","image_url":"https://images.unsplash.com/photo-1564399579883-451a5d44ec08?auto=format&fit=crop&w=1200&q=80","faqs":[("What is the highlight?","The Veiled Rebecca sculpture and the antique clock gallery are visitor favourites.")]},
    {"slug":"victoria-memorial","name":"Victoria Memorial","city":"Kolkata","category":"heritage","short_description":"A grand marble landmark surrounded by peaceful gardens.","description":"Discover Kolkata’s landmark museum and gardens, built in a distinctive Indo-Saracenic style.","opening_hours":"10:00 AM – 5:00 PM, Tuesday to Sunday","visitor_rules":["Follow museum gallery guidelines.","Keep gardens clean."],"facilities":["Museum shop","Gardens","Wheelchair access"],"directions_url":"https://maps.google.com/?q=Victoria+Memorial+Kolkata","image_url":"https://images.unsplash.com/photo-1600100397608-f0100c83f8e0?auto=format&fit=crop&w=1200&q=80","faqs":[("Is it open on Mondays?","The museum is closed on Mondays.")]},
]


def seed_catalog() -> None:
    """Create deterministic local development data once; production uses admin-managed data."""
    with SessionLocal() as session:
        settings = get_settings()
        if settings.demo_bootstrap_password:
            for email, full_name, role in (
                (settings.demo_staff_email, "TixBee Demo Staff", "staff"),
                (settings.demo_admin_email, "TixBee Demo Admin", "admin"),
            ):
                if not session.scalar(select(User.id).where(User.email == email.lower())):
                    session.add(User(
                        full_name=full_name,
                        email=email.lower(),
                        password_hash=hash_password(settings.demo_bootstrap_password),
                        role=role,
                    ))
        for entry in CATALOG:
            if session.scalar(select(Attraction.id).where(Attraction.slug == entry["slug"])):
                continue
            attraction = Attraction(
                **{key: value for key, value in entry.items() if key not in {"faqs"}},
                is_published=True,
            )
            attraction.ticket_types = [
                TicketType(code="adult", label="Adult", price=300, eligibility_note="Ages 18 and above"),
                TicketType(code="student", label="Student", price=220, eligibility_note="Valid student ID required"),
                TicketType(code="child", label="Child", price=150, eligibility_note="Ages 5–17; under 5 enter free"),
            ]
            attraction.faqs = [AttractionFaq(question=question, answer=answer, sort_order=index)
                               for index, (question, answer) in enumerate(entry["faqs"])]
            for day_offset in range(1, 15):
                visit_day = date.today() + timedelta(days=day_offset)
                for start, end in ((time(10, 0), time(12, 0)), (time(12, 30), time(14, 30)), (time(15, 0), time(17, 0))):
                    attraction.slots.append(TimeSlot(visit_date=visit_day, start_time=start, end_time=end,
                                                     capacity=40, remaining_capacity=40))
            session.add(attraction)
        session.commit()
