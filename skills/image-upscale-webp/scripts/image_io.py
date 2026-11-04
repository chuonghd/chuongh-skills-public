"""Shared image helpers for the image-upscale-webp skill: load any image as 8-bit sRGB, resize with
premultiplied alpha, run Upscayl, save PNG or Squoosh WebP."""
import os
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageOps

HERE = Path(__file__).resolve().parent
UPSCAYL_DIR = Path(os.environ.get("UPSCAYL_DIR", "/Applications/Upscayl.app/Contents/Resources"))
UPSCAYL_BIN = UPSCAYL_DIR / "bin" / "upscayl-bin"
UPSCAYL_MODELS = UPSCAYL_DIR / "models"
DEFAULT_MODEL = "high-fidelity-4x"   # Upscayl app: AI Model = High Fidelity
DEFAULT_WEBP_QUALITY = 85
SRGB = ImageCms.createProfile("sRGB")


def has_alpha(im):
    return im.mode in ("RGBA", "LA", "PA", "RGBa", "La") or (im.mode == "P" and "transparency" in im.info)


def load_srgb(path):
    """Open an image upright (EXIF orientation applied), converted to sRGB, as RGB or RGBA 8-bit.
    Web browsers show untagged WebP as sRGB, so wide-gamut (Display P3) photos must be converted."""
    im = ImageOps.exif_transpose(Image.open(path))
    icc = im.info.get("icc_profile")
    alpha = im.convert("RGBA").getchannel("A") if has_alpha(im) else None
    rgb = im.convert("RGB")
    if icc:
        src = ImageCms.ImageCmsProfile(BytesIO(icc))
        if "srgb" not in (ImageCms.getProfileDescription(src) or "").lower():
            rgb = ImageCms.profileToProfile(rgb, src, SRGB, renderingIntent=ImageCms.Intent.PERCEPTUAL)
    if alpha is not None:
        rgb.putalpha(alpha)
    return rgb


def resize(im, size):
    """Lanczos resize. RGBA is resized premultiplied in float, so see-through pixels' colour never
    bleeds into the edges (no light halo or dark fringe) and faint shadows keep their colour."""
    if im.size == tuple(size):
        return im
    if im.mode != "RGBA":
        return im.resize(size, Image.LANCZOS)
    arr = np.asarray(im, dtype=np.float32) / 255.0
    a = arr[..., 3]

    def rs(ch):
        return np.asarray(Image.fromarray(ch, "F").resize(size, Image.LANCZOS), dtype=np.float32)

    a2 = rs(a)   # unclipped: dividing by the same filter's alpha cancels its ringing exactly
    rgb = np.stack([rs(arr[..., c] * a) for c in range(3)], axis=-1)
    safe = np.where(a2 > 1e-4, a2, 1.0)[..., None]
    rgb = np.where(a2[..., None] > 1e-4, rgb / safe, 0.0)
    out = np.dstack([rgb.clip(0, 1), a2.clip(0, 1)])
    return Image.fromarray((out * 255.0 + 0.5).astype(np.uint8), "RGBA")


def upscayl(im, scale, model=DEFAULT_MODEL):
    """One Upscayl pass at 2x, 3x or 4x, same arguments the Upscayl app uses (-s when the scale
    differs from the model's 4x). Colour goes through the AI model; transparency is kept and
    enlarged with smooth bicubic resizing."""
    if not UPSCAYL_BIN.exists():
        raise SystemExit(f"Upscayl not found at {UPSCAYL_BIN} (install Upscayl.app or set UPSCAYL_DIR)")
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "in.png", Path(tmp) / "out.png"
        im.save(src)
        cmd = [str(UPSCAYL_BIN), "-i", str(src), "-o", str(dst), "-s", str(scale),
               "-m", str(UPSCAYL_MODELS), "-n", model, "-f", "png"]
        run = subprocess.run(cmd, capture_output=True, text=True)
        if run.returncode != 0 or not dst.exists():
            raise SystemExit(f"upscayl-bin failed ({run.returncode}):\n{run.stdout[-800:]}{run.stderr[-800:]}")
        out = Image.open(dst)
        out.load()
    want = (im.width * scale, im.height * scale)
    if out.size != want:
        raise SystemExit(f"upscayl-bin returned {out.size}, expected {want}")
    return out.convert("RGBA" if im.mode == "RGBA" else "RGB")


def encode_webp(im, out_path, quality=DEFAULT_WEBP_QUALITY):
    """Lossy WebP with Squoosh's libwebp and Squoosh.app settings (squoosh-webp-encode.mjs)."""
    node = shutil.which("node")
    if not node:
        raise SystemExit("node not found (needed for the Squoosh WebP encoder)")
    rgba = im.convert("RGBA")
    with tempfile.NamedTemporaryFile(suffix=".rgba") as raw:
        raw.write(rgba.tobytes())
        raw.flush()
        run = subprocess.run([node, str(HERE / "squoosh-webp-encode.mjs"), raw.name, str(rgba.width),
                              str(rgba.height), str(quality), str(out_path)], capture_output=True, text=True)
    if run.returncode != 0:
        hint = " (run `npm install` in the skill folder)" if "Cannot find" in run.stderr else ""
        raise SystemExit(f"WebP encode failed{hint}:\n{run.stderr[-800:]}")


def save(im, out_path, quality=DEFAULT_WEBP_QUALITY):
    """PNG (lossless, for intermediates) or WebP (final web output), chosen by extension."""
    out_path = Path(out_path)
    ext = out_path.suffix.lower()
    if ext == ".png":
        im.save(out_path, optimize=False, compress_level=6)
    elif ext == ".webp":
        encode_webp(im, out_path, quality)
    else:
        raise SystemExit(f"unsupported output {ext}: use .png (intermediate) or .webp (final)")
    return out_path
