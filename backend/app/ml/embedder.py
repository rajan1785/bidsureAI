"""Local embedding model + tiny vector search for RAG.

Uses all-MiniLM-L6-v2 (sentence-transformers, self-hosted, cached locally —
no API, works offline). If the model isn't available on a machine, degrades
to a TF-IDF vectorizer so retrieval still works.
"""
import numpy as np

_model = None
_backend = None


def _load():
    global _model, _backend
    if _model is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _backend = "all-MiniLM-L6-v2"
    except Exception:
        from sklearn.feature_extraction.text import TfidfVectorizer

        _model = TfidfVectorizer(ngram_range=(1, 2))
        _backend = "tfidf-fallback"


def backend_name() -> str:
    _load()
    return _backend


def embed(texts: list[str]) -> np.ndarray:
    _load()
    if _backend == "tfidf-fallback":
        return np.asarray(_model.fit_transform(texts).todense())
    return np.asarray(_model.encode(texts, normalize_embeddings=True))


def top_k(query: str, corpus: list[str], k: int = 3) -> list[tuple[int, float]]:
    """Returns [(corpus_index, cosine_score)] best-first."""
    if not corpus:
        return []
    _load()
    if _backend == "tfidf-fallback":
        mats = _model.fit_transform(corpus + [query])
        m = np.asarray(mats.todense())
        c, q = m[:-1], m[-1]
        denom = (np.linalg.norm(c, axis=1) * np.linalg.norm(q)) + 1e-9
        scores = (c @ q) / denom
    else:
        c = np.asarray(_model.encode(corpus, normalize_embeddings=True))
        q = np.asarray(_model.encode([query], normalize_embeddings=True))[0]
        scores = c @ q
    order = np.argsort(-scores)[:k]
    return [(int(i), float(scores[i])) for i in order]


def chunk(text: str, max_len: int = 300) -> list[str]:
    """Split document text into retrieval chunks (grouped lines)."""
    chunks, cur = [], ""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(cur) + len(line) > max_len and cur:
            chunks.append(cur.strip())
            cur = ""
        cur += line + " "
    if cur.strip():
        chunks.append(cur.strip())
    return chunks
