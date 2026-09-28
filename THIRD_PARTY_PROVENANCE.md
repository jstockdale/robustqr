# Third-party license provenance

This document records every third-party component robustqr touches and
verifies that releasing robustqr under **MIT**, **BSD-3-Clause**, or
**GPL-3.0-only** is clear in all three cases.

## Our own code

All code under `robustqr/` and `tests/` (excluding generated fixtures) is
original, written for this project. Copyright holder: John Stockdale.
No third-party code is copied or vendored into this repository.

## Runtime dependencies

| Package | Version pinned in dev | SPDX license | Notes |
|---|---|---|---|
| numpy | 2.5.3 | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` | Permissive bundle |
| pillow | 12.3.0 | `MIT-CMU` | Permissive |
| opencv-contrib-python-headless (`[wechat]` extra) | 5.0.0.93 | `Apache-2.0` | Includes WeChat QR DNN models, also Apache-2.0 (WeChatCV/opencv_3rdparty) |
| pyzbar (`[zbar]` extra) | 0.1.9 | `MIT` | Python wrapper only |
| libzbar0 (system library, *not* bundled) | system | `LGPL-2.1` | Optional runtime dep for the zbar engine; dynamically linked, never distributed with robustqr |

## Dev / test-only dependencies

| Package | SPDX license | Notes |
|---|---|---|
| qrcode (fixture generator) | `BSD-3-Clause` | Only used to *generate* test fixtures; fixtures themselves are our own artifacts |
| pytest | `MIT` | Test runner |

## Compatibility matrix

"Can robustqr be released under X given these dependencies?"

| Release license | numpy | pillow | opencv-contrib (Apache-2.0) | pyzbar (MIT) | libzbar (LGPL-2.1, optional) | Verdict |
|---|---|---|---|---|---|---|
| MIT | ✅ | ✅ | ✅ | ✅ | ✅ (dynamic link, not distributed) | **Clear** |
| BSD-3-Clause | ✅ | ✅ | ✅ | ✅ | ✅ (dynamic link, not distributed) | **Clear** |
| GPL-3.0-only | ✅ | ✅ | ✅ (Apache-2.0 is GPLv3-compatible) | ✅ | ✅ (LGPL-2.1 permits relicense to GPLv3; optional dep) | **Clear** |

Notes:

- **Apache-2.0 → GPLv3** is explicitly compatible (this is why GPL *v3*,
  not v2, is on the options list — Apache-2.0 is *not* GPLv2-compatible).
- **WeChat QR models**: the CNN models bundled inside the
  opencv-contrib wheel are licensed Apache-2.0 per WeChatCV
  (see WeChatCV/opencv_3rdparty). They ship *inside the dependency*,
  not in this repo; users get them by installing the `[wechat]` extra.
- **libzbar**: LGPL-2.1 system library. robustqr never bundles it; the
  zbar engine `dlopen`s whatever the host provides. LGPL permits this
  from any license, including proprietary — so it constrains nothing.
- **Test fixtures** (`tests/fixtures/*.png`) were generated locally with
  the `qrcode` package from the fixed string
  `https://example.com/robustqr-test`. They are original artifacts of
  this project, not third-party content.
- No GPL/AGPL *code* is linked, vendored, or required by any
  configuration of this package.

## Staged license texts

`LICENSES/` holds the full texts of all three candidate licenses
(REUSE convention). The release choice is a one-line change:
copy the chosen file to `LICENSE` and set `project.license` /
the classifier in `pyproject.toml`.

- `LICENSES/MIT.txt` — permissive; max adoption, incl. proprietary use
- `LICENSES/BSD-3-Clause.txt` — permissive; like MIT plus a no-endorsement clause
- `LICENSES/GPL-3.0-only.txt` — copyleft; derivatives must stay open
