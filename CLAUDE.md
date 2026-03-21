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

### API Key Pool Pattern (tencent-function/)

API Keys are stored ONLY in Tencent Cloud Function's `KEY_POOL`, never in database:

```javascript
// tencent-function/index.js
const KEY_POOL = {
  modelscope: ["ms-xxx-01", "ms-xxx-02"],
  t8star: ["sk-xxx-01", "sk-xxx-02"]
};
```

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

// Cloud function replaces placeholder, removes target_url/target_method,
// forwards to AI provider, returns response directly
```

### Points Reserve/Confirm/Refund

The points system uses a 3-step deduction mechanism:

1. **Reserve**: Pre-deduct points, returns `deduction_id` with 600s expiry
2. **Confirm**: Mark as consumed after successful generation
3. **Refund**: Return points if generation fails

See `backend/crud.py`: `reserve_points()`, `confirm_points()`, `refund_points()`

### Model Configuration

Models are configured in `ai_models` table with `config_schema` JSON field containing:
- `pricing_rules`: Dynamic pricing configuration
- `request_mapping`: API request field mapping
- `response_mapping`: API response extraction rules
- `frontend_config`: UI options (dropdowns, sliders, etc.)

## Key Components

- **backend/**: FastAPI with SQLAlchemy ORM (user auth, points, model config, pricing)
- **backend/engines/**: `pricing_engine.py`, `payload_builder.py`
- **tencent-function/**: Cloud function proxy with `KEY_POOL`
- **user-web/**: Vue 3 app, calls AI via cloud function with placeholders
- **admin-web/**: Admin dashboard for model/system configuration

## API Endpoints

**Public APIs:**
- `POST /auth/register`, `POST /auth/token` - User auth
- `GET /api/models` - List enabled models
- `POST /api/calculate-cost` - Calculate generation cost (legacy)
- `POST /api/calculate-cost-dynamic` - Calculate cost using config_schema.pricing_rules
- `POST /api/build-payload` - Build API request payload (for testing)
- `POST /api/points/reserve|confirm|refund` - Points management
- `GET /api/config/pricing-info` - Get `tencent_function_url` and pricing info

**Admin APIs:**
- `GET/POST/PUT/DELETE /admin/models` - Model CRUD
- `GET/PUT /admin/config` - System configuration
- `POST /admin/recharge` - Recharge user points

**Frontend AI Calls (via Tencent Cloud Function):**
- ModelScope: `https://api-inference.modelscope.cn/v1/chat/completions`
- T8Star Video: `https://ai.t8star.cn/v2/videos/generations`
- T8Star Image: `https://ai.t8star.cn/v1/images/generations`

## Database Models

Key tables (see `backend/models.py`):
- `users`: User accounts with points and role
- `ai_models`: AI model configurations with config_schema
- `model_pricing`: Pricing rules (legacy, being replaced by config_schema)
- `point_reserves`: Pre-deducted points with 600s expiry
- `point_logs`: Points transaction history
- `system_config`: Key-value system settings
- `content_configs`: JSON configurations for feature modules (e.g., modal content, enabled flags)

## config_schema Structure (AIModel)

The `config_schema` JSON field in `ai_models` table uses this structure:
```json
{
  "pricing_rules": {
    "mode": "static|dynamic|tiered",
    "base_price": 10,
    "duration_pricing": {"5": 5, "10": 8},
    "resolution_pricing": {"720P": 0, "1080P": 5}
  },
  "request_mapping": {
    "static_params": {"model": "sora-2"},
    "dynamic_params": {"prompt": "prompt", "duration": "duration"},
    "prompt_template": "Generate a video: {prompt}"
  },
  "response_mapping": {
    "task_id_path": "data.task_id",
    "status_path": "data.status",
    "result_url_path": "data.output[0].url"
  },
  "frontend_config": {
    "duration_options": [5, 10, 15],
    "resolution_options": ["720P", "1080P"]
  }
}
```

## Important Files

- `backend/main.py`: FastAPI routes
- `backend/crud.py`: Core business logic
- `backend/models.py`: Database models
- `backend/schemas.py`: Pydantic request/response schemas
- `backend/engines/pricing_engine.py`: Dynamic pricing calculation
- `backend/engines/payload_builder.py`: API request construction from config_schema
- `backend/init_db.py`: Database initialization with default admin/models
- `user-web/src/api/index.js`: Frontend AI calls with placeholder pattern
- `user-web/src/api/request.js`: Axios instance with auth interceptor
- `user-web/src/views/ai/`: AI generation pages (video, image, text)
- `admin-web/src/views/`: Admin pages (Dashboard, ModelManage, SystemConfig, ContentManage)
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