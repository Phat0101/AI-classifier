from __future__ import annotations

from typing import List, Dict, Any, Optional
import asyncio

from pydantic import BaseModel, Field
import httpx


# -----------------------------
# Data models shared by agent
# -----------------------------


class Item(BaseModel):
    id: str = Field(..., description="Item identifier")
    description: str = Field(..., description="Free-text item description")


class SuggestedCode(BaseModel):
    hs_code: str = Field(..., description="8-digit HS code without dots")
    stat_code: str = Field(..., description="2-digit statistical code")
    tco_link: Optional[str] = Field(
        default=None,
        description="TCO link when tariff_orders is True (format as `https://www.abf.gov.au/tariff-classification-subsite/Pages/TariffConcessionOrders.aspx?tcn={94012000}. Note the schema removes all periods and is always 8 digits (ie the 8-digit tariff code)`), otherwise null",
    )


class ClassificationResult(BaseModel):
    id: str
    description: str
    best_suggested_hs_code: str
    best_suggested_stat_code: str
    best_suggested_tco_link: Optional[str] = Field(
        default=None,
        description="TCO link for the best suggestion if applicable (format as `https://www.abf.gov.au/tariff-classification-subsite/Pages/TariffConcessionOrders.aspx?tcn={94012000}. Note the schema removes all periods and is always 8 digits (ie the 8-digit tariff code)`), otherwise null",
    )
    suggested_codes: List[SuggestedCode] = Field(
        default_factory=list,
        description="Two additional suggested HS+stat code pairs",
    )
    schedule4_concession_text: Optional[str] = Field(
        default=None,
        description="If a Schedule 4 concession likely applies, include a concise text summary; otherwise null",
    )
    reasoning: str = Field(..., description="Detailed reasoning for the classification")


class ClassificationRequest(BaseModel):
    items: List[Item]


class ClassificationResponse(BaseModel):
    results: List[ClassificationResult]


# -----------------------------
# External HTTP helper tools
# -----------------------------


_CLEAR_BASE = "https://api.clear.ai/api/v1/au_tariff"


async def tariff_chapter_lookup(hs_code_4_or_more: str) -> Dict[str, Any]:
    """
    Fetch flattened chapter tariffs and chapter notes for a 4+ digit HS code.
    Returns a dict with keys: rawData, chapterNotes.
    """
    code = hs_code_4_or_more.strip()
    if not code.isdigit() or len(code) < 4:
        return {"rawData": [], "chapterNotes": None}

    chapter_code = code[:2]
    tariffs_url = f"{_CLEAR_BASE}/tariffs/chapter_flatten_tariffs?code={code}"
    notes_url = f"{_CLEAR_BASE}/chapters/by_code?code={chapter_code}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        tariffs_task = client.get(tariffs_url)
        notes_task = client.get(notes_url)
        tariffs_res, notes_res = await asyncio.gather(tariffs_task, notes_task)

    raw = []
    notes = None
    try:
        if tariffs_res.status_code == 200:
            raw = tariffs_res.json()
    except (ValueError, httpx.HTTPError):
        raw = []
    try:
        if notes_res.status_code == 200:
            notes = notes_res.json()
    except (ValueError, httpx.HTTPError):
        notes = None

    return {"rawData": raw, "chapterNotes": notes}


async def tariff_search(hs_code_2_to_8: str) -> List[Dict[str, Any]]:
    """
    Detailed lookup for specific HS codes (2-8 digits). Returns list of matches.
    """
    code = hs_code_2_to_8.strip()
    if not code.isdigit() or not (2 <= len(code) <= 8):
        return []

    url = f"{_CLEAR_BASE}/tariffs/chapter_flatten_tariffs?code={code}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(url)
            if res.status_code != 200:
                return []
            data = res.json()
            return data if isinstance(data, list) else []
    except (httpx.HTTPError, ValueError):
        return []


async def tariff_concession_lookup(bylaw_number: str) -> Dict[str, Any]:
    """
    Lookup schedule 4 concession information by by-law number.
    """
    num = bylaw_number.strip()
    if not num.isdigit():
        return {"results": [], "content": "invalid by-law number"}

    url = (
        "https://api.clear.ai/api/v1/au_tariff/book_nodes/search"
        f"?term={num}&book_ref=AU_TARIFF_SCHED4_2022"
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(url)
            if res.status_code != 200:
                return {"results": []}
            return res.json()
    except (httpx.HTTPError, ValueError):
        return {"results": []}


