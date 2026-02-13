import pytest
fitz = pytest.importorskip("fitz")


from certsplit.config import Config
from certsplit.pipeline import process_pdf


def _make_pdf(path):
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((72, 72), "Certificate No. 12345678\nHeat No. H111\nPage 1/2")
    p2 = doc.new_page()
    p2.insert_text((72, 72), "Supplement\nPage 2/2")
    p3 = doc.new_page()
    p3.insert_text((72, 72), "Inspection certificate No: 87654321\nColada: H222")
    doc.save(path)
    doc.close()


def test_process_pdf_splits_by_certificate(tmp_path):
    src = tmp_path / "fixture.pdf"
    out = tmp_path / "out"
    _make_pdf(str(src))
    outputs = process_pdf(str(src), "GENCA", str(out), Config(ocr_mode="none"))
    assert len(outputs) == 2

    d1 = fitz.open(outputs[0])
    d2 = fitz.open(outputs[1])
    try:
        assert d1.page_count in {1, 2}
        assert d2.page_count in {1, 2}
        assert d1.page_count + d2.page_count == 3
    finally:
        d1.close()
        d2.close()

    audit = (out / "audit.csv").read_text(encoding="utf-8")
    assert "12345678" in audit
    assert "87654321" in audit