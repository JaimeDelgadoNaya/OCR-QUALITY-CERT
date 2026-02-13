from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Config:
    ocr_mode: str = "auto"  # auto|none|skip|redo|force
    force_ocr_always: bool = False
    debug_mode: bool = False
    ocr_lang: str = "eng"
    ocr_oversample: str = "450"
    ocr_timeout: str = "0"
    ocr_jobs: str = "1"
    max_filename: int = 180
    default_norma: str = "ASME_BPE"
    default_sf: str = "SF?"
    split_within_cert_on_heat_change: bool = True
    vendor_templates: Dict[str, str] = field(default_factory=lambda: {
        "DEFAULT": "{cert}({vendor})_{desc}_{norma}_{sf}_{dn_mm}_{dn_in}_{heats}.pdf",
        "GENCA": "{cert}_{heats}_{desc}_{dn_mm}_{dn_in}.pdf",
    })
