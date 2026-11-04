// Encodes raw RGBA pixels to WebP with Squoosh's libwebp build (@jsquash/webp), using
// Squoosh.app's exact WebP encoder settings (only quality differs).
// Called by encode_webp.py, which does all decoding and colour handling.
//
// Usage: node squoosh-webp-encode.mjs <raw-rgba-file> <width> <height> <quality> <out.webp>
import { readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'

// Squoosh.app WebP "Advanced settings" (libwebp WebPConfig fields). Every field is explicit so
// results never drift with the library's own defaults.
const SQUOOSH_WEBP_OPTIONS = {
  lossless: 0,
  method: 4, // Effort
  quality: 85,
  alpha_compression: 1,
  alpha_quality: 100,
  alpha_filtering: 1,
  autofilter: 0,
  filter_strength: 60,
  filter_type: 1, // Strong filter
  filter_sharpness: 7,
  use_sharp_yuv: 0,
  pass: 1,
  sns_strength: 50, // Spatial noise shaping
  preprocessing: 0,
  segments: 4,
  partitions: 0,
  exact: 0, // Preserve transparent data
  // Not exposed in the Squoosh UI; libwebp defaults.
  target_size: 0,
  target_PSNR: 0,
  show_compressed: 0,
  partition_limit: 0,
  image_hint: 0,
  emulate_jpeg_size: 0,
  thread_level: 0,
  low_memory: 0,
  near_lossless: 100,
  use_delta_palette: 0,
}

const [rawPath, width, height, quality, outPath] = process.argv.slice(2)
if (!outPath) {
  console.error('usage: squoosh-webp-encode.mjs <raw-rgba> <width> <height> <quality> <out.webp>')
  process.exit(2)
}

// jsquash fetches its Wasm by URL, which Node can't do for file: URLs, so hand it the module.
const require = createRequire(import.meta.url)
const encodePath = require.resolve('@jsquash/webp/encode')
const { default: encode, init } = await import(encodePath)
const wasm = readFileSync(new URL('./codec/enc/webp_enc_simd.wasm', 'file://' + encodePath))
await init(await WebAssembly.compile(wasm))

const w = Number(width), h = Number(height)
const data = new Uint8ClampedArray(readFileSync(rawPath).buffer)
if (data.length !== w * h * 4) throw new Error(`raw size ${data.length} != ${w}x${h}x4`)
const out = await encode({ data, width: w, height: h, colorSpace: 'srgb' }, { ...SQUOOSH_WEBP_OPTIONS, quality: Number(quality) })
writeFileSync(outPath, Buffer.from(out))
