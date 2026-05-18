# AI Social Media Automation Platform

Full-stack AI-powered social media automation platform for managing content across **Instagram**, **YouTube**, **TikTok**, **Facebook**, and **Twitter/X**.

## Features

- **AI Content Generator** — Generate posts, captions, hashtags using GPT-4o
- **AI Image Generator** — Create images with DALL-E 3
- **Auto Scheduler** — Schedule and automate content publishing
- **Live Streaming 24/7** — Multi-platform RTMP streaming with FFmpeg
- **Multi-Account Manager** — Manage multiple accounts per platform
- **Analytics Dashboard** — Track followers, engagement, impressions
- **Video Generator** — Create videos from images/text with FFmpeg
- **Caption AI & Hashtag AI** — Platform-optimized captions and hashtags
- **Content Queue** — Manage content pipeline with status tracking
- **Webhooks** — Event-driven notifications for all actions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, FastAPI, Celery, Redis, PostgreSQL |
| **Frontend** | React, TypeScript, Tailwind CSS, Vite |
| **AI** | OpenAI GPT-4o, DALL-E 3, Whisper |
| **Video** | FFmpeg, RTMP streaming |
| **Deploy** | Docker, Docker Compose |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) OpenAI API key for AI features

### Run with Docker

```bash
# Clone the repository
git clone https://github.com/Satrioadi017/music-video-compiler.git
cd music-video-compiler

# Copy environment file
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Development Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Celery Worker:**
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

**Celery Beat (Scheduler):**
```bash
cd backend
celery -A app.tasks.celery_app beat --loglevel=info
```

## Architecture

```
├── backend/
│   ├── app/
│   │   ├── api/              # API routes (auth, accounts, content, etc.)
│   │   ├── models/           # SQLAlchemy database models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic & platform adapters
│   │   │   └── platform_adapters/  # Instagram, YouTube, TikTok, Facebook, Twitter
│   │   ├── tasks/            # Celery async tasks
│   │   ├── middleware/       # Auth & rate limiting
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Settings & environment variables
│   │   └── database.py       # Database connection
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API client
│   │   ├── hooks/            # Custom React hooks
│   │   ├── types/            # TypeScript types
│   │   └── styles/           # Tailwind CSS
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Get current user |
| GET/POST | `/api/v1/accounts/` | List/create social accounts |
| GET/POST | `/api/v1/content/` | List/create content |
| POST | `/api/v1/content/{id}/publish` | Publish content |
| POST | `/api/v1/content/ai/generate` | AI content generation |
| POST | `/api/v1/content/ai/hashtags` | AI hashtag generation |
| POST | `/api/v1/content/ai/image` | AI image generation |
| POST | `/api/v1/content/ai/caption` | AI caption generation |
| GET/POST | `/api/v1/schedules/` | List/create schedules |
| GET | `/api/v1/analytics/summary` | Analytics summary |
| GET/POST | `/api/v1/streams/` | List/create live streams |
| POST | `/api/v1/streams/{id}/action` | Start/stop/restart stream |
| GET/POST | `/api/v1/webhooks/` | List/create webhooks |

## Platform Configuration

Each platform requires OAuth credentials. Set them in your `.env` file:

- **Instagram**: Graph API with long-lived tokens
- **YouTube**: Google OAuth 2.0 with YouTube Data API v3
- **TikTok**: TikTok Login Kit + Content Posting API
- **Facebook**: Facebook Graph API with Page management
- **Twitter/X**: OAuth 2.0 with Tweet write permissions

## License

MIT License

---

**Dibuat oleh:** Satrio Adi Wibowo
**GitHub:** https://github.com/Satrioadi017/music-video-compiler

---

## Music Video Compiler (Legacy)

The original Music Video Compiler application is still available in the `music_video_compiler/` directory.
See the [original documentation](music_video_compiler/README.md) for details.
