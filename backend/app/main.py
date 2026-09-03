from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import (
    chat_router,
    conversation_settings_router,
    documents_router,
    status_stream_router,
)

app = FastAPI(title="Allslate API")

cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_stream_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(conversation_settings_router)
