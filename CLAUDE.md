# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hi-Tom-AI is an AI e-commerce content generation platform that generates images and videos using AI services (T8Star, ModelScope). The architecture separates AI API calls (handled by Vercel Functions) from business logic (handled by FastAPI backend).

## Development Commands

```bash
# Backend (FastAPI)
cd backend && pip install -r requirements.txt
cd backend && uvicorn main:app --reload --port 8000

# Vercel API (AI proxy)
cd vercel-api && npm install
cd vercel-api && npm run dev           # vercel dev

# User Frontend (Vue 3)
cd user-web && npm install
cd user-web && npm run dev             # port 8080

# Admin Frontend (Vue 3)
cd admin-web && npm install
cd admin-web && npm run dev            # port 8081
```

## Architecture

```
User Browser
    │
    ├── AI requests ──────────→ Vercel Functions ──→ AI Provider (T8Star)
    │   (image/video gen)         (stores API keys)
    │
    └── Business requests ─────→ FastAPI Backend
        (auth, points, logs)       (SQLite database)
```

### Key Components

- **backend/**: FastAPI with SQLAlchemy ORM, handles user auth, points system, model configuration, pricing
- **vercel-api/**: Serverless functions that proxy AI requests, keeping API keys secure on the server side
- **user-web/**: User-facing Vue 3 app with Element Plus
- **admin-web/**: Admin dashboard for model management and system configuration

## Key Patterns

### Provider Mapper Pattern

Different AI models have different API parameter formats. The `vercel-api/lib/provider-mapper.js` handles parameter transformation:

- `PARAM_MAPPINGS`: Field name mappings (e.g., `ratio` → `aspect_ratio` for Sora-2)
- `STATUS_MAPPINGS`: Normalize different status codes to standard `SUCCESS/FAILURE/PROCESSING/PENDING`
- `mapRequestParams()`: Transform frontend params to API-specific format

### Points Reserve/Confirm/Refund

The points system uses a 3-step deduction mechanism to prevent double-charging:

1. **Reserve**: Pre-deduct points, returns `deduction_id` with 600s expiry
2. **Confirm**: Mark as consumed after successful generation
3. **Refund**: Return points if generation fails

See `backend/crud.py` functions: `reserve_points()`, `confirm_points()`, `refund_points()`

### Model Configuration

Models are configured in `ai_models` table with flexible pricing via `model_pricing` table:
- `billing_mode`: `per_use` or `duration`
- Pricing rules can add costs for duration, resolution, aspect ratio
- Frontend options configured via `frontend_config` JSON

## Environment Variables

**Vercel (vercel-api/.env):**
```
T8STAR_API_KEY=sk-xxx
MODELSCOPE_API_KEY=sk-xxx
BACKEND_URL=https://your-server.com
```

**Backend:** No special env vars needed; SQLite database created automatically.

## API Endpoints

**Public APIs:**
- `POST /auth/register`, `POST /auth/token` - User auth
- `GET /api/models` - List enabled models
- `POST /api/calculate-cost` - Calculate generation cost
- `POST /api/points/reserve|confirm|refund` - Points management

**Admin APIs (require admin role):**
- `GET/POST/PUT/DELETE /admin/models` - Model CRUD
- `GET/PUT /admin/config` - System configuration

**Vercel Functions:**
- `POST /api/ai/generate-image` - Image generation proxy
- `POST /api/ai/generate-video` - Video generation proxy
- `GET /api/ai/video-status` - Query video generation status

## Progress Tracking

Development progress tracked in `feature_list.json` (completed items have `"passes": true`). Current phase: frontend development (items 11-16 pending).