"""Preprocessing variants.

Each variant is a small function ``BGR ndarray -> BGR ndarray`` registered
under a short name. The pipeline runs every (variant, engine) combination
until something decodes, so variants should be cheap and each target a
different failure mode:

- ``original``   — untouched input (engines may do their own preprocessing)
- ``clahe``      — local contrast boost for washed-out / uneven lighting
- ``denoised``   — edge-preserving denoise + adaptive threshold for noisy prints
- ``upscale_15`` / ``upscale_20`` — for small or distant codes
- ``unwarp``     — perspective-flatten the detected QR quad; the
  "wrinkled hoodie" variant. Falls back to the input when no quad is found.
"""

from typing import Callable, Dict

import numpy as np


def _need_cv2():
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("robustqr preprocessing needs opencv-python-headless (or -contrib)") from exc
    return cv2


def v_original(image: np.ndarray) -> np.ndarray:
    return image


def v_clahe(image: np.ndarray) -> np.ndarray:
    cv2 = _need_cv2()
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    out = clahe.apply(gray)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def v_denoised(image: np.ndarray) -> np.ndarray:
    cv2 = _need_cv2()
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    smooth = cv2.bilateralFilter(gray, 5, 50, 50)
    th = cv2.adaptiveThreshold(smooth, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 9)
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)


def _upscale(scale: float) -> Callable[[np.ndarray], np.ndarray]:
    def fn(image: np.ndarray) -> np.ndarray:
        cv2 = _need_cv2()
        h, w = image.shape[:2]
        return cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    fn.__name__ = f"v_upscale_{scale}"
    return fn


def v_unwarp(image: np.ndarray) -> np.ndarray:
    """Warp the detected QR quad to a front-on square.

    Uses the classical detector's ``detect()`` (detection without
    decoding) to find corner points, then a perspective transform. On
    wrinkled or tilted codes this hands the decoder engines a much
    easier image. Returns the input unchanged when no quad is detected.
    """
    cv2 = _need_cv2()
    try:
        det = cv2.QRCodeDetector()
        out = det.detect(image)
        # 5.x -> (ok: bool, points); 4.x -> points
        if isinstance(out, tuple) and len(out) == 2 and isinstance(out[0], bool):
            ok, points = out
        else:
            ok, points = True, out
        quads = np.asarray(points).reshape(-1, 4, 2) if ok and points is not None else None
    except Exception:
        quads = None
    if quads is None or len(quads) == 0:
        return image
    quad = np.asarray(quads[0], dtype=np.float32)  # 4x2
    # Order: top-left, top-right, bottom-right, bottom-left via sums/diffs.
    s = quad.sum(axis=1)
    d = np.diff(quad, axis=1).ravel()
    ordered = np.array([quad[np.argmin(s)], quad[np.argmin(d)], quad[np.argmax(s)], quad[np.argmax(d)]],
                       dtype=np.float32)
    side = int(max(np.linalg.norm(ordered[0] - ordered[1]), np.linalg.norm(ordered[1] - ordered[2])))
    side = max(side, 64)
    dst = np.array([[0, 0], [side, 0], [side, side], [0, side]], dtype=np.float32)
    try:
        m = cv2.getPerspectiveTransform(ordered, dst)
        return cv2.warpPerspective(image, m, (side, side))
    except Exception:
        return image


VARIANTS: Dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "original": v_original,
    "clahe": v_clahe,
    "upscale_15": _upscale(1.5),
    "upscale_20": _upscale(2.0),
    "denoised": v_denoised,
    "unwarp": v_unwarp,
}

#: Default pipeline order. Cheap/global variants first; ``unwarp`` last
#: because it runs a DNN detection pass of its own.
DEFAULT_VARIANT_ORDER = ["original", "clahe", "upscale_15", "upscale_20", "denoised", "unwarp"]
