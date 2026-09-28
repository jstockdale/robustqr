"""Structured decode results."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DecodeResult:
    """One successfully decoded QR code."""

    data: str                      # decoded text payload
    engine: str                    # engine that decoded it, e.g. "wechat"
    variant: str                   # preprocessing variant, e.g. "clahe"
    bbox: Optional[list] = field(default=None)   # corner points [[x,y]...] if known
    raw: bytes = b""               # raw decoded bytes when available

    def __str__(self) -> str:
        return self.data
