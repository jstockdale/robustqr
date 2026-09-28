"""The pipeline: variants x engines, first success wins."""

from pathlib import Path
from typing import List, Optional, Sequence, Union

import numpy as np

from . import preprocess
from .engines import Engine, available_engines, default_engines
from .result import DecodeResult


def _load_image(source: Union[str, Path, np.ndarray]) -> np.ndarray:
    if isinstance(source, np.ndarray):
        image = source
    else:
        import cv2

        image = cv2.imread(str(source), cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(f"robustqr: cannot read image {source!r}")
    if image.ndim == 2:
        import cv2

        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image


def decode_all(
    source: Union[str, Path, np.ndarray],
    engines: Optional[Sequence[Engine]] = None,
    variants: Optional[Sequence[str]] = None,
) -> List[DecodeResult]:
    """Run every (variant, engine) pair; return all successes in attempt order.

    Each result is stamped with the ``engine`` and ``variant`` that produced
    it, so callers can see exactly which combination cracked the code.
    """
    image = _load_image(source)
    engines = list(engines) if engines is not None else default_engines()
    engines = [e for e in engines if e.available]
    if not engines:
        raise RuntimeError(
            "robustqr: no decoder engines available. "
            "Install an extra: pip install 'robustqr[wechat]' or 'robustqr[zbar]'"
        )
    variant_names = list(variants) if variants is not None else preprocess.DEFAULT_VARIANT_ORDER
    hits: List[DecodeResult] = []
    for vname in variant_names:
        fn = preprocess.VARIANTS.get(vname)
        if fn is None:
            raise ValueError(f"robustqr: unknown variant {vname!r}")
        try:
            variant_image = fn(image)
        except Exception:
            continue
        for engine in engines:
            try:
                results = engine.decode(variant_image)
            except Exception:
                continue
            for r in results:
                r.variant = vname
                hits.append(r)
    return hits


def decode(
    source: Union[str, Path, np.ndarray],
    engines: Optional[Sequence[Engine]] = None,
    variants: Optional[Sequence[str]] = None,
) -> Optional[DecodeResult]:
    """Decode the first QR found, or return None.

    This is the one most callers want: try hard, return the payload.
    """
    hits = decode_all(source, engines=engines, variants=variants)
    return hits[0] if hits else None


def decode_file(path: Union[str, Path], **kwargs) -> Optional[DecodeResult]:
    """Convenience wrapper for ``decode`` on a file path."""
    return decode(path, **kwargs)


def engine_report() -> str:
    """Human-readable availability report for every known engine."""
    lines = []
    for e in default_engines():
        status = "available" if e.available else f"UNAVAILABLE ({e.reason})"
        lines.append(f"  {e.name:8s} {status}")
    return "robustqr engines:\n" + "\n".join(lines)


__all__ = ["decode", "decode_all", "decode_file", "engine_report", "available_engines"]
