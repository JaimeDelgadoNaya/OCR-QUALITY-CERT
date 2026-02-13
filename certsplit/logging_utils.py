import csv
import os
from .models import GroupSignature, PageExtraction


def write_page_audit(out_dir: str, base: str, extractions: list[PageExtraction]) -> str:
    path = os.path.join(out_dir, f"{base}__page_signatures.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(["page", "cert_id", "heats", "vendor", "score", "flags", "raw_cert_candidates", "raw_heat_candidates"])
        for e in extractions:
            sig = e.signature
            w.writerow([
                e.page_index + 1,
                sig.cert_id if sig else "",
                "+".join(sig.heats) if sig else "",
                sig.vendor if sig else "",
                sig.score if sig else 0,
                ",".join(sig.flags) if sig else "",
                repr(e.cert_candidates),
                repr(e.heat_candidates),
            ])
    return path


def append_group_audit(out_dir: str, input_pdf: str, output_pdf: str, sig: GroupSignature) -> str:
    path = os.path.join(out_dir, "audit.csv")
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=';')
        if not exists:
            w.writerow(["input", "output", "pages", "cert", "heats", "vendor", "score"])
        w.writerow([input_pdf, output_pdf, ",".join(str(i + 1) for i in sig.pages), sig.cert_id, "+".join(sig.heats), sig.vendor, sig.score])
    return path
