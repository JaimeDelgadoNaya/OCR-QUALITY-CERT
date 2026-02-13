from dataclasses import dataclass, field
from typing import Tuple, List


@dataclass(frozen=True)
class PageSignature:
    cert_id: str
    heats: Tuple[str, ...]
    vendor: str
    flags: Tuple[str, ...]
    is_attachment: bool
    is_certificate_page: bool
    score: float


@dataclass
class PageExtraction:
    page_index: int
    full_text: str
    cert_candidates: List[tuple[str, float]] = field(default_factory=list)
    heat_candidates: List[tuple[str, float]] = field(default_factory=list)
    signature: PageSignature | None = None


@dataclass
class GroupSignature:
    cert_id: str
    heats: Tuple[str, ...]
    vendor: str
    score: float
    pages: List[int]
