from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SummaryRecord:
    element_id: str
    summary_text: str
    asset_reference: Optional[str] = None


class Summarizer:
    def summarize(self, element_id: str, content: str, asset_reference: Optional[str] = None) -> SummaryRecord:
        summary = content.strip() or "No summary available"
        return SummaryRecord(element_id=element_id, summary_text=summary, asset_reference=asset_reference)
