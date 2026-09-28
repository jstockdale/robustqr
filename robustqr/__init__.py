"""robustqr — a robust QR decoder that keeps trying where others give up.

Born from a wrinkled hoodie QR code that defeated pyzbar and plain OpenCV
but fell to the WeChat DNN detector. The strategy is simple: generate
several preprocessed variants of the input image and run them through a
chain of decoder engines, returning the first success with full provenance
(which engine, which variant, where in the image).

Engines are optional and probed at runtime — missing system libraries
(e.g. libzbar for pyzbar) just disable that engine instead of breaking
the import.
"""

from .pipeline import decode, decode_all, decode_file
from .result import DecodeResult

__version__ = "0.1.0"
__all__ = ["decode", "decode_all", "decode_file", "DecodeResult"]
