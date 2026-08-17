from __future__ import annotations

from fastapi import FastAPI

from backend.app.api.routes import (
    chat_router,
    conversation_settings_router,
    documents_router,
    status_stream_router,
)

app = FastAPI(title="Allslate API")

app.include_router(documents_router)
app.include_router(status_stream_router)
app.include_router(chat_router)
app.include_router(conversation_settings_router)
