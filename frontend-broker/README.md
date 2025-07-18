# Frankie Frontend (frontend-broker)

## Overview
React/TypeScript dashboard for brokers and admins. Minimal, responsive, and focused on urgent loan files.

## Setup
```bash
cd frontend-broker
npm install
cp .env.example .env
npm start
```

## Environment Variables
See `.env.example` for required variables (API URL, etc).

## Scripts
- `npm start` — Run dev server
- `npm run build` — Production build
- `npm run lint` — Lint code

## Troubleshooting
- **Port in use:** Change `PORT` in `.env`
- **API errors:** Ensure backend is running and CORS is allowed

## Features
- Animated tooltips, toast notifications, error boundary
- Soft delete, status highlighting, mobile-friendly

## Deployment
Deployed to Vercel. See `/vercel.json` for config.
