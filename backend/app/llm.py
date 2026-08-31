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
    "gemini-3.6-flash:generateContent"
)


def feature_enabled(feature: str) -> bool:
    """GEMINI_FEATURES controls which pipeline steps may call the LLM.
    Default 'recommend': prose only — extraction and rule drafting stay
    deterministic so verification results are stable run-to-run."""
    enabled = os.environ.get("GEMINI_FEATURES", "recommend")
    return feature in [f.strip() for f in enabled.split(",")] or enabled == "all"


def llm_json(prompt: str, cache_key: str, feature: str = "recommend"):
    """Returns parsed JSON from the LLM, cached copy, or None."""
    if not feature_enabled(feature):
        return None  # feature off: no API call AND no LLM cache reuse
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
