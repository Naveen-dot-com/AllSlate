from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from supabase import Client, create_client

project_root = Path(__file__).resolve().parents[2]
for env_path in (project_root / ".env", project_root / "backend" / ".env"):
    if env_path.exists() and load_dotenv is not None:
        load_dotenv(env_path)


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def get_supabase_client() -> Optional[Client]:
    """Return a configured Supabase client when backend credentials are available."""
    url = _first_env("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL")
    key = _first_env("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:  # pragma: no cover - provider creates a client object if env exists
        return None


def get_gemini_call() -> Optional[Callable[[str], str]]:
    """Return a real Gemini generation callable when a key is configured."""
    api_key = _first_env("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
    except Exception:  # pragma: no cover - dependency may be absent until installed
        return None

    try:
        client = genai.Client(api_key=api_key)
    except Exception:  # pragma: no cover - invalid config falls back gracefully
        return None

    def _call(prompt: str) -> str:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if text:
            return text.strip()
        output = getattr(response, "output_text", None)
        if output:
            return str(output).strip()
        return str(response).strip()

    return _call
