# Flex Web To AE — browser extension

Capture any live web page and rebuild it in After Effects as **native, editable
layers**: real text layers with real fonts, real shape layers with editable
paths, fills, strokes and corner radii — not a screenshot.

## Install (Chrome, Edge, Brave, Arc — anything Chromium)

1. Open **After Effects**, open the **Flex GUI Pro** panel, and switch to
   **FX & ADVANCED RIGS → WEB→AE**. The panel opens the local link the extension
   talks to; it only runs while the panel is open.
2. In the browser go to `chrome://extensions`.
3. Turn on **Developer mode** (top right).
4. Click **Load unpacked** and choose this folder:

   ```
   /Library/Application Support/Adobe/CEP/extensions/Flex GUI Pro/browser_extension/flex_web_capture
   ```

5. Pin the extension if you want the toolbar button.

The panel's **EXTENSION** button opens this folder in Finder for you.

## Sending a page

Three ways, all the same thing:

- the floating **Send to AE** pill in the bottom-right of any page,
- the toolbar icon → **Send this page to After Effects**,
- <kbd>Alt</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd>.

The dot on the pill is the live connection: green means After Effects is
listening, red means the panel isn't open (or is on another tab).

<kbd>Alt</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd> hides or shows the pill. You can
also drag it — it snaps to the nearest corner and remembers where you put it.

Then switch to After Effects: the capture appears in the **WEB→AE** tab. Pick
your options and hit **Build In After Effects**.

## Options (the caret on the pill, or the toolbar popup)

| Option | What it does |
|---|---|
| **Full page** | Scrolls the whole page first so lazy-loaded images and reveal-on-scroll sections exist before measuring. Off = just what's on screen. |
| **Images & icons** | Fetches artwork and inline SVG. Off gives a much smaller, faster capture. |
| **One layer per text line** | Exact layout, one layer per line. Off (default) keeps each paragraph as a single editable text layer with the browser's line breaks baked in. |
| **On-page button** | Show or hide the floating pill. |
| **Panel port** | Only change this if 45327 is taken; the panel reports the port it actually bound. |

## How it fits together

```
content.js ──▶ capture_engine.js        walks the DOM, measures everything
     │
     ▼
background.js                            fetches images cross-origin,
     │                                   POSTs to the panel
     ▼
web2ae_bridge.js  (in the AE panel)      127.0.0.1 only, writes the capture
     │                                   to ~/Documents/Flex/web2ae/
     ▼
web2ae.js         (the WEB→AE tab)       preview, options, font check
     │
     ▼
web2ae_host.jsx   (After Effects)        builds the native layers
```

The network work is in `background.js` on purpose: a content script's `fetch` is
treated as coming from the page, so a page's own CSP blocks the call to
localhost and a CDN without CORS headers blocks the images. The service worker
is subject to neither.

## What comes across

- **Text** → text layers with font family/weight/style, size, tracking, leading,
  justification and colour. Positioned by **baseline**, which both the browser
  and After Effects agree on exactly, so nothing drifts when a font substitutes.
- **Boxes, cards, buttons** → shape layers with a real bezier path, so each
  corner keeps its own radius (AE's Rectangle has only one Roundness value).
  Fills, borders → strokes, and `box-shadow` → Drop Shadow.
- **Gradients** → a solid with a Gradient Ramp masked to the element's outline.
  After Effects does not expose gradient stops to scripting at all, so a shape
  layer's gradient fill cannot be set; this keeps every part editable and
  actually looks like the page.
- **Images** → imported and scaled, with `object-fit: cover` masked to its box.
- **Inline SVG** → converted to real shape layers via *Create Shapes from Vector
  Layer* (falls back to the imported vector if the menu command isn't found).
- **Hierarchy** → layers are named after the element, colour-labelled by type,
  and parented to their container (or grouped under nulls).

## Known limits

- **Web fonts are not installed fonts.** A font the browser downloaded doesn't
  exist in After Effects. The panel tells you which will substitute, and lets you
  choose the replacement per family and weight.
- **CSS generics** (`sans-serif`, `monospace`) resolve to the closest real
  installed face — the page never said which font it actually got.
- Gradients keep their first and last stop; middle stops are noted in the layer
  comment.
- `conic-gradient`, backdrop filters, blend modes and CSS animations do not come
  across.
- `chrome://`, the Web Store and other privileged pages cannot be captured by any
  extension.

## Privacy

The capture never leaves the machine. It goes to `127.0.0.1` only — never
`0.0.0.0` — so nothing on the network can reach the panel, and it is written to
`~/Documents/Flex/web2ae/`. Nothing is built in After Effects until you click
**Build**.
