"""Decoder engine adapters.

Every engine exposes the same tiny interface::

    name: str            # short id, e.g. "wechat"
    available: bool      # False when its dependency is missing
    reason: str          # human-readable when unavailable
    decode(image)        # BGR ndarray -> list[DecodeResult]

Engines are ordered strongest-first by the pipeline: the DNN-based WeChat
detector handles wrinkles, folds and perspective far better than the
classical decoders, so it goes first.
"""

from typing import List

import numpy as np

from .result import DecodeResult


class Engine:
    name = "base"
    available = False
    reason = "not implemented"

    def decode(self, image: np.ndarray) -> List[DecodeResult]:  # noqa: ARG002
        return []


def _to_gray(image: np.ndarray):
    import cv2

    if image.ndim == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def _quad(result: DecodeResult, points) -> DecodeResult:
    if points is not None:
        try:
            result.bbox = [[float(x), float(y)] for x, y in np.asarray(points).reshape(-1, 2)]
        except Exception:
            pass
    return result


class WeChatEngine(Engine):
    """OpenCV contrib WeChat QR detector (DNN-based).

    This is the engine that cracked the wrinkled hoodie: classical
    decoders need clean finder patterns, the DNN tolerates distortion.
    Requires ``opencv-contrib-python`` (or the headless build).
    """

    name = "wechat"

    def __init__(self) -> None:
        self.available = False
        self.reason = ""
        self._det = None
        try:
            import cv2

            if not hasattr(cv2, "wechat_qrcode_WeChatQRCode"):
                self.reason = "opencv-contrib-python not installed (plain opencv has no wechat_qrcode module)"
                return
            # Zero-arg constructor works: models ship inside the wheel.
            self._det = cv2.wechat_qrcode_WeChatQRCode()
            self.available = True
        except ImportError as exc:
            self.reason = f"cv2 import failed: {exc}"
        except Exception as exc:  # e.g. cv2.error from the constructor
            self.reason = f"wechat_qrcode_WeChatQRCode() failed: {exc}"

    def decode(self, image: np.ndarray) -> List[DecodeResult]:
        if not self.available:
            return []
        try:
            out = self._det.detectAndDecode(image)
        except Exception:
            return []
        # OpenCV 4.x returns (retval, decoded_info, points, straight);
        # OpenCV 5.x returns (decoded_info, points). Handle both.
        try:
            if len(out) == 4:
                _, decoded_info, points, _ = out
            elif len(out) == 2:
                decoded_info, points = out
            else:
                return []
        except Exception:
            return []
        out = []
        n = len(decoded_info)
        if points is None:
            pts = [None] * n
        else:
            pts = list(np.asarray(points).reshape(n, -1, 2))
        for text, pt in zip(decoded_info, pts):
            if text:  # empty string == detected but not decoded
                out.append(_quad(DecodeResult(data=text, engine=self.name, variant=""), pt))
        return out


class OpenCVEngine(Engine):
    """Classical OpenCV QRCodeDetector (detectAndDecodeMulti).

    Fast and dependency-light, but needs fairly clean finder patterns —
    wrinkles and folds usually defeat it.
    """

    name = "opencv"

    def __init__(self) -> None:
        self.available = False
        self.reason = ""
        self._det = None
        try:
            import cv2

            self._det = cv2.QRCodeDetector()
            self.available = True
        except ImportError as exc:
            self.reason = f"cv2 import failed: {exc}"

    def decode(self, image: np.ndarray) -> List[DecodeResult]:
        if not self.available:
            return []
        try:
            ok, decoded_info, points, _ = self._det.detectAndDecodeMulti(image)
        except Exception:
            return []
        if not ok:
            return []
        out = []
        pts = np.asarray(points).reshape(len(decoded_info), -1, 2) if points is not None else [None] * len(decoded_info)
        for text, pt in zip(decoded_info, pts):
            if text:
                out.append(_quad(DecodeResult(data=text, engine=self.name, variant=""), pt))
        return out


class PyzbarEngine(Engine):
    """pyzbar / ZBar decoder.

    Excellent on clean codes; needs the ``libzbar0`` system library,
    which is why this engine degrades gracefully when it is absent.
    """

    name = "pyzbar"

    def __init__(self) -> None:
        self.available = False
        self.reason = ""
        try:
            from pyzbar.pyzbar import decode as _decode

            self._decode = _decode
            self.available = True
        except ImportError as exc:
            self.reason = f"pyzbar unavailable: {exc}"
        except Exception as exc:  # missing libzbar shared library, etc.
            self.reason = f"pyzbar unavailable: {exc}"

    def decode(self, image: np.ndarray) -> List[DecodeResult]:
        if not self.available:
            return []
        try:
            gray = _to_gray(image)
            found = self._decode(gray)
        except Exception:
            return []
        out = []
        for sym in found:
            if sym.type != "QRCODE":
                continue
            try:
                text = sym.data.decode("utf-8", errors="replace")
            except Exception:
                continue
            r = DecodeResult(data=text, engine=self.name, variant="", raw=bytes(sym.data))
            if sym.rect:
                x, y, w, h = sym.rect.left, sym.rect.top, sym.rect.width, sym.rect.height
                r.bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
            out.append(r)
        return out


def default_engines() -> List[Engine]:
    """Engines in pipeline priority order: strongest first."""
    return [WeChatEngine(), OpenCVEngine(), PyzbarEngine()]


def available_engines() -> List[Engine]:
    """Only the engines whose dependencies are present."""
    return [e for e in default_engines() if e.available]
