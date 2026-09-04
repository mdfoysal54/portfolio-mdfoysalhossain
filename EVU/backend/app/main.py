from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agent import router as agent_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.documents import router as documents_router
from app.api.routes.providers import router as providers_router
from app.core.config import settings
from app.database import models  # noqa: F401
from app.database.database import Base, engine
from app.services.redis_service import redis_service


app = FastAPI(title=settings.APP_NAME, version="0.7.0", description="EVU AI platform")

# Allow localhost, 127.0.0.1, your local network IP, and the configured FRONTEND_URL
allowed_origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.0.103:3000",
]

# Deduplicate origins list
allowed_origins = list({origin for origin in allowed_origins if origin})

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Local development convenience. Production should use Alembic migrations.
Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(providers_router)
app.include_router(documents_router)


@app.get("/")
async def root():
    return {"name": "EVU", "status": "online", "version": "0.6.0"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "redis": await redis_service.ping(),
        "redis_enabled": settings.REDIS_ENABLED,
        "rag_enabled": settings.RAG_ENABLED,
    }