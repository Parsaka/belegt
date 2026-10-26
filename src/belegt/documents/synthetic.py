"""A small, made-up sustainability statement as a real PDF, for tests and the kind smoke test.

Real reports are copyrighted and cannot be checked in. This writes a valid PDF with one text
line per row (standard Helvetica, ASCII only), which pypdf reads back line by line like a table.
"""

from __future__ import annotations

from collections.abc import Sequence


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pdf_bytes(pages: Sequence[Sequence[str]]) -> bytes:
    """A PDF with one page per item; each string is one line of text."""
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",  # the page tree, filled in once the page ids are known
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    page_ids = []
    for lines in pages:
        ops = ["BT", "/F1 10 Tf", "14 TL", "50 790 Td"]
        for line in lines:
            ops += [f"({_escape(line)}) Tj", "T*"]
        ops.append("ET")
        stream = "\n".join(ops).encode("latin-1")
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        content_id = len(objects)
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % content_id
        )
        page_ids.append(len(objects))
    kids = " ".join(f"{i} 0 R" for i in page_ids).encode()
    objects[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(page_ids))

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


def statement(company: str, scope1_mt: str, scope2_mt: str, scope3_mt: str) -> bytes:
    """Three pages: cover, prose that mentions Scope 1 (a decoy), and the E1-6 table."""
    return pdf_bytes(
        [
            [f"{company}", "Nachhaltigkeitserklaerung 2024 (synthetisch, nur fuer Tests)"],
            [
                "Klimaschutz",
                "Wir wollen die Emissionen in Scope 1 bis 2030 um 25 % senken.",
            ],
            [
                "E1-6 Brutto-THG-Emissionen der Kategorien Scope 1, 2 und 3",
                "in Mio. t CO2e 2024 2023",
                f"Scope 1 THG-Emissionen {scope1_mt} 9,9",
                f"Scope 2 THG-Emissionen (marktbasiert) {scope2_mt} 1,2",
                f"Scope 3 THG-Emissionen gesamt {scope3_mt} 55,0",
            ],
        ]
    )
