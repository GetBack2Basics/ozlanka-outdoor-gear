# OzLanka Outdoor Gear MVP

## Layout

- `backend/` FastAPI, PostgreSQL, Celery, Playwright scraper
- `frontend/` Next.js 15 App Router, Tailwind, shadcn-style UI
- `docs/nginx-proxy-manager.md` host proxy setup

## Run

1. Copy `.env.example` to `.env` and set secrets.
2. Start the stack with Docker Compose.
3. Point Nginx Proxy Manager at `127.0.0.1:3000`.
4. Log in with the seeded admin credentials from `.env`.

## Notes

- Backend, Redis, and PostgreSQL stay internal to Docker.
- Use a different `FRONTEND_HOST_PORT` for every project folder on the same VPS.
