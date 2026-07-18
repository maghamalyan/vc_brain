import pytest

from vc_brain.labels.identity import normalize_domain, twitter_handle


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://www.Example.com/about", "example.com"),
        ("example.com/path", "example.com"),
        ("http://sub.example.com:8080", "sub.example.com"),
        (None, None),
    ],
)
def test_normalize_domain(value: str | None, expected: str | None) -> None:
    assert normalize_domain(value) == expected


def test_twitter_handle_normalizes_urls_and_at_prefix() -> None:
    assert twitter_handle("https://twitter.com/Alice/") == "alice"
    assert twitter_handle("@Alice") == "alice"
