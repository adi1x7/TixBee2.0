# TixBee 2.0

TixBee is a full-stack ticket-booking application for museums, heritage sites, galleries, and cultural attractions. Built as an academic project, it demonstrates attraction discovery, timed-slot booking, QR ticket delivery, booking management, and venue operations.

> **Academic-demo notice:** The UPI QR checkout is an amount-specific demonstration flow. It does not verify a real payment and must not be used for commercial ticket sales without a verified payment-provider integration.

## Features

### Customer booking journey

- Browse 16 attractions across Bengaluru, Delhi, Kolkata, and Mumbai.
- Search and filter by city, category, or attraction name.
- View attraction images, descriptions, opening hours, facilities, visitor rules, FAQs, ticket prices, and visit slots.
- Register, sign in, sign out, and reset a forgotten password.
- Reserve capacity using backend-calculated pricing and a 10-minute booking hold.
- Display an amount-specific UPI QR in the checkout demonstration.
- Receive a signed QR ticket and optional confirmation email with visit details, ticket quantities, amount, ticket ID, and QR code.
- Access booking history and QR passes through **My bookings**.
- Cancel an eligible confirmed booking up to 24 hours before the visit; the application records a 50% refund as pending and sends an optional cancellation email.

### Operations

- Role-protected customer, staff, and administrator accounts.
- Staff access limited to one assigned attraction; administrator access across all sites.
- Validate signed QR tickets and redeem a ticket only once.
- View issued, redeemed, and confirmed-booking activity metrics.
- Manage visit-slot capacity and availability grouped by attraction and date.
- View a role-scoped customer directory with account and booking summaries.

### TixBee Concierge

- Gemini-powered assistance for attraction discovery, ticket guidance, facilities, rules, FAQs, and visit planning.
- Signed-in customer booking questions are answered directly from TixBee data, so private booking details are not sent to Gemini.
- Compact attraction/city context and a low-latency Gemini Flash model keep responses quick.

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, Pydantic |
| Data | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Authentication | Bcrypt, JWT bearer sessions, role-based access control |
| Ticketing | Signed JWT ticket payloads and SVG QR codes |
| AI | Google Gemini API (gemini-3.5-flash-lite) |
| Local runtime | Docker Compose, PostgreSQL, Redis |

## Architecture

~~~text
Browser
  |
  v
Next.js frontend :3001
  |
  | REST API + bearer token
  v
FastAPI backend :8000
  |- identity and password recovery
  |- attraction catalogue and slots
  |- booking holds and price snapshots
  |- UPI-QR demonstration checkout and tickets
  |- email, cancellation, operations, and Concierge
  |
  v
PostgreSQL : authoritative records
~~~

## Run locally

### Prerequisites

- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) with Linux containers enabled

### 1. Clone

~~~powershell
git clone https://github.com/adi1x7/TixBee2.0.git
cd TixBee2.0
~~~

### 2. Configure environment variables

Create a local configuration file:

~~~powershell
Copy-Item .env.example .env
~~~

At minimum, replace the placeholder secrets and configure local demo operations accounts:

~~~env
JWT_SECRET_KEY=replace-with-a-long-random-secret
TICKET_SIGNING_SECRET=replace-with-a-different-long-random-secret
DEMO_BOOTSTRAP_PASSWORD=choose-a-strong-demo-password
DEMO_STAFF_EMAIL=staff@tixbee-demo.com
DEMO_ADMIN_EMAIL=admin@tixbee-demo.com
DEMO_STAFF_ATTRACTION_SLUG=visvesvaraya-museum
~~~

Optional services:

- Set GEMINI_API_KEY to enable Concierge answers.
- Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM to send booking, reset, and cancellation emails.
- Set UPI_PAYEE_ID and UPI_PAYEE_NAME for the UPI QR demonstration.

Do not commit .env; it is already ignored by Git.

### 3. Start TixBee

~~~powershell
docker compose up --build
~~~

| Service | Address |
| --- | --- |
| Customer application | http://localhost:3001 |
| Customer login | http://localhost:3001/login |
| Password reset | http://localhost:3001/forgot-password |
| Staff and administrator desk | http://localhost:3001/operations |
| API health check | http://localhost:8000/health |
| Interactive API documentation | http://localhost:8000/docs |

Stop the stack:

~~~powershell
docker compose down
~~~

Remove local database data as well:

~~~powershell
docker compose down -v
~~~

## Demonstration walkthrough

1. Open the customer application and select an attraction.
2. Select a visit date, time slot, and ticket quantities.
3. Register or sign in, then create the reservation hold.
4. Select **Pay** to show the amount-specific UPI QR prompt.
5. Open **My bookings** to view the issued QR pass.
6. Sign in at /operations using the configured staff account and redeem the ticket.
7. Redeem the same ticket again to demonstrate one-time admission protection.
8. Sign in as the administrator to view all-site activity, slot controls, and the customer directory.

## Core API routes

Application endpoints use /api/v1, except /health and /docs.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | /auth/register | Create a customer account and session |
| POST | /auth/login | Sign in and receive a JWT session |
| POST | /auth/password-reset/request | Request a password reset |
| POST | /auth/password-reset/confirm | Confirm a password reset |
| GET | /attractions | List and filter published attractions |
| GET | /attractions/{id} | Read attraction details |
| GET | /attractions/{id}/slots | Read available future slots |
| POST | /bookings | Create a capacity hold |
| GET | /bookings/{id}/upi-qr | Generate an amount-specific UPI QR SVG |
| POST | /bookings/{id}/demo-pay | Complete the local demonstration flow |
| POST | /bookings/{id}/cancel-confirmed | Cancel an eligible confirmed booking |
| GET | /me/bookings | Read the signed-in customer's bookings |
| POST | /chat/messages | Send a Concierge message |
| POST | /operations/tickets/{code}/redeem | Validate and redeem a ticket |

## Repository layout

~~~text
.
|- backend/                       FastAPI application and Alembic migrations
|  '- app/                        Models, routers, schemas, and services
|- frontend/                      Next.js customer and operations interface
|  '- public/images/attractions/  Local attraction images
|- assets/                        Source attraction images
|- docker-compose.yml             Local service definition
|- Dockerfile.api                 Backend image
|- Dockerfile.frontend            Frontend image
|- .env.example                   Safe configuration template
|- PRD.md                         Product planning material
'- README.md                      Project documentation
~~~

## Development checks

~~~powershell
# Frontend lint and production build
cd frontend
npm run lint
npm run build

# From the repository root
python -m compileall backend/app
~~~

## Security and future-production notes

- Passwords use Bcrypt hashing; sessions use expiring JWT tokens.
- Protected APIs enforce roles, and staff ticket actions are restricted to their assigned site.
- QR ticket signatures are verified before redemption.
- The payment flow is intentionally a local academic demo, not a real payment-verification system.
- A production version should add verified payment webhooks, rate limits, background hold expiry, production secret management, backups, and formal accessibility/security testing.

## License

This is an academic project. Add an explicit license before using it in a production or commercial context.
