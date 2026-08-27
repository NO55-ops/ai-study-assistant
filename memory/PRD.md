# AI Study Assistant — PRD

## Original problem statement
An AI-powered study assistant that transforms learning material into personalized summaries, quizzes, flashcards, tutoring, and study plans. Core features: file upload (PDF/DOCX/PPTX/TXT), AI Summaries, AI Tutor, AI Quiz Generator, AI Study Planner, Flashcards, and a Daily Streak System. Target: high school / IB / AP / SAT students.

## Tech stack (now fully standalone)
- **Frontend**: React 19 + Tailwind + shadcn/ui + Lucide + Sonner
- **Backend**: FastAPI + Motor + OpenAI SDK (standard `openai` library)
- **Database**: MongoDB
- **Storage**: Local filesystem (`STORAGE_DIR`, default `./storage`)
- **Auth**: JWT via HTTP-only cookies, bcrypt

## What's implemented
- Full auth (register / login / logout / onboarding / /me) with JWT cookies
- Dashboard (bento grid, recent docs, stats, current study plan)
- Document upload → local filesystem storage → text extraction (PDF/DOCX/PPTX/TXT)
- AI Summary (short / detailed / bullet_points / timeline)
- AI Tutor with SSE streaming
- AI Quiz + AI Flashcards + AI Study Planner (JSON output parsed and stored)
- Notes CRUD + floating NotesWidget across protected pages
- Progress tracking (streaks, activity log)
- Settings page with dark/light mode + accent theme (CSS-variable driven)

## Standalone / portability refactor — 30 Jul 2026
- Removed `emergentintegrations` dependency; replaced with standard `openai.AsyncOpenAI` SDK.
- Removed Emergent object-storage HTTP client; replaced with local filesystem (`put_object` / `get_object` operate on `STORAGE_DIR`).
- Removed `EMERGENT_LLM_KEY` env; project now uses `OPENAI_API_KEY` + `OPENAI_MODEL`.
- Added `README.md` with full setup, prod build & troubleshooting.
- Added `backend/.env.example` and `frontend/.env.example`.
- Extended `.gitignore` to cover venv, storage, and Emergent-platform folders.
- Verified upload end-to-end (login → upload PDF → local FS write → DocumentView).

## Known items / backlog
- **P0**: Test end-to-end AI endpoints (summary/tutor/quiz) with a real `OPENAI_API_KEY` on user's machine.
- **P1**: Refactor hard-coded hex colours in `Upload.js`, `DocumentView.js`, `Login.js` to CSS variables so dark mode covers every page.
- **P1**: Assess if standalone `/notes` route is redundant (NotesWidget covers same UX).
- **P2**: Daily streak badges + achievements.
- **P2**: Google/Apple auth, image/handwritten/audio support, Mind Maps.

## API surface (all `/api` prefixed)
Auth · Documents · AI (summary / tutor / quiz / flashcards / study-plan) · Notes · Progress · Dashboard.

## Test credentials
See `/app/memory/test_credentials.md` (admin auto-seeded on startup via `ADMIN_EMAIL` / `ADMIN_PASSWORD`).
