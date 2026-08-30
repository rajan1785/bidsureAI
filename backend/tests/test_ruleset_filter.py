# Regression: ISSUE-001 — officer-deleted requirements were still evaluated
# Found by /qa on 2026-08-30
# Report: .gstack/qa-reports/qa-report-bidsure-2026-08-30.md
from app.pipeline.rules import filter_ruleset, load_ruleset


def test_filter_ruleset_drops_removed_requirements():
    ruleset = load_ruleset()
    approved = {"gst_active", "pan_valid", "psara_license", "not_blacklisted"}
    filtered = filter_ruleset(ruleset, approved)
    keys = {r["requirement_key"] for r in filtered["rules"]}
    assert keys == approved
    assert "udyam_valid" not in keys  # the officer deleted it — must not be evaluated


def test_filter_ruleset_empty_keys_falls_back_to_full_set():
    ruleset = load_ruleset()
    filtered = filter_ruleset(ruleset, set())
    assert len(filtered["rules"]) == len(ruleset["rules"])


def test_filter_ruleset_preserves_version():
    ruleset = load_ruleset()
    filtered = filter_ruleset(ruleset, {"gst_active"})
    assert filtered["version"] == ruleset["version"]
    assert len(filtered["rules"]) == 1
