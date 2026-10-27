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
    {"slug":"gateway-of-india","name":"Gateway of India","city":"Mumbai","category":"heritage","short_description":"A waterfront landmark at the edge of the Arabian Sea.","description":"Take in Mumbai’s classic harbour-front monument and the energy of Colaba.","opening_hours":"Open all day","visitor_rules":["Keep the promenade clean.","Follow local security instructions."],"facilities":["Nearby cafés","Public transport","Accessible promenade"],"directions_url":"https://maps.google.com/?q=Gateway+of+India+Mumbai","image_url":"https://www.seascanner.co.uk/images/10021/1/d6aac7d3-0c30-4cb6-8edb-1a2a9c8faf0e_Gateway-of-India-Mumbai.jpg?auto=compress%2Cformat&fit=crop&h=500&q=50&rect=77%2C0%2C600%2C600&w=500","faqs":[("Do I need a ticket?","The public monument and promenade are open to visitors.")]},
    {"slug":"victoria-memorial","name":"Victoria Memorial","city":"Kolkata","category":"heritage","short_description":"A grand marble landmark surrounded by peaceful gardens.","description":"Discover Kolkata’s landmark museum and gardens, built in a distinctive Indo-Saracenic style.","opening_hours":"10:00 AM – 5:00 PM, Tuesday to Sunday","visitor_rules":["Follow museum gallery guidelines.","Keep gardens clean."],"facilities":["Museum shop","Gardens","Wheelchair access"],"directions_url":"https://maps.google.com/?q=Victoria+Memorial+Kolkata","image_url":"https://images.unsplash.com/photo-1600100397608-f0100c83f8e0?auto=format&fit=crop&w=1200&q=80","faqs":[("Is it open on Mondays?","The museum is closed on Mondays.")]},
    {"slug":"lalbagh-botanical-garden","name":"Lalbagh Botanical Garden","city":"Bengaluru","category":"nature","short_description":"A historic garden known for its glasshouse and mature trees.","description":"Walk through lakeside paths, botanical collections, and the iconic glasshouse in central Bengaluru.","opening_hours":"6:00 AM – 7:00 PM, daily","visitor_rules":["Keep to marked paths.","Do not disturb plants or wildlife."],"facilities":["Parking","Washrooms","Wheelchair-friendly paths"],"directions_url":"https://maps.google.com/?q=Lalbagh+Botanical+Garden+Bengaluru","faqs":[("How long should I plan for?","Most visitors spend one to two hours in the garden.")]},
    {"slug":"karnataka-chitrakala-parishath","name":"Karnataka Chitrakala Parishath","city":"Bengaluru","category":"gallery","short_description":"A campus of Indian art galleries and changing exhibitions.","description":"Explore a thoughtful collection of modern, folk, and traditional Indian art in Bengaluru.","opening_hours":"10:30 AM – 7:30 PM, Tuesday to Sunday","visitor_rules":["Do not touch artworks.","Follow gallery photography notices."],"facilities":["Gallery shop","Washrooms","Café nearby"],"directions_url":"https://maps.google.com/?q=Karnataka+Chitrakala+Parishath+Bengaluru","faqs":[("Are exhibitions permanent?","The campus combines permanent collections with changing exhibitions.")]},
    {"slug":"india-gate","name":"India Gate","city":"Delhi","category":"heritage","short_description":"A landmark war memorial set along Delhi’s ceremonial avenue.","description":"Visit one of Delhi’s best-known public monuments and its surrounding lawns.","opening_hours":"Open all day","visitor_rules":["Follow security guidance.","Keep the public lawns clean."],"facilities":["Public transport","Nearby cafés","Accessible paths"],"directions_url":"https://maps.google.com/?q=India+Gate+Delhi","faqs":[("Do I need a ticket?","The monument and surrounding public area are free to visit.")]},
    {"slug":"qutub-minar","name":"Qutub Minar","city":"Delhi","category":"heritage","short_description":"A UNESCO-listed minaret within Delhi’s historic Qutub complex.","description":"Discover early Delhi Sultanate architecture, carved stonework, and the surrounding archaeological complex.","opening_hours":"7:00 AM – 5:00 PM, daily","visitor_rules":["Stay within visitor areas.","Respect protected monuments."],"facilities":["Audio guides","Washrooms","Parking nearby"],"directions_url":"https://maps.google.com/?q=Qutub+Minar+Delhi","faqs":[("How long does a visit take?","Plan around 90 minutes for the complex.")]},
    {"slug":"national-gallery-modern-art","name":"National Gallery of Modern Art","city":"Delhi","category":"gallery","short_description":"Modern and contemporary Indian art in a historic Jaipur House setting.","description":"View major works of modern Indian art and curated temporary exhibitions.","opening_hours":"10:00 AM – 5:00 PM, Tuesday to Sunday","visitor_rules":["No flash photography.","Food is not permitted in galleries."],"facilities":["Café","Bookshop","Wheelchair access"],"directions_url":"https://maps.google.com/?q=National+Gallery+of+Modern+Art+Delhi","faqs":[("Is it open on Monday?","The gallery is closed on Mondays.")]},
    {"slug":"elephanta-caves","name":"Elephanta Caves","city":"Mumbai","category":"heritage","short_description":"Rock-cut cave temples on an island in Mumbai Harbour.","description":"Take a harbour ferry to explore historic cave temples and monumental sculpture.","opening_hours":"9:00 AM – 5:30 PM, Tuesday to Sunday","visitor_rules":["Keep your return ferry timing in mind.","Do not climb on monuments."],"facilities":["Ferry access","Food stalls","Washrooms"],"directions_url":"https://maps.google.com/?q=Elephanta+Caves+Mumbai","faqs":[("How do I get there?","Ferries depart from the Gateway of India area.")]},
    {"slug":"dr-bhau-daji-lad-museum","name":"Dr Bhau Daji Lad Museum","city":"Mumbai","category":"museum","short_description":"Mumbai’s city museum with decorative arts and urban history collections.","description":"Explore the history, craft, and culture of Mumbai in a restored nineteenth-century museum.","opening_hours":"10:00 AM – 5:30 PM, Wednesday to Monday","visitor_rules":["No flash photography.","Please follow gallery instructions."],"facilities":["Café","Museum shop","Accessible entry"],"directions_url":"https://maps.google.com/?q=Dr+Bhau+Daji+Lad+Museum+Mumbai","faqs":[("Where is the museum?","It is located in Byculla, beside the zoo gardens.")]},
    {"slug":"indian-museum","name":"Indian Museum","city":"Kolkata","category":"museum","short_description":"A major museum of archaeology, art, and natural history.","description":"Explore one of India’s oldest museums, with collections spanning art, archaeology, and natural history.","opening_hours":"10:00 AM – 5:00 PM, Tuesday to Sunday","visitor_rules":["No flash photography.","Large bags may need to be deposited."],"facilities":["Cloakroom","Washrooms","Museum shop"],"directions_url":"https://maps.google.com/?q=Indian+Museum+Kolkata","faqs":[("Is the museum open on Monday?","The museum is closed on Mondays.")]},
    {"slug":"marble-palace","name":"Marble Palace","city":"Kolkata","category":"heritage","short_description":"A nineteenth-century mansion with sculpture, art, and marble interiors.","description":"See a distinctive historic residence known for its art collection and ornate interiors.","opening_hours":"10:00 AM – 4:00 PM, Tuesday to Sunday","visitor_rules":["Entry arrangements may vary.","Follow on-site photography guidance."],"facilities":["Guided visits","Nearby transport","Washrooms nearby"],"directions_url":"https://maps.google.com/?q=Marble+Palace+Kolkata","faqs":[("Should I check before visiting?","Yes. Confirm current visitor arrangements before travel.")]},
    {"slug":"science-city-kolkata","name":"Science City","city":"Kolkata","category":"museum","short_description":"Interactive science exhibits, space displays, and family learning zones.","description":"Spend a hands-on day with science galleries, demonstrations, and large-format exhibits.","opening_hours":"9:00 AM – 8:00 PM, daily","visitor_rules":["Children should remain with their group.","Follow exhibit safety instructions."],"facilities":["Food court","Parking","Accessible washrooms"],"directions_url":"https://maps.google.com/?q=Science+City+Kolkata","faqs":[("Is it suitable for children?","Yes. Many exhibits are designed for school-age visitors and families.")]},
]

# The frontend serves these supplied photographs from its public directory.
# Keeping the mapping next to the seeded attraction identity means every API
# response carries the same image URL for catalogue and detail screens.
LOCAL_IMAGE_URLS = {
    "visvesvaraya-museum": "/images/attractions/Visvesvaraya%20Museum.jpg",
    "bangalore-palace": "/images/attractions/Bangalore%20Palace.jpg",
    "national-museum": "/images/attractions/National%20Museum.jpeg",
    "csmvs-museum": "/images/attractions/CSMVS%20Museum.jpeg",
    "gateway-of-india": "/images/attractions/Gateway%20of%20India.jpg",
    "victoria-memorial": "/images/attractions/Victoria%20Memorial.jpeg",
    "lalbagh-botanical-garden": "/images/attractions/Lalbagh%20Botanical%20Garden.jpg",
    "karnataka-chitrakala-parishath": "/images/attractions/Karnataka%20Chitrakala%20Parishath.jpeg",
    "india-gate": "/images/attractions/India%20Gate.jpg",
    "qutub-minar": "/images/attractions/Qutub%20Minar.jpg",
    "national-gallery-modern-art": "/images/attractions/National%20Gallery%20of%20Modern%20Art.jpg",
    "elephanta-caves": "/images/attractions/Elephanta%20Caves.jpeg",
    "dr-bhau-daji-lad-museum": "/images/attractions/Dr%20Bhau%20Daji%20Lad%20Museum.jpg",
    "indian-museum": "/images/attractions/Indian%20Museum.jpg",
    "marble-palace": "/images/attractions/Marble%20Palace.jpg",
    "science-city-kolkata": "/images/attractions/Science%20City.jpg",
}

ALLOWED_CITIES = {"Bengaluru", "Delhi", "Kolkata", "Mumbai"}
ALLOWED_SLUGS = {entry["slug"] for entry in CATALOG}

SLOT_TIMES = ((time(10, 0), time(12, 0)), (time(12, 30), time(14, 30)), (time(15, 0), time(17, 0)))


def ensure_future_slots(session, attraction: Attraction) -> None:
    """Keep a rolling local-demo window of future slots without duplicating rows."""
    today = date.today()
    existing = {
        (slot.visit_date, slot.start_time)
        for slot in session.scalars(select(TimeSlot).where(TimeSlot.attraction_id == attraction.id, TimeSlot.visit_date >= today))
    }
    for day_offset in range(1, 15):
        visit_day = today + timedelta(days=day_offset)
        for start, end in SLOT_TIMES:
            if (visit_day, start) not in existing:
                session.add(TimeSlot(
                    attraction_id=attraction.id,
                    visit_date=visit_day,
                    start_time=start,
                    end_time=end,
                    capacity=40,
                    remaining_capacity=40,
                ))


def seed_catalog() -> None:
    """Create deterministic local development data once; production uses admin-managed data."""
    with SessionLocal() as session:
        settings = get_settings()
        for attraction in session.scalars(select(Attraction).where(Attraction.slug.not_in(ALLOWED_SLUGS), Attraction.is_published.is_(True))):
            attraction.is_published = False
        for catalog_entry in (item for item in CATALOG if item["city"] in ALLOWED_CITIES):
            entry = {**catalog_entry, "image_url": LOCAL_IMAGE_URLS[catalog_entry["slug"]]}
            attraction = session.scalar(select(Attraction).where(Attraction.slug == entry["slug"]))
            if not attraction:
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
                session.add(attraction)
                session.flush()
            else:
                for key, value in entry.items():
                    if key != "faqs":
                        setattr(attraction, key, value)
                attraction.is_published = True
            ensure_future_slots(session, attraction)
        if settings.demo_bootstrap_password:
            assigned_attraction = session.scalar(
                select(Attraction).where(Attraction.slug == settings.demo_staff_attraction_slug)
            )
            if not assigned_attraction:
                raise RuntimeError("DEMO_STAFF_ATTRACTION_SLUG must identify a seeded attraction.")
            demo_accounts = (
                (settings.demo_staff_email, "TixBee Demo Staff", "staff", assigned_attraction.id),
                (settings.demo_admin_email, "TixBee Demo Admin", "admin", None),
            )
            for email, full_name, role, assigned_attraction_id in demo_accounts:
                user = session.scalar(select(User).where(User.email == email.lower()))
                if not user:
                    user = User(
                        full_name=full_name,
                        email=email.lower(),
                        password_hash=hash_password(settings.demo_bootstrap_password),
                    )
                    session.add(user)
                user.role = role
                user.assigned_attraction_id = assigned_attraction_id
        session.commit()
