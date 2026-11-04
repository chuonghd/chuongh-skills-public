"""Resize an image to a target size the right way: if the source is smaller than the target, enlarge
it with Upscayl (High Fidelity, 2x; 4x when 2x falls short; repeated if still short), then shrink
to the exact target with Lanczos. A source already big enough is only shrunk, never AI-processed.

Usage:
  upscale.py IN OUT (--width W | --height H | --size WxH) [--quality 85] [--model high-fidelity-4x]
OUT ending in .png is lossless; .webp is encoded with Squoosh settings at --quality.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from image_io import DEFAULT_MODEL, DEFAULT_WEBP_QUALITY, load_srgb, resize, save, upscayl

ASPECT_TOLERANCE = 0.005   # --size may differ from the source's shape by 0.5% (rounding); more needs a crop


def target_size(src, args):
    w, h = src
    if args.width:
        return args.width, max(1, round(h * args.width / w))
    if args.height:
        return max(1, round(w * args.height / h)), args.height
    tw, th = (int(v) for v in args.size.lower().split("x"))
    if abs((tw / th) / (w / h) - 1) > ASPECT_TOLERANCE:
        raise SystemExit(f"--size {tw}x{th} has a different shape from the source {w}x{h}: crop first")
    return tw, th


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("output")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--width", type=int)
    g.add_argument("--height", type=int)
    g.add_argument("--size", help="WxH, same shape as the source")
    p.add_argument("--quality", type=int, default=DEFAULT_WEBP_QUALITY, help="WebP quality (default 85)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    args = p.parse_args()

    im = load_srgb(args.input)
    tw, th = target_size(im.size, args)
    steps = [f"source {im.width}x{im.height} {im.mode}"]
    while im.width < tw or im.height < th:
        need = max(tw / im.width, th / im.height)
        scale = 2 if need <= 2 else 4
        im = upscayl(im, scale, args.model)
        steps.append(f"upscayl {scale}x -> {im.width}x{im.height}")
    if im.size != (tw, th):
        im = resize(im, (tw, th))
        steps.append(f"lanczos -> {tw}x{th}")
    out = save(im, args.output, args.quality)
    steps.append(f"{out.name} {out.stat().st_size / 1024:.0f} KB")
    print(" | ".join(steps))


if __name__ == "__main__":
    main()
