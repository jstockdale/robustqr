# robustqr

**The QR decoder that keeps trying where others give up.**

Most QR libraries try one decoder, once, and shrug. robustqr tries a whole
grid — *preprocessing variants × decoder engines* — and returns the first
success, telling you exactly which combination cracked it.

```python
from robustqr import decode

r = decode("wrinkled-hoodie.jpg")
print(r.data)             # https://example.com/...
print(r.engine, r.variant)  # wechat clahe  ← the combo that won
```

## The story

This library exists because of a hoodie. A wrinkled QR code printed on
fabric defeated `pyzbar` and plain OpenCV completely. OpenCV's contrib
**WeChat detector** (a small DNN, of all things) finally read it — but only
from the flatter photos, and only after contrast enhancement. So instead of
betting on one decoder and one preprocessing step, robustqr bets on all of
them:

```
input image
 ├── variants: original → clahe → upscale → denoise → unwarp …
 └── engines (strongest first): wechat → opencv → pyzbar
        → first success wins, stamped with (engine, variant, bbox)
```

On the original hoodie photos it decodes **2 out of 3** — including one
that the bare WeChat detector couldn't read on its own. The wrinkle that
started it all is immortalized as a synthetic test fixture
(`tests/fixtures/wrinkled.png`: drape + crease + fold shading), tuned until
the classical engines fail it and the DNN decodes it. The hoodie incident,
reproducible.

## Install

```bash
pip install "robustqr[cv]"        # classical engine + preprocessing
pip install "robustqr[wechat]"    # + the DNN engine (the wrinkle-crusher) ⭐
pip install "robustqr[zbar]"      # + ZBar engine (needs libzbar0 on your system)
pip install "robustqr[all]"       # everything
```

> `opencv-contrib-python-headless` (wechat) and `opencv-python-headless`
> (cv) are mutually exclusive — install one, not both. If you're not sure,
> pick `[wechat]`: it's the whole reason this library exists.

Check what's usable in your environment:

```bash
robustqr --engines
```

Engines whose dependencies are missing don't crash your import — they're
simply listed as unavailable and skipped. (Looking at you, libzbar.)

## Use it

**Python:**

```python
from robustqr import decode, decode_all

r = decode("photo.jpg")          # first hit, or None
all_hits = decode_all("photo.jpg")  # every hit, in attempt order

# source can also be a BGR numpy array (hello, OpenCV pipelines)
# constrain the search space if you're in a hurry:
r = decode(img, engines=[...], variants=["original", "clahe"])
```

Each `DecodeResult` carries `data`, `engine`, `variant`, `bbox` (corner
points when known), and `raw` bytes.

**CLI:**

```bash
robustqr hoodie.jpg                    # human-readable
robustqr *.jpg --json                  # machine-readable
robustqr --all photo.jpg               # every hit, not just the first
```

## How it thinks

**Engines** (tried strongest-first):

| Engine | What it is | Needs |
|---|---|---|
| `wechat` | OpenCV contrib DNN detector — laughs at wrinkles, folds, perspective | `opencv-contrib-python` |
| `opencv` | Classical `QRCodeDetector` — fast, great on clean codes | `opencv-python` |
| `pyzbar` | ZBar wrapper — excellent on clean codes | `pyzbar` + system `libzbar0` |

**Variants** (each targets a failure mode):

| Variant | For when… |
|---|---|
| `original` | the code is fine, actually |
| `clahe` | washed-out / uneven lighting (this one cracked the hoodie) |
| `upscale_15` / `upscale_20` | small or distant codes |
| `denoised` | noisy prints |
| `unwarp` | perspective tilt — flattens the detected quad first |

## For contributors

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all,dev]"
python tests/make_fixtures.py   # regenerate fixtures
python -m pytest tests/ -q      # 12 passed, 1 skipped (pyzbar w/o libzbar)
```

Engines implement a tiny interface (`name`, `available`, `decode(image)`),
so adding a new one is a ~30-line affair — PRs welcome. One compatibility
note: OpenCV 5.x changed the WeChat module's return shapes; the adapter
handles both 4.x and 5.x.

## License

Take your pick — all three are staged in [`LICENSES/`](LICENSES/) with full
provenance verified in [`THIRD_PARTY_PROVENANCE.md`](THIRD_PARTY_PROVENANCE.md):

- **MIT** — do anything, just keep the notice
- **BSD-3-Clause** — like MIT, plus "don't imply we endorse you"
- **GPL-3.0-only** — share alike; derivatives stay open

Every dependency (numpy, pillow, opencv-contrib incl. the WeChat models,
pyzbar, qrcode, pytest) is permissive and compatible with all three —
verified, not assumed. The one copyleft-ish piece in the orbit, system
`libzbar` (LGPL-2.1), is an optional runtime link, never bundled.

---

*Born from a wrinkled hoodie at 1 AM. Some libraries are written; this one
was negotiated with.*
