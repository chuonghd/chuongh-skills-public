"""Logo and favicon for the usage report, as inline SVG so the page stays one standalone file.

The mark: white crop corners framing a white dot, on a vivid orange tile
with rounded corners. The frame is an image being made; the dot is a coin for what it cost.
The page logo and the favicon are the same drawing, bold enough to read at 16px.
"""

import base64

TILE = "#ff6a13"
INK = "#ffffff"

_SHAPES = (f'<rect width="256" height="256" rx="60" fill="{TILE}"/>'
           f'<g transform="translate(36 36) scale(.71875)" fill="{INK}">'
           '<path d="M16 112V16h96v36H52v60zM240 144v96h-96v-36h60v-60z"/>'
           f'<circle cx="128" cy="128" r="50"/></g>')

LOGO_SVG = f'<svg class="brand-logo" viewBox="0 0 256 256" role="img" aria-label="Image generation usage logo">{_SHAPES}</svg>'
FAVICON_SVG = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">{_SHAPES}</svg>'
FAVICON_LINK = ('<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,'
                + base64.b64encode(FAVICON_SVG.encode()).decode() + '">')

CSS = """
  .brand { display:flex; align-items:center; gap:16px; }
  .brand-logo { width:48px; height:48px; flex:none; }
"""
