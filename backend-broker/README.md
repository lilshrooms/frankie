# Frankie Backend (backend-broker)

## Overview
FastAPI backend for email ingestion, document parsing, RAG, and admin API.

## Setup
```bash
cd backend-broker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

## Environment Variables
See `.env.example` for Gmail, Gemini, and DB credentials.

## API Docs
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Features
- Email fetching, PDF/image parsing, RAG, YAML criteria
- Soft delete, audit logging

## Testing
```bash
pytest
```

## Deployment
Deploy to cloud host (e.g., Render, AWS, GCP). 