# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hi-Tom-AI is an AI e-commerce content generation platform that generates images and videos using AI services (T8Star, ModelScope). The architecture separates AI API calls (handled by Tencent Cloud Functions) from business logic (handled by FastAPI backend).

## Development Commands

```bash
# Backend (FastAPI)
cd backend && pip install -r requirements.txt
cd backend && python init_db.py              # 初始化数据库
cd backend && uvicorn main:app --reload --port 8000

# User Frontend (Vue 3)
cd user-web && npm install && npm run dev   # port 8080

# Admin Frontend (Vue 3)
cd admin-web && npm install && npm run dev  # port 8081
```

## Architecture

```
User Browser
    │
    ├── AI requests ──────────→ Tencent Cloud Functions ──→ AI Provider
    │   (image/video gen)         (API key pool)              (T8Star/ModelScope)
    │
    └── Business requests ─────→ FastAPI Backend
        (auth, points, logs)       (SQLite database)
```

### Key Components

- **backend/**: FastAPI with SQLAlchemy ORM, handles user auth, points system, model configuration, pricing
- **tencent-function/**: Single Tencent Cloud Function proxy that routes requests to AI providers based on placeholder keys
- **tencent-api-web/**: Web function format code for Tencent Cloud Functions deployment
- **user-web/**: User-facing Vue 3 app with Element Plus
- **admin-web/**: Admin dashboard for model management and system configuration

## Key Patterns

### API Key Pool Pattern (tencent-function/)

The cloud function uses a key pool with random selection:
- `KEY_POOL.modelscope`: Array of ModelScope API keys
- `KEY_POOL.t8star`: Array of T8Star API keys
- Frontend sends requests with placeholder keys (`MODELSCOPE_API_KEY` or `T8STAR_API_KEY`)
- Cloud function replaces placeholders with real keys from the pool
- Routes to `api.modelscope.cn` or `api.t8star.com` based on placeholder type

**Note:** The frontend (`user-web/src/api/index.js`) currently references `VERCEL_URL`. This needs to be updated to point to the Tencent Cloud Function URL once deployed.

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

**Tencent Cloud Functions:**
```
# Key Pool (configured in tencent-function/index.js)
KEY_POOL.modelscope = ["sk-xxx-01", "sk-xxx-02", ...]
KEY_POOL.t8star = ["sk-xxx-01", "sk-xxx-02", ...]
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

**Tencent Cloud Functions:**
- Single proxy endpoint that routes to ModelScope or T8Star based on placeholder key in request

## Deployment

See `tencent-api-web/DEPLOYMENT_GUIDE.md` for Tencent Cloud Functions deployment instructions.

## Progress Tracking

All 20 features completed. See `feature_list.json` for details.

## Current Status

- **Backend**: Fully functional (FastAPI + SQLite)
- **Frontend**: User-web and Admin-web complete
- **AI Proxy**: Migrating from Vercel to Tencent Cloud Functions
  - `tencent-function/index.js`: Simple proxy with key pool pattern (created by Gemini)
  - `tencent-api-web/`: Contains deployment guide and detailed function implementations
  - Frontend still points to old Vercel URL - needs update after Tencent deployment