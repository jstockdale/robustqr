# robustqr

A QR decoder that keeps trying where others give up: it runs **preprocessing
variants × decoder engines** and returns the first success — stamped with
exactly which engine and variant cracked it.

## Origin story

A wrinkled hoodie QR code defeated `pyzbar` and plain OpenCV completely.
OpenCV's contrib **WeChat detector** (DNN-based) finally read it — but only
from the flatter photos, and only at some scales. So the pipeline was born:
don't bet on one decoder or one preprocessing step; try a grid of them.

On the original hoodie photos, the pipeline decodes **2 of 3** images —
including one that the bare WeChat detector couldn't read the night it was
cracked (the `clahe` contrast variant did it).

## How it works

```
input image
  ├─ variants: original, clahe, upscale_15, upscale_20, denoised, unwarp
  └─ engines (strongest first): wechat → opencv → pyzbar
       → first success wins, with (engine, variant, bbox) provenance
```

- **Engines** are optional and probed at runtime. Missing `libzbar`? The
  pyzbar engine reports unavailable instead of breaking your import.
- **Variants** each target a failure mode: `clahe` for washed-out prints,
  `upscale_*` for small/distant codes, `denoised` for noisy prints,
  `unwarp` for perspective tilt (it perspective-flattens the detected quad).

## Install

```bash
pip install "robustqr[cv]"        # classical engine + preprocessing
pip install "robustqr[wechat]"    # + DNN engine (the wrinkle-crusher)
pip install "robustqr[zbar]"      # + ZBar engine (needs libzbar0 system lib)
pip install "robustqr[all]"       # everything
```

Note: `opencv-contrib-python-headless` (wechat) and `opencv-python-headless`
(cv) are mutually exclusive — install one, not both.

## Use

```python
from robustqr import decode

r = decode("hoodie.jpg")
if r:
    print(r.data)            # the payload
    print(r.engine, r.variant)  # e.g. "wechat clahe"
    print(r.bbox)            # corner points, when known
```

```bash
# CLI
python -m robustqr hoodie.jpg --json
robustqr --engines   # check which engines are available
```

## API

- `decode(source)` → `DecodeResult | None` — first hit wins
- `decode_all(source)` → `list[DecodeResult]` — every hit, in attempt order
- `decode_file(path)` — convenience wrapper
- `engine_report()` — availability of every known engine

`source` is a file path or a BGR `numpy` array. Custom engine/variant
subsets: `decode(img, engines=[...], variants=["original", "clahe"])`.

## Tests

```bash
python tests/make_fixtures.py   # regenerate fixtures (needs qrcode)
python -m pytest tests/ -q
```

Fixtures include a **synthetic wrinkled-fabric QR** (drape + crease +
fold shading), tuned so the classical engines fail it and the DNN engine
decodes it — the hoodie incident, reproducible. 12 passed, 1 skipped
(the skip is pyzbar without system libzbar, by design).

## OpenCV version note

OpenCV 5.x changed the WeChat module's return signatures
(`detectAndDecode` returns 2 items, not 4; standalone `detect()` is gone).
robustqr handles both 4.x and 5.x.

## License

MIT — see [LICENSE](LICENSE).
