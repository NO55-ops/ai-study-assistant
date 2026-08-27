# AI Study Assistant

A full-stack AI-powered study assistant that transforms learning material (PDFs, DOCX, PPTX, TXT) into personalized summaries, quizzes, flashcards, AI tutoring, and study plans. Built for high school, IB, AP, and SAT students.

## Tech Stack

- **Frontend**: React 19, React Router, Tailwind CSS, shadcn/ui, Lucide Icons, Sonner
- **Backend**: FastAPI (Python), Motor (async MongoDB driver), OpenAI SDK
- **Database**: MongoDB
- **Auth**: JWT (HTTP-only cookies) with bcrypt password hashing
- **Storage**: Local filesystem (configurable via `STORAGE_DIR`)
- **UI Design**: Neo-Brutalist Soft (pastel palette + hard shadows + solid borders)

## Project Structure

```
.
├── backend/
│   ├── server.py            # FastAPI app, all API routes, models, LLM helpers
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Backend env template
│   └── storage/             # (auto-created) Local file uploads
│
├── frontend/
│   ├── src/
│   │   ├── App.js           # Router + global providers
│   │   ├── index.css        # CSS variables (theming, dark mode)
│   │   ├── components/      # NotesWidget, Navbar, ProtectedRoute
│   │   ├── context/         # AuthContext, ThemeContext
│   │   ├── pages/           # Login, Dashboard, Upload, Documents, Tutor, Quiz, Flashcards, Settings, Notes
│   │   └── services/api.js  # Axios client + typed service methods
│   ├── package.json
│   └── .env.example         # Frontend env template
│
└── README.md
```

## Prerequisites

- **Node.js** ≥ 18 and **Yarn**
- **Python** ≥ 3.10
- **MongoDB** ≥ 6 (local install or MongoDB Atlas cloud)
- An **OpenAI API key** (required for AI features — summary, tutor, quiz, flashcards, study plan)

## Setup — Backend

```bash
cd backend

# 1. Create a virtual environment
python3 -m venv venv
source venv/bin/activate            # macOS/Linux
# venv\Scripts\activate             # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set MONGO_URL, DB_NAME, JWT_SECRET, OPENAI_API_KEY

# 4. Run the API server
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

The API is now live at `http://localhost:8001` (Swagger docs at `http://localhost:8001/docs`).

An **admin user is auto-seeded** on startup using `ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env` (defaults: `admin@studyai.com` / `admin123`).

## Setup — Frontend

```bash
cd frontend

# 1. Install dependencies
yarn install

# 2. Configure environment
cp .env.example .env
# Edit .env — set REACT_APP_BACKEND_URL (e.g. http://localhost:8001)

# 3. Run the dev server
yarn start
```

The app is now live at `http://localhost:3000`.

## Setup — MongoDB

### Option A: Local MongoDB
```bash
# macOS (Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Ubuntu / Debian
sudo apt-get install -y mongodb
sudo systemctl start mongod

# Docker (any OS)
docker run -d --name mongo -p 27017:27017 mongo:7
```
Then set `MONGO_URL=mongodb://localhost:27017` in `backend/.env`.

### Option B: MongoDB Atlas (cloud)
1. Create a free cluster at [mongodb.com/atlas](https://www.mongodb.com/atlas).
2. Copy the SRV connection string.
3. Set `MONGO_URL=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/?retryWrites=true` in `backend/.env`.

## Environment Variables

### `backend/.env`
| Variable | Required | Default | Description |
|---|---|---|---|
| `MONGO_URL` | yes | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | yes | `studyai` | Database name |
| `JWT_SECRET` | yes | — | Long random secret for signing JWT tokens |
| `OPENAI_API_KEY` | recommended | — | Required for AI features. Get one at [platform.openai.com](https://platform.openai.com/api-keys) |
| `OPENAI_MODEL` | no | `gpt-4o-mini` | Model used by all AI endpoints |
| `STORAGE_DIR` | no | `./storage` | Absolute or relative path for uploaded file storage |
| `CORS_ORIGINS` | no | `*` | Comma-separated list of allowed origins |
| `ADMIN_EMAIL` | no | `admin@studyai.com` | Email of the auto-seeded admin |
| `ADMIN_PASSWORD` | no | `admin123` | Password of the auto-seeded admin |

### `frontend/.env`
| Variable | Required | Description |
|---|---|---|
| `REACT_APP_BACKEND_URL` | yes | Full URL to backend API (e.g. `http://localhost:8001`) |

## Building for Production

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
```
Use a process manager like **systemd**, **supervisor**, or **PM2** for auto-restart. Put **nginx** or **Caddy** in front for HTTPS.

### Frontend
```bash
cd frontend
yarn build
# Serves optimized static files from ./build
# Deploy to Vercel, Netlify, or any static host, OR serve via nginx:
#   root /path/to/frontend/build;
#   try_files $uri /index.html;
```

Make sure the frontend's `REACT_APP_BACKEND_URL` (baked in at build time) points to your deployed API domain.

## API Endpoints

All backend routes are prefixed with `/api`.

### Auth
- `POST /api/auth/register` — Create account
- `POST /api/auth/login` — Log in (sets HTTP-only cookie)
- `POST /api/auth/logout` — Clear session
- `GET /api/auth/me` — Get current user
- `POST /api/auth/onboarding` — Save curriculum/subjects/goals

### Documents
- `POST /api/documents/upload` — Upload PDF/DOCX/PPTX/TXT (`multipart/form-data`)
- `GET /api/documents` — List user's documents
- `GET /api/documents/{id}` — Fetch document metadata
- `DELETE /api/documents/{id}` — Soft-delete

### AI
- `POST /api/ai/summary` — Generate summary (types: `short`, `detailed`, `bullet_points`, `timeline`)
- `POST /api/ai/tutor` — Streamed SSE tutor chat
- `POST /api/ai/quiz` — Generate quiz JSON
- `POST /api/ai/flashcards` — Generate flashcards JSON
- `POST /api/ai/study-plan` — Generate weekly study plan

### Notes
- `GET /api/notes` — List
- `POST /api/notes` — Create
- `PUT /api/notes/{id}` — Update
- `DELETE /api/notes/{id}` — Delete

### Progress & Dashboard
- `GET /api/progress/stats`
- `POST /api/progress/log-activity`
- `GET /api/dashboard`
- `GET /api/study-plan/current`
- `GET /api/flashcards`

## Troubleshooting

| Problem | Fix |
|---|---|
| `ImportError: No module named 'X'` | `pip install -r requirements.txt` (in the venv) |
| `MongoDB connection error` | Verify `MONGO_URL` and that MongoDB is running (`mongo --eval "db.stats()"`) |
| `AI endpoint returns 503` | `OPENAI_API_KEY` missing in `backend/.env` — add it and restart |
| `CORS error in browser` | Set `CORS_ORIGINS=http://localhost:3000` in `backend/.env` |
| Login works but subsequent requests fail | Ensure frontend calls use `withCredentials: true` (already set) and backend cookie domain matches |
| Upload fails silently | Check `backend/storage/` exists and is writable |

## License

MIT — do whatever you want.
