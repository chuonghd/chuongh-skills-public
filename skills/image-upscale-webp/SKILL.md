---
name: image-upscale-webp
description: Enlarge images with Upscayl (High Fidelity AI model) and make web WebP files with Squoosh's encoder at quality 85. Use whenever an image will be shown bigger than its source, when resizing or exporting images, mockups, cutouts or photos for the web, or when making any .webp file. Never enlarge with plain resizing (PIL, sharp, ImageMagick, CSS) and never make WebP with other encoders or defaults.
user-invocable: true
argument-hint: "[input] [output] [--width W | --height H | --size WxH]"
---

# Image upscale + WebP

Two rules, because outputs keep coming out worse than the source the user gave:

1. **Bigger than the source? Upscale with Upscayl first, then shrink to the exact size.**
   AI Model High Fidelity, 2x; 4x when 2x falls short of the target (repeat if still short).
   Then Lanczos down to the target. Never stretch with ordinary resizing.
2. **WebP only via Squoosh's encoder, quality 85**, with Squoosh.app's WebP settings
   (see `scripts/squoosh-webp-encode.mjs`). Encode once, at the very end.

## Commands

Write the Python path out in full (a hook blocks it inside a shell variable):

```bash
S=~/.claude/skills/image-upscale-webp/scripts
# to a target size (upscales only if needed); .png = lossless intermediate, .webp = final
~/.claude/skills/.venv/bin/python3 -I $S/upscale.py in.png out.webp --width 2400   # or --height H, --size WxH (same shape)
# WebP from an image that is already the right size (or larger: --width/--height shrink only)
~/.claude/skills/.venv/bin/python3 -I $S/encode_webp.py in.png [out.webp] [--quality 85] [--width W]
```

A 2000x2500 cutout to 2x takes about 30 s (Upscayl on the GPU), so give long runs a timeout.

Each prints its steps, e.g. `source 1200x1500 RGBA | upscayl 2x -> 2400x3000 | lanczos -> 2000x2500 | out.webp 412 KB`.

## Working rules

- **Start from the user's original file** (find it in `~/Downloads` etc. by name or size), never a
  copy pasted into chat: those are smaller, recompressed JPEGs.
- **Pick the target from the display size**: CSS px x 2 for retina. Upscale to that, not to "about".
- **Keep intermediates PNG.** Only the final file is WebP (or the format asked for). Never re-encode
  a lossy file into another lossy file.
- **Upscale before editing**, when an edited image will end up larger than its source: edits at the
  final resolution stay sharp; edits upscaled later get AI-smoothed.
- **Cutouts / transparency work.** Upscayl keeps the alpha channel and position exactly; it enlarges
  alpha with smooth bicubic (the AI works on colour). Shrinking uses premultiplied float Lanczos, so
  see-through colour never bleeds into edges.
- **Colour:** input is converted to sRGB (EXIF rotation applied); WebP is written untagged sRGB.
- **Check before calling it done:** open the result and the source side by side at 2x zoom on
  edges and fine texture. If the output looks softer than the source, find out why before moving on.

## Setup (already done on this Mac)

- Upscayl.app in `/Applications` (engine `Contents/Resources/bin/upscayl-bin`, models alongside).
  Override with `UPSCAYL_DIR`. Same arguments the app uses, so results match the app's
  "2x / High Fidelity" output (`*_upscayl_2x_high-fidelity-4x.png`).
- Node + `@jsquash/webp` 1.5.0 in this folder (`npm install` here if missing).
- Python 3 with `numpy` and `Pillow` (here: `~/.claude/skills/.venv`, used in the commands above).
