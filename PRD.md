# TixBee v1 — Product Requirements Document

## 1. Product summary

TixBee is a web-based ticket-booking platform for heritage sites, museums, art galleries, and cultural attractions.

Users can browse attractions, select a visit date and time slot, book tickets, make a sandbox payment, and receive a QR ticket. A Gemini-powered chatbot helps users understand an attraction and complete the booking flow.

The chatbot is a guide—not an autonomous agent. It answers booking-related questions and suggests or prefills booking details, but it never creates bookings, changes inventory, or processes payments itself.

## 2. Product goal

Build and deploy a polished, full-stack portfolio application that demonstrates:

- Modern frontend development
- REST API and database design
- Transaction-safe booking logic
- AI integration with practical boundaries
- Authentication and role-based access
- Payment webhook handling
- Docker, testing, CI/CD, and deployment

## 3. Target users

| User | Main need |
|---|---|
| Visitor | Discover attractions and book tickets easily |
| Registered customer | View and manage booked tickets |
| Admin | Manage attraction data, pricing, slots, and bookings |
| Venue staff | Validate QR tickets at entry |

## 4. Locked MVP scope

### Customer features

1. Public catalog

- Landing page with featured attractions.
- Browse attractions by city.
- Search by attraction name.
- Filter by city and category: museum, heritage site, gallery.
- Responsive mobile-first design.

2. Attraction detail page

Each attraction must display:

- Name, city, category, image, and description
- Opening hours
- Visitor rules and facilities
- Directions/location link
- Ticket types and pricing
- Available visit dates and time slots
- Frequently asked questions
- “Book now” button
- Contextual chatbot panel

3. Booking flow

The customer flow is:

`Select attraction → select date → select slot → choose tickets → enter visitor details → pay → receive ticket`

Supported ticket types:

- Adult
- Student
- Child

Booking rules:

- A user cannot book more tickets than available capacity.
- A slot is temporarily held for 10 minutes once the user enters checkout.
- Price is calculated by backend logic only.
- The booking stores a price snapshot so later price edits do not affect old tickets.
- A successful payment confirms the booking.
- Expired or failed payments release the held capacity.

4. Payment

- Integrate Razorpay in Test Mode.
- Support the existing simulated UPI-style experience during development if needed.
- Handle payment confirmation through a verified webhook.
- Avoid real-money payments in v1.
- Prevent duplicate payment events from generating duplicate tickets.

5. Ticket and confirmation

After successful payment:

- Show booking confirmation page.
- Generate a unique booking reference.
- Generate a signed QR ticket.
- Send confirmation email.
- Allow the user to view their ticket from “My Bookings.”

6. Authentication

- Public users may browse attractions.
- A user must create an account or sign in before payment.
- Use email/password authentication with JWT-based sessions.
- Roles: `customer`, `admin`, `staff`.

7. My Bookings

Customers can:

- View current and past bookings.
- Open/download a QR ticket.
- View booking status.
- Cancel a booking only before the configured cancellation deadline.

8. Admin dashboard

Admins can:

- Create, edit, publish, or disable attractions.
- Add images, descriptions, visitor rules, and FAQs.
- Create date slots and configure capacity.
- Create ticket types and prices.
- View bookings and payment status.
- Cancel a booking manually.

9. Staff check-in

Staff can:

- Scan or enter a QR ticket code.
- See whether a ticket is valid.
- Mark a ticket as redeemed.
- Prevent a redeemed ticket from being used again.

## 5. Chatbot scope

The chatbot exists on attraction pages and the booking flow.

It can answer:

- Visiting hours
- Ticket prices
- Student/child ticket eligibility
- Facilities and accessibility
- Photography, food, baggage, and visitor policies
- Directions and location
- Booking instructions
- Available slots, if the backend provides that data

It can guide users with messages such as:

> “For two adults this Sunday, choose the 11:00 AM slot. I’ve prefilled the ticket quantities for you.”

It may return structured suggestions:

```json
{
  "answer": "The museum is open from 10 AM to 6 PM.",
  "suggested_action": "prefill_booking",
  "prefill": {
    "adult_tickets": 2,
    "visit_date": "2026-09-13"
  }
}
```

The frontend decides whether to apply the suggestion.

### Explicit AI restrictions

The chatbot must not:

- Create or confirm bookings
- Modify availability or inventory
- Start or verify payments
- Access raw database credentials
- Run SQL queries
- Invent prices, availability, policies, or operating hours
- Answer unrelated general-purpose questions
- Use RAG, vector databases, LangGraph, agents, or multi-agent workflows

The backend will pass the selected attraction’s curated database information directly to Gemini as context.

## 6. Non-goals for v1

These are deliberately out of scope:

- Real payment collection
- RAG/vector search
- Voice assistant
- Native mobile app
- Seat-selection maps
- Dynamic pricing
- Coupons and loyalty points
- Multi-vendor onboarding
- Multi-language UI
- Recommendation engine
- Microservices, Kubernetes, Kafka, or complex cloud infrastructure

## 7. Technical architecture

### Locked stack

| Area | Technology |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python |
| Database | PostgreSQL |
| ORM/migrations | SQLAlchemy, Alembic |
| AI | Gemini API |
| Authentication | JWT, password hashing, role-based authorization |
| Payments | Razorpay Test Mode |
| Email | SMTP or Resend |
| QR tickets | Signed QR token generated by backend |
| Local environment | Docker Compose |
| Backend tests | Pytest |
| Frontend/browser tests | Playwright |
| CI/CD | GitHub Actions |
| Deployment | Vercel + Render/Railway + managed PostgreSQL |

### Backend modules

```text
api/
  auth/
  attractions/
  slots/
  bookings/
  payments/
  tickets/
  chat/
  admin/
  staff/
  common/
```

This remains a single FastAPI application with clean modules. No microservices.

## 8. Core database entities

| Entity | Purpose |
|---|---|
| `users` | Customer, admin, and staff accounts |
| `attractions` | Museum, gallery, or heritage-site details |
| `attraction_faqs` | Curated chatbot-answerable content |
| `time_slots` | Visit dates, start times, capacity, remaining capacity |
| `ticket_types` | Adult, student, child pricing |
| `bookings` | Main booking record |
| `booking_items` | Ticket quantities and price snapshot |
| `payments` | Razorpay payment status and provider reference |
| `tickets` | QR token, ticket status, redemption timestamp |
| `chat_messages` | Basic conversation history per user/session |

## 9. Booking state model

```text
DRAFT
  ↓
HOLD_ACTIVE
  ↓
PAYMENT_PENDING
  ↓
CONFIRMED
  ↓
CANCELLED / EXPIRED
```

A booking becomes `CONFIRMED` only after the payment webhook is successfully verified.

## 10. Essential API endpoints

```text
GET    /attractions
GET    /attractions/{id}
GET    /attractions/{id}/slots

POST   /auth/register
POST   /auth/login

POST   /bookings/quote
POST   /bookings
GET    /bookings/me
GET    /bookings/{id}
POST   /bookings/{id}/cancel

POST   /payments/create-order
POST   /payments/webhook

POST   /chat/message

POST   /staff/tickets/validate
POST   /staff/tickets/redeem

POST   /admin/attractions
PATCH  /admin/attractions/{id}
POST   /admin/slots
PATCH  /admin/slots/{id}
```

## 11. Quality requirements

Before v1 is considered complete:

- Users can complete the booking journey on mobile and desktop.
- Slot capacity cannot become negative.
- Two simultaneous bookings cannot oversell the final ticket.
- Duplicate payment webhooks do not create duplicate tickets.
- QR tickets cannot be redeemed twice.
- Backend has tests for pricing, booking state transitions, payment verification, cancellation, and ticket validation.
- Playwright covers registration, booking, payment simulation, confirmation, and ticket access.
- API documentation is available at `/docs`.
- Docker Compose starts the frontend, backend, and database locally.
- A live deployment and public GitHub README exist.
- README includes architecture, setup steps, screenshots, API examples, and a demo video link.

## 12. Delivery order

1. Set up Next.js, FastAPI, PostgreSQL, Docker Compose, and CI.
2. Build attraction catalog and detail pages.
3. Build slots, ticket pricing, and booking hold logic.
4. Add authentication and My Bookings.
5. Add Razorpay Test Mode and QR tickets.
6. Add admin dashboard and staff check-in.
7. Add Gemini chatbot.
8. Test, deploy, document, and record demo.

This is the locked TixBee v1: a real ticket-booking application first, with AI as a focused support feature.