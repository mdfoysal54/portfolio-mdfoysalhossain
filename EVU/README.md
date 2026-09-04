# EVU 

This is the single project. Do not manually merge another folder.

## Architecture

Browser
  -> Next.js frontend (Step 3)
  -> FastAPI backend (Steps 1 + 2)
  -> JWT authentication
  -> PostgreSQL later / SQLite now
  -> EVU AI Gateway
  -> OpenAI

## Your current .env

SQLite is OK for local development:

DATABASE_URL=sqlite:///./app.db

FastAPI/SQLAlchemy supports SQLite for simple local development; a server database such as PostgreSQL is a better later production choice.

IMPORTANT: `OPENAI_API_KEY=sk-placeholder-key-12345` is only a placeholder and will NOT produce real AI answers. Put your real API key in `backend/.env`.

## Backend

PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend:
http://127.0.0.1:8000

Swagger:
http://127.0.0.1:8000/docs

## Frontend

Open a SECOND terminal:

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Frontend:
http://localhost:3000

## Test

1. Open http://localhost:3000
2. Register an account
3. Login
4. Send a message
5. EVU calls the backend
6. Backend authenticates you
7. Backend sends the conversation to the AI Gateway
8. AI Gateway calls OpenAI
9. Response is saved to SQLite
10. Response appears in the browser

## If you see an AI provider error

Check `backend/.env`.

This will NOT work:

OPENAI_API_KEY=sk-placeholder-key-12345

You need your real API key.

Do not post your API key in chat, GitHub, screenshots, or public repositories.

## Next planned EVU steps

Step 4 — Redis + streaming + better chat state
Step 5 — multiple LLM providers (OpenAI/Claude/Gemini/Grok)
Step 6 — file upload + RAG + pgvector
Step 7 — long-term memory
Step 8 — tools
Step 9 — agent orchestration
Step 10 — voice/vision/multimodal
Step 11 — open-source models
Step 12 — fine-tuning
Step 13+ — model training infrastructure
