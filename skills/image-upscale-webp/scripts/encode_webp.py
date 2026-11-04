"""Convert an image to WebP with Squoosh's encoder and Squoosh.app settings (quality 85 by default),
optionally shrinking it first. Never enlarges: use upscale.py for that.

Usage: encode_webp.py IN [OUT.webp] [--quality 85] [--width W | --height H]
OUT defaults to IN with a .webp extension.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from image_io import DEFAULT_WEBP_QUALITY, load_srgb, resize, save


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("output", nargs="?")
    p.add_argument("--quality", type=int, default=DEFAULT_WEBP_QUALITY)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--width", type=int)
    g.add_argument("--height", type=int)
    args = p.parse_args()

    out = Path(args.output or Path(args.input).with_suffix(".webp"))
    if out.suffix.lower() != ".webp":
        raise SystemExit("output must end in .webp")
    im = load_srgb(args.input)
    w, h = im.size
    tw, th = (args.width, round(h * args.width / w)) if args.width else \
        (round(w * args.height / h), args.height) if args.height else (w, h)
    if tw > w or th > h:
        raise SystemExit(f"{w}x{h} -> {tw}x{th} would enlarge: use upscale.py instead")
    im = resize(im, (tw, th))
    save(im, out, args.quality)
    print(f"{out.name} {tw}x{th} {im.mode} q{args.quality} {out.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
