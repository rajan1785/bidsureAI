"""AI recommendation (FR-A01..04): grounded in stored rule results.

LLM writes the prose when available; the deterministic writer produces the
same structure offline. Either way the content only restates verified
results — the AI never invents government facts.
"""
from app.llm import llm_json

PROMPT = """You are a procurement compliance assistant. Based ONLY on the verified
results below, write a recommendation for the procurement officer. Do not invent
any facts. Return ONLY JSON: {{"summary": "...", "recommendation": "...",
"uncertainties": ["..."]}}. Keep it under 150 words total.

Bidder: {bidder}
Compliance score: {score}/100, Risk: {risk}
Results:
{results_text}
"""


def _retrieve_evidence(results: list[dict], doc_texts: dict[str, str]) -> list[str]:
    """RAG: semantic search over bidder document chunks for each problem
    requirement, using the local embedding model (all-MiniLM-L6-v2)."""
    try:
        from app.ml.embedder import backend_name, chunk, top_k
    except Exception:
        return []
    corpus, sources = [], []
    for fname, text in doc_texts.items():
        for c in chunk(text):
            corpus.append(c)
            sources.append(fname)
    if not corpus:
        return []
    lines = []
    problems = [r for r in results
                if r["status"] in ("Review Required", "Non-Compliant")][:4]
    for r in problems:
        hits = top_k(r["requirement_text"], corpus, k=1)
        if hits and hits[0][1] > 0.25:
            i, score = hits[0]
            lines.append(
                f"[{r['requirement_key']}] closest evidence ({sources[i]}, "
                f"similarity {score:.2f}): \"{corpus[i][:140]}\""
            )
    if lines:
        lines.insert(0, f"Evidence retrieved by semantic search ({backend_name()}):")
    return lines


def recommend(bidder_name: str, results: list[dict], assessment: dict,
              doc_texts: dict[str, str] | None = None) -> dict:
    evidence_lines = _retrieve_evidence(results, doc_texts or {})
    results_text = "\n".join(
        f"- {r['requirement_key']}: {r['status']} — {r['reason']}" for r in results
    )
    out = llm_json(
        PROMPT.format(bidder=bidder_name, score=assessment["score"],
                      risk=assessment["risk"], results_text=results_text),
        f"recommend_{bidder_name.lower().replace(' ', '_')[:40]}",
    )
    refs = [r["rule_id"] for r in results]

    if isinstance(out, dict) and out.get("recommendation"):
        text = (
            f"{out.get('summary', '')}\n\nRecommendation: {out['recommendation']}"
            + (
                "\n\nUncertainties: " + "; ".join(out["uncertainties"])
                if out.get("uncertainties")
                else ""
            )
        )
        if evidence_lines:
            text += "\n\n" + "\n".join(evidence_lines)
        return {"text": text.strip(), "model": "gemini-2.0-flash + minilm-rag", "grounded_refs": refs}

    # Deterministic writer
    problems = [r for r in results if r["status"] in ("Non-Compliant", "Review Required")]
    unavailable = [r for r in results if r["status"] == "Verification Unavailable"]
    compliant = [r for r in results if r["status"] == "Compliant"]

    lines = [
        f"{bidder_name} scored {assessment['score']}/100 with {assessment['risk']} risk. "
        f"{len(compliant)} requirement(s) verified compliant, {len(problems)} issue(s) found."
    ]
    for r in problems:
        lines.append(f"• {r['requirement_text']}: {r['status']} — {r['reason']} (rule {r['rule_id']}).")
    for r in unavailable:
        lines.append(f"• {r['requirement_text']}: could not be verified — {r['reason']}. Manual verification advised.")

    if any(r["critical"] and r["status"] == "Non-Compliant" for r in results):
        lines.append("Recommendation: critical mandatory requirement(s) failed; recommend detailed review before any qualification. Final decision rests with the Procurement Officer.")
    elif problems or unavailable:
        lines.append("Recommendation: seek clarification from the bidder on the flagged items before deciding. Final decision rests with the Procurement Officer.")
    else:
        lines.append("Recommendation: all verifiable requirements are compliant; bidder appears qualified subject to officer review. Final decision rests with the Procurement Officer.")

    lines.extend(evidence_lines)
    return {"text": "\n".join(lines), "model": "rules + minilm-rag", "grounded_refs": refs}
