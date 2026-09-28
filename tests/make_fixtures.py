"""Generate test fixtures: clean QRs plus hostile variants.

Run:  .venv/bin/python tests/make_fixtures.py
Writes PNGs into tests/fixtures/.
"""

from pathlib import Path

import cv2
import numpy as np
import qrcode

PAYLOAD = "https://example.com/robustqr-test"

OUT = Path(__file__).parent / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)


def base_qr(size: int = 400) -> np.ndarray:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=10, border=4)
    qr.add_data(PAYLOAD)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    arr = np.array(img)
    return cv2.resize(cv2.cvtColor(arr, cv2.COLOR_RGB2BGR), (size, size), interpolation=cv2.INTER_AREA)


def save(name: str, img: np.ndarray) -> None:
    cv2.imwrite(str(OUT / name), img)
    print("wrote", name, img.shape)


def main() -> None:
    clean = base_qr()
    save("clean.png", clean)

    # small / distant code -> exercises the upscale variants
    save("small.png", cv2.resize(clean, (120, 120), interpolation=cv2.INTER_AREA))

    # rotated 15 degrees
    h, w = clean.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), 15, 1.0)
    save("rotated.png", cv2.warpAffine(clean, m, (w, h), borderValue=(255, 255, 255)))

    # washed out -> exercises CLAHE
    washed = (clean.astype(np.float32) * 0.45 + 120).clip(0, 255).astype(np.uint8)
    save("lowcontrast.png", washed)

    # perspective tilt -> exercises unwarp
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[40, 30], [w - 80, 10], [w - 20, h - 40], [20, h - 10]])
    save("perspective.png", cv2.warpPerspective(clean, cv2.getPerspectiveTransform(src, dst), (w, h),
                                               borderValue=(255, 255, 255)))

    # synthetic fabric wrinkle: gentle drape + one sharp crease (the
    # characteristic fabric defect: a fold line with a local kink) +
    # fold shading. Tuned so the DNN engine decodes it while the
    # classical engines fail -- the hoodie story, reproduced.
    big = base_qr(600)
    h, w = big.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    amp = 5.0
    crease = 22.0 * np.exp(-((xs * 0.6 + ys * 0.8 - 360) ** 2) / (2 * 18.0 ** 2))
    map_x = (xs + amp * np.sin(0.008 * ys) + crease).astype(np.float32)
    map_y = (ys + 0.6 * amp * np.sin(0.008 * 0.7 * xs + 1.3)).astype(np.float32)
    wrinkled = cv2.remap(big, map_x, map_y, interpolation=cv2.INTER_LINEAR,
                         borderValue=(255, 255, 255))
    shade = (0.78 + 0.22 * np.sin(0.008 * ys + 0.5)).astype(np.float32)
    wrinkled = (wrinkled.astype(np.float32) * shade[..., None]).clip(0, 255).astype(np.uint8)
    wrinkled = cv2.GaussianBlur(wrinkled, (3, 3), 0.6)
    save("wrinkled.png", wrinkled)


if __name__ == "__main__":
    main()
