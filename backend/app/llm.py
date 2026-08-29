"""LLM helper (Gemini) with a hard offline guarantee.

Every generative feature has a deterministic fallback, so the demo never
depends on network or quota. Successful LLM responses are cached to disk
and reused when offline.
"""
import json
import os
import re
from pathlib import Path

import httpx

CACHE_DIR = Path(__file__).parents[1] / "cache"
CACHE_DIR.mkdir(exist_ok=True)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


def llm_json(prompt: str, cache_key: str):
    """Returns parsed JSON from the LLM, cached copy, or None."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            r = httpx.post(
                f"{GEMINI_URL}?key={api_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30,
            )
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            m = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
            parsed = json.loads(m.group(0)) if m else None
            if parsed is not None:
                cache_file.write_text(json.dumps(parsed, indent=2))
                return parsed
        except Exception:
            pass
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except Exception:
            return None
    return None
