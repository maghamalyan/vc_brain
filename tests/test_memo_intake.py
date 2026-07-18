from pathlib import Path

from vc_brain.memo.intake import extract_deck_evidence


def _single_page_pdf(text: str) -> bytes:
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
        + content
        + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, value in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode())
        pdf.extend(value)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n"
        ).encode()
    )
    return bytes(pdf)


def test_deck_pages_become_traceable_single_source_evidence(tmp_path: Path) -> None:
    deck = tmp_path / "deck.pdf"
    deck.write_bytes(_single_page_pdf("Three paid design partners"))

    deck_text, evidence = extract_deck_evidence(deck, "Fixture Co")

    assert deck_text == "[deck page 1] Three paid design partners"
    assert len(evidence) == 1
    assert evidence[0]["event_type"] == "deck_claim"
    assert evidence[0]["source"] == "deck page 1"
    assert evidence[0]["verification_status"] == "single_source"
    assert evidence[0]["url"].endswith("deck.pdf#page=1")
    assert evidence[0]["evidence_id"].startswith("deck-")
