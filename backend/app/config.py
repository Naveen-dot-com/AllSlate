from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    load_dotenv = None

project_root = Path(__file__).resolve().parents[2]
backend_dir = project_root / "backend"
for env_path in (project_root / ".env", backend_dir / ".env"):
    if env_path.exists() and load_dotenv is not None:
        load_dotenv(env_path)


@dataclass(frozen=True)
class HardeningConfig:
    ocr_confidence_partial_threshold: float = 0.75
    ocr_confidence_uncertain_threshold: float = 0.55
    table_regularity_partial_threshold: float = 0.8
    table_regularity_uncertain_threshold: float = 0.6
    partial_vs_fail_threshold: float = 0.25
    supported_languages: tuple[str, ...] = (
        "en",
        "es",
        "fr",
    )


def _normalize_supported_languages(value: str | None) -> tuple[str, ...]:
    languages = (value or "en,es,fr").split(",")
    normalized = []
    for language in languages:
        item = language.strip().lower()
        if item:
            normalized.append(item)
    return tuple(dict.fromkeys(normalized))


DEFAULT_HARDENING_CONFIG = HardeningConfig(
    ocr_confidence_partial_threshold=float(os.getenv("OCR_CONFIDENCE_PARTIAL_THRESHOLD", 0.75)),
    ocr_confidence_uncertain_threshold=float(os.getenv("OCR_CONFIDENCE_UNCERTAIN_THRESHOLD", 0.55)),
    table_regularity_partial_threshold=float(os.getenv("TABLE_REGULARITY_PARTIAL_THRESHOLD", 0.8)),
    table_regularity_uncertain_threshold=float(os.getenv("TABLE_REGULARITY_UNCERTAIN_THRESHOLD", 0.6)),
    partial_vs_fail_threshold=float(os.getenv("PARTIAL_VS_FAIL_THRESHOLD", 0.25)),
    supported_languages=_normalize_supported_languages(os.getenv("SUPPORTED_LANGUAGES")),
)


def get_hardening_config() -> HardeningConfig:
    return DEFAULT_HARDENING_CONFIG
