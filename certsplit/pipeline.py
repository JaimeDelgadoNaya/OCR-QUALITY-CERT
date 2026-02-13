import os
from typing import Callable

import fitz

from .config import Config
from .extraction import extract_page_signature
from .grouping import build_group_signature, group_pages
from .logging_utils import append_group_audit, write_page_audit
from .naming import build_filename
from .ocr import needs_ocr, run_ocr


def insert_pages_exact(newdoc: fitz.Document, src: fitz.Document, pages: list[int]) -> None:
    for p in pages:
        newdoc.insert_pdf(src, from_page=p, to_page=p)


def _decide_ocr(doc: fitz.Document, cfg: Config) -> str:
    if cfg.force_ocr_always:
        return "force"
    if cfg.ocr_mode != "auto":
        return cfg.ocr_mode
    sample = "\n".join((doc.load_page(i).get_text("text") or "") for i in range(min(doc.page_count, 5)))
    return "skip" if needs_ocr(sample) else "none"


def process_pdf(pdf_path: str, vendor: str, out_dir: str, cfg: Config, status_cb: Callable[[str], None] | None = None) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    work_pdf = pdf_path

    doc = fitz.open(pdf_path)
    mode = _decide_ocr(doc, cfg)
    doc.close()

    if mode in {"skip", "redo", "force"}:
        ocr_pdf = os.path.join(out_dir, f"{base}__ocr.pdf")
        if status_cb:
            status_cb(f"OCR ({mode})")
        run_ocr(pdf_path, ocr_pdf, cfg, mode)
        work_pdf = ocr_pdf

    doc = fitz.open(work_pdf)
    extractions = [extract_page_signature(doc.load_page(i), vendor) for i in range(doc.page_count)]
    groups = group_pages(extractions, split_on_heat_change=cfg.split_within_cert_on_heat_change)
    write_page_audit(out_dir, base, extractions)

    outputs: list[str] = []
    used = set()
    for pages in groups:
        gs = build_group_signature(pages, extractions, vendor)
        filename = build_filename(gs, cfg)
        candidate = filename
        n = 1
        while candidate in used or os.path.exists(os.path.join(out_dir, candidate)):
            candidate = filename.replace(".pdf", f"__{n}.pdf")
            n += 1
        used.add(candidate)
        out_path = os.path.join(out_dir, candidate)
        newdoc = fitz.open()
        insert_pages_exact(newdoc, doc, pages)
        newdoc.save(out_path)
        newdoc.close()
        outputs.append(out_path)
        append_group_audit(out_dir, pdf_path, out_path, gs)
    doc.close()
    return outputs
