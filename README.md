# LearnLoop V1

LearnLoop is a responsive, adaptive learning platform that helps students optimize their study sessions. By dynamically adjusting the difficulty, format, and duration of activities based on real-time feedback, it creates a personalized and stress-free educational experience.

---

## The Core Problem

Many students struggle with rigid learning structures that do not adapt to their daily cognitive capacity. LearnLoop solves this by continuously adapting the learning path so that students remain in their zone of proximal development, reducing cognitive overload and preventing premature abandonment of study sessions.

---

## Key Features

- **Dynamic Recommendations:** Suggests the exact "next best step" based on immediate past performance.
- **Study Buddy Integration:** Contextual, RAG-backed AI tutor available on demand.
- **Privacy-First Analytics:** Deterministic telemetry for educational optimization — no behavioral surveillance.
- **Flexible Availability:** Activity durations scale to fit whatever time the student has available.
- **Local + Remote Modes:** Works in-browser locally or backed by a full PostgreSQL stack.

---

## System Architecture

```text
Railway Project
├── Frontend service (React/Vite — static build served via Railway)
├── Backend service  (FastAPI/Python — uvicorn)
└── PostgreSQL service
```

**Frontend:** React + TypeScript SPA (Vite). Captures interactions and renders learning materials.  
**Backend:** FastAPI Python service. Houses the Adaptive Decision Engine and REST API.  
**Database:** PostgreSQL — stores Student, LearningProfile, Activity, LearningEvent, StateSnapshot.  
**AI Layer:** Study Buddy — RAG module (Groq + LangChain + FAISS) for contextual help.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL |
| AI/RAG | LangChain, Groq, FAISS, HuggingFace Embeddings |
| Testing | Pytest (67 tests) |

---

## Repository Structure

```text
.
├── backend/
│   ├── app/             # FastAPI Application (API, Models, Services, Engine)
│   │   ├── api/         # Route handlers (students, activities, interactions, analytics, health)
│   │   ├── config.py    # Environment configuration
│   │   ├── db/          # SQLAlchemy session setup
│   │   ├── models/      # SQLAlchemy ORM models
│   │   ├── schemas/     # Pydantic request/response schemas
│   │   └── services/    # Business logic (adaptive engine, study buddy, student service)
│   ├── tests/           # Comprehensive Pytest suite (67 tests)
│   ├── .env.example     # Backend environment variable template
│   └── requirements.txt # Python dependencies
├── src/                 # React Frontend Application
│   ├── components/      # Reusable UI components (layout, ui primitives)
│   ├── hooks/           # State management (useRemoteAdaptiveLearning, useLearningController)
│   ├── pages/           # Page-level components (Dashboard, StudyPlan, FocusMode, etc.)
│   └── services/        # API client (api.ts)
├── .env.example         # Frontend environment variable template
├── .gitignore
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## Prerequisites

- Node.js v18+
- Python 3.9+
- PostgreSQL 13+

---

## Environment Variables

### Frontend (`/.env`)

Copy `.env.example` → `.env`:

```env
# "remote" = use FastAPI backend. "local" = run adaptive engine in-browser only.
VITE_ADAPTIVE_MODE=remote

# URL of the running FastAPI backend (no trailing slash)
VITE_API_BASE_URL=http://localhost:8000
```

> ⚠️ All `VITE_` variables are embedded into the frontend build. Do **not** place backend secrets here.

### Backend (`/backend/.env`)

Copy `backend/.env.example` → `backend/.env`:

```env
APP_ENV=pilot
DATABASE_URL=postgresql://user:password@localhost:5432/learnloop
GROQ_API_KEY=your_groq_api_key_here
ML_ENABLED=False
FRONTEND_ORIGIN=http://localhost:5173
```

> ⚠️ `GROQ_API_KEY` is backend-only. Never expose it to the frontend or version control.

---

## Local Development

### 1. PostgreSQL Setup

```sql
CREATE DATABASE learnloop;
```

### 2. Backend

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit backend/.env with your DATABASE_URL and GROQ_API_KEY

uvicorn app.main:app --reload
```

Tables are created automatically on first startup (`Base.metadata.create_all` — non-destructive, safe to call on restarts).

### 3. Frontend

```bash
# From repository root
cp .env.example .env
# Edit .env — set VITE_API_BASE_URL=http://localhost:8000

npm install
npm run dev
```

Application available at `http://localhost:5173`.

---

## Production Start Commands

**Backend:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Frontend (build + serve):**
```bash
npm run build
# Serve the dist/ directory via Railway's static hosting or a CDN
```

---

## Railway Deployment Guide

### Architecture on Railway

```text
Railway Project
├── Service: learnloop-backend   (root: ./backend, Python)
├── Service: learnloop-frontend  (root: ./, Node)
└── Service: PostgreSQL (managed plugin)
```

### Step-by-Step

**1. Create Railway project**
- Go to [railway.app](https://railway.app) → New Project.

**2. Add PostgreSQL**
- Inside the project → Add Service → Database → PostgreSQL.
- Railway provides `DATABASE_URL` automatically when linked to the backend service.

**3. Deploy the backend**
- Add Service → GitHub Repo → select this repository.
- Set **Root Directory** to `backend`.
- Railway auto-detects Python. Set the **Start Command** to:
  ```
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

**4. Configure backend environment variables**

In the backend service settings → Variables:

| Variable | Value |
|---|---|
| `APP_ENV` | `pilot` |
| `DATABASE_URL` | *(auto-injected by Railway when PostgreSQL is linked)* |
| `GROQ_API_KEY` | *(your Groq API key — add as a secret)* |
| `ML_ENABLED` | `False` |
| `FRONTEND_ORIGIN` | *(set after step 8 — the frontend public domain)* |

**5. Generate backend public domain**
- Railway Settings → Networking → Generate Domain.
- Note the URL: e.g. `https://learnloop-backend.up.railway.app`

**6. Deploy the frontend**
- Add another Service → GitHub Repo → same repository.
- Set **Root Directory** to `/` (repository root).
- Set the **Build Command** to: `npm run build`
- Set the **Start Command** to: *(leave blank or use `npx serve dist`)*.

**7. Configure frontend environment variables**

In the frontend service settings → Variables:

| Variable | Value |
|---|---|
| `VITE_ADAPTIVE_MODE` | `remote` |
| `VITE_API_BASE_URL` | `https://learnloop-backend.up.railway.app` *(your backend domain from step 5)* |

**8. Generate frontend public domain**
- Railway Settings → Networking → Generate Domain.
- Note the URL: e.g. `https://learnloop-frontend.up.railway.app`

**9. Update backend CORS**
- Go back to the **backend** service → Variables.
- Set `FRONTEND_ORIGIN` = `https://learnloop-frontend.up.railway.app`.
- Redeploy (Railway does this automatically on variable save).

**10. Verify health endpoint**
```
GET https://learnloop-backend.up.railway.app/health/ready
# Expected: {"status": "ready", "database": "connected"}
```

**11. Run complete live smoke test**
- Open the frontend URL in a browser.
- Complete the full student journey (see Testing section below).

---

## Database Schema

Schema is managed by SQLAlchemy `Base.metadata.create_all`. This is **safe for existing databases** — it creates tables if they don't exist and leaves existing tables untouched.

**There is no automated migration framework in V1.** Future schema changes should be applied manually via SQL migrations or by introducing Alembic.

Models:
- `students` — name, email, is_demo flag
- `learning_profiles` — adaptive state per student  
- `activities` — learning activity catalog
- `learning_events` — telemetry records
- `state_snapshots` — pre-session state capture for telemetry linkage
- `help_requests` — Study Buddy invocation records

---

## Health / Readiness Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health/` | Liveness — returns `{"status": "ok"}` |
| `GET /health/ready` | Readiness — tests PostgreSQL connectivity |

These endpoints do not expose secrets or PII.

---

## Testing

```bash
# Backend (67 tests)
pytest backend/tests

# Frontend build verification
npm run build
```

---

## ML Status

- **Production recommendation logic is strictly deterministic.**
- `ML_ENABLED=False` is enforced in `pilot` mode regardless of the environment variable value.
- Real student data is collected solely for future offline ML validation.
- Synthetic experiment results from earlier development phases are **not** evidence of real-world effectiveness.

---

## Data & Privacy

- No medical inferences or sensitive diagnostic labels are stored.
- Data points are strictly pedagogical (duration, self-reported difficulty, topic).
- Real student profiles (`is_demo=False`) are protected from demo reset scripts.
- `GROQ_API_KEY` is backend-only and never exposed to the frontend bundle.

---

## Limitations

- V1 uses lightweight `localStorage` session management (no OAuth/JWT). Suitable for pilot use.
- Study Buddy requires external Groq LLM availability. Graceful fallback is implemented.

---

## Deployment Checklist

```
[ ] GitHub repository clean (no .env files, no secrets committed)
[ ] PostgreSQL service created on Railway
[ ] Backend deployed with correct Root Directory (backend/)
[ ] Backend environment variables configured:
    [ ] APP_ENV=pilot
    [ ] DATABASE_URL (auto-linked from Railway PostgreSQL)
    [ ] GROQ_API_KEY (secret)
    [ ] ML_ENABLED=False
    [ ] FRONTEND_ORIGIN=(frontend domain, set after frontend deployment)
[ ] Backend health endpoint returns ready: GET /health/ready
[ ] Frontend deployed with correct Root Directory (/)
[ ] Frontend environment variables configured:
    [ ] VITE_ADAPTIVE_MODE=remote
    [ ] VITE_API_BASE_URL=(backend domain)
[ ] CORS verified: frontend can reach backend API
[ ] Remote mode enabled and functioning
[ ] ML confirmed disabled (ML_ENABLED=False)
[ ] GROQ_API_KEY secret configured (Study Buddy)
[ ] Real user smoke test completed end-to-end
[ ] PostgreSQL persistence verified (data survives backend restart)
```

---

## Future Roadmap

- **OAuth Integration:** Secure platform with robust user authentication.
- **ML Candidate Promotion:** Evaluate offline ML models against real V1 data corpus.
- **Expanded RAG:** Connect Study Buddy to broader, dynamically indexed knowledge bases.
- **Teacher Dashboard:** Aggregate classroom-level insights for educators.
- **Alembic Migrations:** Formal schema migration framework for production schema evolution.
