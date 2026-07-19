"""Regression: garbage blog values must not crash domain normalization."""

from vc_brain.labels.identity import normalize_domain


def test_normalize_domain_survives_bracketed_garbage() -> None:
    assert normalize_domain("[object Object]") is None
    assert normalize_domain("[::1]") in (None, "::1")
    assert normalize_domain("https://example.com/x") == "example.com"
