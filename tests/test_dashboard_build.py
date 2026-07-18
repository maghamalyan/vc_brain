from html.parser import HTMLParser
from pathlib import Path

from vc_brain.dashboard.build import build_site


class StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.tables = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        if element_id := attributes.get("id"):
            self.ids.add(element_id)
        if tag == "a" and (href := attributes.get("href")):
            self.links.append(href)
        if tag == "table":
            self.tables += 1


def parse(path: Path) -> tuple[StructureParser, str]:
    html = path.read_text(encoding="utf-8")
    parser = StructureParser()
    parser.feed(html)
    return parser, html


def test_dashboard_build_exposes_ranked_and_trust_boundaries(tmp_path: Path) -> None:
    output = tmp_path / "site"

    index_path = build_site(output_dir=output)

    index, index_html = parse(index_path)
    assert index.tables == 1
    assert "ranked-candidates" in index.ids
    assert "thesis-filter" in index.ids
    assert index_html.count("data-candidate-row") == 12
    assert "Synthetic demo data" in index_html
    assert (output / "assets" / "plotly.min.js").stat().st_size > 1_000_000
    assert (output / "thesis.json").exists()

    detail, detail_html = parse(
        output / "candidate" / "ada-lovelace-fixture.html"
    )
    assert {
        "trajectory-chart",
        "investment-memo",
        "three-axis-screen",
        "evidence-timeline",
        "evidence-gaps",
    }.issubset(detail.ids)
    assert "plotly.min.js" in detail_html
    assert "trust-badge verified" in detail_html
    assert "Contradiction detected" in detail_html
    assert "LICENSE is AGPL-3.0" in detail_html
    assert any(link.startswith("https://github.com/") for link in detail.links)

    _, honest_gap_html = parse(
        output / "candidate" / "grace-hopper-fixture.html"
    )
    assert "Traction &amp; KPIs: not disclosed — pre-launch." in honest_gap_html

