# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hi-Tom-AI is an AI e-commerce content generation platform that generates images and videos using AI services (T8Star, ModelScope). The architecture separates AI API calls (handled by Tencent Cloud Functions) from business logic (handled by FastAPI backend).

## Development Commands

```bash
# Backend (FastAPI)
cd backend && pip install -r requirements.txt
cd backend && python init_db.py              # Initialize database
cd backend && uvicorn main:app --reload --port 8000

# User Frontend (Vue 3)
cd user-web && npm install && npm run dev   # port 8080

# Admin Frontend (Vue 3)
cd admin-web && npm install && npm run dev  # port 8081
```

## Tech Stack

**Backend**: FastAPI 0.115 + SQLAlchemy 2.0 + SQLite + Pydantic 2.10
**Frontend**: Vue 3.5 + Vite 5.4 + Element Plus 2.8 + Pinia 2.2 + Axios
**Cloud**: Tencent Cloud Functions (Node.js 16)

## Default Credentials

- Admin: `admin` / `admin123`
- New user signup bonus: 10 points

## Architecture

```
User Browser
    │
    ├── AI requests ──────────→ Tencent Cloud Functions ──→ AI Provider
    │   (image/video/gen)         (API key pool)              (T8Star/ModelScope)
    │
    └── Business requests ─────→ FastAPI Backend
        (auth, points, logs)       (SQLite database)
```

**CRITICAL: All AI requests MUST go through Tencent Cloud Functions proxy. The backend NEVER directly calls AI providers.**

## Key Patterns

### API Key Pool Pattern

API Keys are stored ONLY in Tencent Cloud Function's `KEY_POOL` (`tencent-function/index.js`), never in database.

**Request flow:**
1. Frontend fetches `tencent_function_url` from backend via `GET /api/config/pricing-info`
2. Frontend sends request to cloud function with placeholder: `Authorization: Bearer MODELSCOPE_API_KEY`
3. Cloud function replaces placeholder with real key from `KEY_POOL`, forwards to AI provider
4. Cloud function returns response to frontend

**Placeholders:**
- `MODELSCOPE_API_KEY` → replaced with ModelScope key
- `T8STAR_API_KEY` → replaced with T8Star key

**Cloud Function Request Format:**
```javascript
// Frontend sends to cloud function:
{
  target_url: "https://ai.t8star.cn/v2/videos/generations",
  target_method: "POST",  // or "GET" for status queries
  model: "sora-2",
  prompt: "..."
}
// Headers: { Authorization: "Bearer T8STAR_API_KEY" }  // placeholder
```

### Points Reserve/Confirm/Refund

The points system uses a 3-step deduction mechanism:

1. **Reserve**: Pre-deduct points, returns `deduction_id` with 1200s expiry
2. **Confirm**: Mark as consumed after successful generation
3. **Refund**: Return points if generation fails

See `backend/crud.py`: `reserve_points()`, `confirm_points()`, `refund_points()`

### Model Configuration (config_schema)

Models are configured in `ai_models` table with `config_schema` JSON field. The `pricing_engine.py` and `payload_builder.py` in `backend/engines/` handle dynamic pricing and request construction.

Key config_schema sections:
- `pricing_rules`: Dynamic pricing (mode: static/dynamic/tiered)
- `request_mapping`: API request field mapping
- `response_mapping`: API response extraction rules
- `frontend_config`: UI options (dropdowns, sliders, etc.)

## Important Files

**Backend:**
- `backend/main.py`: FastAPI routes
- `backend/crud.py`: Core business logic
- `backend/models.py`: Database models
- `backend/engines/pricing_engine.py`: Dynamic pricing calculation
- `backend/engines/payload_builder.py`: API request construction

**Frontend:**
- `user-web/src/api/index.js`: Frontend AI calls with placeholder pattern
- `user-web/src/api/request.js`: Axios instance with auth interceptor
- `user-web/src/views/ai/`: AI generation pages (VideoTool.vue, ImageTool.vue)

**Cloud Function:**
- `tencent-function/index.js`: Cloud function with `KEY_POOL`

## Frontend Structure

**user-web/src/views/**:
- `ai/`: AI generation features (video, image, text/copywriting)
- `service/`: Service pages
- `shrimp/`: Feature-specific module (e.g., shrimp product workflow)

**admin-web/src/views/**:
- `Dashboard.vue`: Overview stats
- `ModelManage.vue`: AI model CRUD with config_schema editor
- `SystemConfig.vue`: System-wide settings (tencent_function_url, prompts, etc.)
- `ContentManage.vue`: Feature module configurations
- `UserManage.vue`: User management and points recharge

## Database Tables

Key tables (see `backend/models.py`):
- `users`: User accounts with points and role
- `ai_models`: AI model configurations with config_schema
- `point_reserves`: Pre-deducted points with expiry
- `point_logs`: Points transaction history
- `system_config`: Key-value system settings
- `content_configs`: JSON configurations for feature modules
- `generation_history`: User's generation history (video/image/text)