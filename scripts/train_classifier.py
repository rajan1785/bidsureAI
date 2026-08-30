"""Train the document-type classifier on the synthetic corpus.

Produces backend/app/ml/doc_classifier.joblib (TF-IDF + Logistic Regression
pipeline) and metrics.json (held-out accuracy + per-class report).

Run: .venv/bin/python scripts/train_classifier.py
"""
import json
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from app.ml.synth import DOC_TYPES, build_corpus  # noqa: E402

OUT = Path(__file__).parents[1] / "backend" / "app" / "ml"


def main():
    texts, labels = build_corpus(per_class=120)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, stratify=labels, random_state=7
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2),
                                  sublinear_tf=True, min_df=2)),
        ("clf", LogisticRegression(max_iter=2000, C=4.0)),
    ])
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    report = classification_report(y_test, pred, output_dict=True)
    cm = confusion_matrix(y_test, pred, labels=DOC_TYPES).tolist()

    joblib.dump(model, OUT / "doc_classifier.joblib")
    (OUT / "metrics.json").write_text(json.dumps({
        "model": "TF-IDF (1-2 grams) + LogisticRegression",
        "corpus": f"{len(texts)} synthetic documents, {len(DOC_TYPES)} classes",
        "test_size": len(y_test),
        "accuracy": round(acc, 4),
        "labels": DOC_TYPES,
        "confusion_matrix": cm,
        "per_class_f1": {k: round(v["f1-score"], 4) for k, v in report.items()
                         if k in DOC_TYPES},
    }, indent=2))

    print(f"accuracy on held-out set: {acc:.4f} ({len(y_test)} samples)")
    for k in DOC_TYPES:
        print(f"  {k:16} f1={report[k]['f1-score']:.3f}")
    print(f"saved: {OUT / 'doc_classifier.joblib'}")


if __name__ == "__main__":
    main()
