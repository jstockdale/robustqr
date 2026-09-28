"""Command-line interface: ``python -m robustqr image.png [...]``."""

import argparse
import json
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="robustqr",
        description="Robust QR decoder: preprocessing variants x decoder engines, first success wins.",
    )
    parser.add_argument("images", nargs="*", help="image files to decode")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--all", action="store_true", help="report every hit, not just the first")
    parser.add_argument("--engines", action="store_true", help="list engine availability and exit")
    args = parser.parse_args(argv)

    from .pipeline import decode, decode_all, engine_report

    if args.engines:
        print(engine_report())
        return 0
    if not args.images:
        parser.print_help()
        return 2

    failed = False
    for path in args.images:
        try:
            hits = decode_all(path)
        except Exception as exc:
            failed = True
            print(f"{path}: ERROR {exc}", file=sys.stderr)
            continue
        if not hits:
            failed = True
            if not args.json:
                print(f"{path}: no QR decoded")
            continue
        show = hits if args.all else hits[:1]
        if args.json:
            for h in show:
                print(json.dumps({
                    "path": path, "data": h.data, "engine": h.engine,
                    "variant": h.variant, "bbox": h.bbox,
                }))
        else:
            for h in show:
                print(f"{path}: {h.data}  [engine={h.engine} variant={h.variant}]")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
