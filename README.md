# TixBee v1

PRD-led ticket-booking application for cultural attractions. The v1 stack is Next.js, FastAPI, PostgreSQL, Alembic, Redis, Gemini, Razorpay Test Mode, Docker Compose, and role-based JWT authentication.

## Current milestone

FastAPI, PostgreSQL, Alembic, Docker Compose, and the public attraction API foundation.

## Local development

Copy `.env.example` to `.env`, then run `docker compose up --build`.

- Frontend: `http://localhost:3001`
- API docs: `http://localhost:8000/docs`

## Local Review Demo Accounts

To demonstrate staff check-in and administrator slot controls locally, set a strong
`DEMO_BOOTSTRAP_PASSWORD` in `.env` before the first startup. TixBee creates one
staff account and one admin account only when this local-only setting is present.
Use the configured `DEMO_STAFF_EMAIL` or `DEMO_ADMIN_EMAIL` to sign in at
`/staff`. Do not set this option in a deployed environment.
