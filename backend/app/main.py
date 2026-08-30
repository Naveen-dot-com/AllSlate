from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import (
    chat_router,
    conversation_settings_router,
    documents_router,
    status_stream_router,
)

app = FastAPI(title="Allslate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(status_stream_router)
app.include_router(chat_router)
app.include_router(conversation_settings_router)
