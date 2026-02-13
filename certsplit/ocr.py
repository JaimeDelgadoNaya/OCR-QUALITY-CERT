import os
import shutil
import subprocess
import sys

from .config import Config


def _ensure_tools() -> None:
    import ocrmypdf  # noqa: F401
    if shutil.which("tesseract") is None:
        raise RuntimeError("No encuentro tesseract en PATH")


def needs_ocr(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    alnum = sum(ch.isalnum() for ch in t)
    ratio = alnum / max(len(t), 1)
    return len(t) < 30 or ratio < 0.3


def run_ocr(input_pdf: str, output_pdf: str, cfg: Config, mode: str) -> None:
    _ensure_tools()
    cmd = [
        sys.executable,
        "-m",
        "ocrmypdf",
        "--rotate-pages",
        "--deskew",
        "--rotate-pages-threshold",
        cfg.ocr_rotate_threshold,
        "--oversample",
        cfg.ocr_oversample,
        "--tesseract-timeout",
        cfg.ocr_timeout,
        "--jobs",
        cfg.ocr_jobs,
        "--language",
        cfg.ocr_lang,
        "--tesseract-pagesegmode",
        cfg.ocr_pagesegmode,
        "--optimize",
        "0",
    ]
    flag = {"skip": "--skip-text", "redo": "--redo-ocr", "force": "--force-ocr"}.get(mode, "--skip-text")
    cmd.append(flag)
    cmd.extend([input_pdf, output_pdf])
    proc = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "OCR error").strip())
