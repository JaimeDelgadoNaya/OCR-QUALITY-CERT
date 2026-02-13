import re

from .config import Config
from .models import GroupSignature


def sanitize(value: str, max_len: int = 80) -> str:
    v = (value or "").strip()
    v = v.replace("/", "-").replace("\\", "-")
    v = re.sub(r"[<>:\\|?*\"]", "", v)
    v = re.sub(r"\s+", "_", v)
    v = re.sub(r"_+", "_", v).strip("._-")
    return (v or "NA")[:max_len]


def format_heats(heats: tuple[str, ...]) -> str:
    return "+".join(heats) if heats else "HEAT?"


def build_filename(sig: GroupSignature, cfg: Config, desc: str = "TUBERIA", sf: str | None = None, dn_mm: str = "DN?", dn_in: str = "IN?") -> str:
    cert = sig.cert_id or "SIN_CERT"
    cert = sanitize(cert, 60)
    vendor = sanitize(sig.vendor or "UNKNOWN", 25)
    heats = sanitize(format_heats(sig.heats), 50)
    dn_mm = sanitize(dn_mm if dn_mm.startswith("DN") else f"DN{dn_mm}", 10).replace("DNDN", "DN")
    dn_in = sanitize(dn_in, 15)
    sf = sanitize(sf or cfg.default_sf, 10)
    desc = sanitize(desc, 80)

    template = cfg.vendor_templates.get(vendor, cfg.vendor_templates["DEFAULT"])
    name = template.format(cert=cert, vendor=vendor, desc=desc, norma=cfg.default_norma, sf=sf, dn_mm=dn_mm, dn_in=dn_in, heats=heats)
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    if len(name) > cfg.max_filename:
        name = f"{cert}_{heats}_{dn_mm}_{dn_in}.pdf"
    if name.startswith("_") or name == ".pdf":
        name = f"{cert or 'SIN_CERT'}_{heats or 'HEAT?'}.pdf"
    return name
