# TixBee

TixBee is a full-stack ticket-booking application for museums, heritage sites,
galleries, and other cultural attractions. It gives visitors one flow for
discovering a venue, selecting a timed visit, reserving capacity, completing a
local payment simulation, receiving a signed QR ticket, and checking in at the
venue. The application also gives staff a protected ticket desk and gives
administrators protected controls for visit-slot capacity.

The project is designed as a modular monolith: one Next.js frontend, one FastAPI
application, and PostgreSQL as the authoritative record for booking state.

## Implemented capabilities

### Visitor and customer journey

- Browse published attractions by city, category, or name.
- View attraction details, facilities, visitor rules, FAQs, ticket types, and
  available timed slots.
- Register and sign in with email and password.
- Create a backend-priced reservation with a ten-minute capacity hold.
- Complete a no-money local payment simulation that confirms the booking.
- Receive a unique booking reference and signed QR ticket.
- View booking history and display the QR ticket.
- Cancel an unpaid held reservation and restore its reserved capacity.

### Venue operations

- Authenticate staff and administrator users with role-protected API endpoints.
- View issued, redeemed, and confirmed-booking totals.
- Redeem a ticket exactly once. A repeat redemption returns a conflict response.
- Let administrators view visit slots, close or reopen slots, and change a
  slot's capacity without dropping below already reserved places.

### Reliability and security controls

- Bcrypt password hashing and signed JWT sessions.
- Backend role checks for customer, staff, and administrator operations.
- Row-level locking for booking holds, staff redemption, and capacity updates.
- Server-side price calculation and immutable booking-item price snapshots.
- PostgreSQL persistence for users, attractions, slots, bookings, payments,
  tickets, and chat messages.
- Alembic migrations for schema versioning.
- Docker Compose for repeatable local services.

## Current scope boundaries

TixBee includes configuration fields and module boundaries for Gemini, Razorpay,
SMTP, and Redis. The locally demonstrated workflow intentionally uses the
in-process payment simulator instead of a live Razorpay order/webhook flow.
Live Gemini responses, payment webhooks, refunds, email-provider delivery, and
full attraction-content administration are future extensions rather than
completed features. No real money is collected.

## Technology stack

| Area | Technology |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, Pydantic |
| Data | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Authentication | Bcrypt, JWT bearer sessions, role-based authorization |
| Ticketing | Signed JWT QR payloads, `qrcode` SVG generation |
| Local services | Docker Compose, PostgreSQL, Redis |
| Optional integrations | Gemini API, Razorpay Test Mode, SMTP |
| Quality tooling | Pytest, Next.js production build, FastAPI OpenAPI docs |

## Architecture

```text
Browser
  │
  ▼
Next.js frontend (port 3001)
  │  REST + bearer token
  ▼
FastAPI application (port 8000)
  ├── Authentication and roles
  ├── Attraction catalog and slots
  ├── Booking holds and price snapshots
  ├── Demo payment and QR tickets
  ├── Staff redemption and admin operations
  └── Optional concierge integration
  │
  ▼
PostgreSQL (authoritative records)     Redis (reserved for short-lived state)
```

### Backend modules

```text
backend/app/
├── core/        # configuration, database session, JWT and password security
├── models/      # SQLAlchemy domain entities
├── routers/     # HTTP endpoints grouped by capability
├── schemas/     # request and response validation models
└── services/    # catalog seeding, email adapter, concierge adapter
```

### Core data model

| Entity | Responsibility |
| --- | --- |
| `users` | Customer, staff, and administrator accounts |
| `attractions` | Published venue information |
| `time_slots` | Visit time, total capacity, and remaining capacity |
| `ticket_types` | Adult, student, and child ticket pricing |
| `bookings` and `booking_items` | Reservation status and preserved price snapshot |
| `payments` | Payment-provider or local-demo reference and status |
| `tickets` | Signed QR value, ticket status, and redemption record |
| `chat_messages` | Scoped concierge conversation history |

## Booking state flow

```text
Customer selects tickets
        │
        ▼
HOLD ── local demo payment ──► CONFIRMED ──► QR ticket ISSUED
  │                                                   │
  └── cancel unpaid reservation ──► CANCELLED         └── staff redemption ──► REDEEMED
```

The booking route locks the selected slot before it calculates remaining
capacity and creates the hold. Cancellation locks the same slot before it
returns capacity. Staff redemption locks the ticket before it changes its state.

## Quick start

### Prerequisites

- Docker Desktop with the Linux container engine running
- Git

### Configure the environment

Create a local `.env` file from the sample:

```powershell
Copy-Item .env.example .env
```

For the staff and administrator demo, set a strong local-only value in `.env`:

```env
DEMO_BOOTSTRAP_PASSWORD=choose-a-strong-demo-password
DEMO_STAFF_EMAIL=staff@tixbee.local
DEMO_ADMIN_EMAIL=admin@tixbee.local
```

The bootstrap accounts are created only when `DEMO_BOOTSTRAP_PASSWORD` is set.
Keep this setting out of deployed environments and never commit `.env`.

### Start the application

```powershell
docker compose up --build
```

Open these local endpoints:

| Service | Address |
| --- | --- |
| Customer application | http://localhost:3001 |
| API health check | http://localhost:8000/health |
| Interactive API documentation | http://localhost:8000/docs |
| Staff and admin operations | http://localhost:3001/operations |

Stop the stack with:

```powershell
docker compose down
```

To reset local database data completely, use `docker compose down -v`. This
removes the Docker volume containing PostgreSQL data.

## Demo walkthrough

1. Open the customer application and choose an attraction.
2. Pick an available date and time, then select ticket quantities.
3. Create a customer account, reserve the visit, and complete the demo payment.
4. Open **My bookings** to display the issued QR ticket.
5. Sign in at `/operations` with `staff@tixbee.local` and the configured demo
   password. Enter the ticket code and redeem it.
6. Submit the same ticket code a second time to demonstrate one-time admission.
7. Sign in as `admin@tixbee.local` to show slot capacity and open/close controls.

## API overview

All application endpoints are prefixed with `/api/v1`, except `/health` and
`/docs`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/auth/register` | Create a customer account and JWT session |
| `POST` | `/auth/login` | Sign in and receive a JWT session |
| `GET` | `/attractions` | List published attractions with filters |
| `GET` | `/attractions/{id}` | Read full attraction details |
| `GET` | `/attractions/{id}/slots` | Read future available slots |
| `POST` | `/bookings` | Create a locked, priced capacity hold |
| `POST` | `/bookings/{id}/demo-pay` | Confirm a held booking in local demo mode |
| `POST` | `/bookings/{id}/cancel` | Cancel an unpaid hold and restore capacity |
| `GET` | `/me/bookings` | Read the authenticated customer's bookings |
| `GET` | `/tickets/{code}/qr` | Render the customer's QR ticket as SVG |
| `POST` | `/operations/tickets/{code}/redeem` | Redeem a ticket as staff or admin |
| `GET` | `/operations/summary` | Read protected ticket-desk counts |
| `GET` | `/operations/slots` | Read slots as an administrator |
| `PATCH` | `/operations/slots/{id}` | Update slot capacity or active state as an administrator |

Use the API documentation at `/docs` for request shapes, response schemas, and
interactive testing.

## Development commands

### Frontend build

```powershell
cd frontend
npm run build
```

### Backend syntax check

```powershell
python -m compileall backend/app
```

### Docker rebuild after dependency changes

```powershell
docker compose up --build -d api frontend
```

## Repository layout

```text
.
├── backend/                 # FastAPI application and Alembic migrations
├── frontend/                # Next.js user and operations interfaces
├── docker-compose.yml       # Local frontend, API, PostgreSQL, and Redis stack
├── Dockerfile.api           # Backend container image
├── Dockerfile.frontend      # Frontend container image
├── .env.example             # Safe configuration template
└── PRD.md                   # Product requirements and planned future scope
```

## Security notes

- `.env` is ignored by Git. Do not commit passwords, JWT secrets, API keys, or
  provider credentials.
- Replace the development JWT secret before any deployment.
- The demo account bootstrap exists only for local academic demonstration.
- The local payment simulator must not be represented as a real payment gateway.

## License

This repository is an academic project. Add a license before using it as a
public production product.
