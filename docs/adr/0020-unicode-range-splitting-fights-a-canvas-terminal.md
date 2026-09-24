# 0020 — unicode-range splitting fights a canvas terminal

Status: **declined, with a reopen trigger.** Nothing is split; the npm package
still ships one WOFF2 per cut and weight. This records the measurement so the
question is not re-opened from scratch, and states what would have to be true
to take it.

**Premise, stated because this repository has not recorded it before.** The
consuming application renders through xterm.js's WebGL addon. That matters:
xterm.js's own default renderer is `DomRenderer` — `browser/Terminal.ts:584`
instantiates it unconditionally, and `browser/renderer/` contains only `dom/`
and `shared/` — and a DOM renderer paints real text nodes through CSS
`font-family`, so the browser repaints them when a font resolves and none of
the defect below exists. The bitmap-caching machinery in `shared/` is reached
only by `@xterm/addon-webgl` and `@xterm/addon-canvas`. So this record applies
to a canvas-backed consumer, which is what we have, and not to xterm.js in
general.

## Context

The npm package serves 4.7 MiB of WOFF2 per cut at `font-display: block`, which
is the whole font for a terminal that mostly draws ASCII. `cn-font-split`
(HarfBuzz-based, splits a CJK font into `unicode-range` chunks and emits the
`@font-face` CSS) was raised as the obvious fix.

The size argument is real. Subsetting `dist/HarenaTermK-Regular.ttf` with
fontTools 4.63.0 — `Options(hinting=True, layout_features=["*"],
notdef_outline=True)`, `flavor="woff2"` — intersecting each range set with the
font's own `cmap`, and reporting KiB:

| subset | codepoints | KiB |
|---|---|---|
| **terminal-hot** | **637** | **35.0** |
| hangul | 11335 | 1280.1 |
| kana | 247 | 22.1 |
| han | 7491 | 1723.0 |
| **whole font, as shipped** | **37652** | **4730.1** |

Ranges, so the table can be re-derived — the standard
[0019](0019-the-hinting-failure-was-position-not-width.md) had to apply to
itself for the same reason:

- **terminal-hot** — U+0020–007E, U+00A0–00FF, U+2010–203A, U+2190–21FF,
  U+2500–259F, U+25A0–25FF, U+E0A0–E0D4. ASCII, Latin-1, general punctuation,
  arrows, box drawing, block elements, geometric shapes, powerline.
- **hangul** — U+1100–11FF, U+3130–318F, U+A960–A97F, U+AC00–D7FF.
- **kana** — U+3040–30FF, U+31F0–31FF, U+FF61–FF9F.
- **han** — U+3400–4DBF, U+4E00–9FFF, U+F900–FAFF, U+20000–3FFFF.

A terminal's first screen needs the first row. 35.0 KiB against 4730.1 KiB is
135×, and han — a third of the file — is a block nobody types into a shell.

## Splitting is byte-neutral, and the trap is not where the bytes are

Splitting costs essentially nothing in total transfer, at either granularity
measured. Summing complete partitions of the font's 37652 codepoints:

| chunks | total | vs monolith |
|---|---|---|
| 1 (shipping) | 4730.1 KiB | — |
| 3 — hot / hangul+kana / everything else | 4749.3 KiB | 1.004× |
| 5 — hot / hangul / kana / han / rest | 4739.7 KiB | 1.002× |

So the 135× figure belongs to *first paint* and must not be carried over to
total bytes, which do not move. Splitting buys latency and is paid for in
bookkeeping, not bandwidth.

**The trap is `ccmp`.** This font composes NFD hangul itself, through 11172
ligatures from conjoining jamo to precomposed syllables
([0007](0007-the-font-composes-nfd-hangul-itself.md)). Layout closure follows
those ligatures, so a bucket is disjoint in codepoints and not in glyphs:

```
subset of the 69 conjoining jamo alone   ->  11242 glyphs   1276.0 KiB
  the same 69 with layout_features=[]    ->      70 glyphs
"rest" bucket without the jamo (17942 cp) -> 18844 glyphs   1679.4 KiB
"rest" bucket with them      (18011 cp)   -> 30085 glyphs   2952.9 KiB
```

**69 codepoints cost 1273.5 KiB — a 76% increase in the chunk they land in.**
Whichever chunk gets U+1100–11FF gets the entire hangul block with it.

That is how the first draft of this section got its numbers wrong, and the
mistake is worth keeping. It claimed 6027.5 KiB and 1.27× for a five-way split
and built a "chunk count is the variable" argument on the contrast. The figure
came from a partition whose first bucket spanned U+0000–2FFF — which contains
the jamo — so the 11172 syllables were counted twice, once there and once in
the hangul bucket. The buckets were disjoint in codepoints, which is what was
checked, and overlapping in glyphs, which is what was billed. **0019's lesson,
repeated inside the record that cites it**: the number moved for a reason other
than the one being measured.

The surviving consequence is sharper than the discarded one. This record's
own five-way split avoids the trap — its `hangul` bucket keeps U+1100–11FF
co-located with U+AC00–D7FF, so the jamo and the syllables they compose sit in
the same chunk and nothing duplicates. What is untested is whether a splitter
that partitions by codepoint automatically, rather than by hand — which is what
`cn-font-split` does — can be trusted to draw that same boundary. Left to
itself it has no reason to keep jamo and syllables together, and the two
failure modes on either side of a wrong boundary are not symmetric: a chunk
that includes the jamo without the syllables they close over is normal
`hb-subset` behaviour and merely duplicates glyphs across chunks, cheaply; a
chunk that is told to *exclude* what closure would pull in breaks NFD
composition outright, which is the defect 0007 exists to prevent. Untested
here; it is the first question anyone building this has to answer.

## Hinting survives subsetting

This was the first suspicion, because
[0019](0019-the-hinting-failure-was-position-not-width.md) had just spent a
release on `-x 20 -X 15` and a subsetter that dropped bytecode would discard it
silently. It does not. Through `hb-subset`, which is `cn-font-split`'s own core:

- `fpgm`, `prep` and `cvt ` come out **byte-identical** to the shipped font;
- an ASCII subset (U+0020–007E, `hb-subset --notdef-outline`) comes out **100**
  glyphs, not 96 — `quotedbl`, `colon`, `semicolon`, `i` and `j` are composite
  glyphs and pull in the components they reference (`quotesingle`,
  `dotaccent`, `uniA78F`, …), which `layout_features` does not gate because
  composite inclusion is mandatory `glyf` structure, not a layout feature. Of
  those 100, every hint **program** is byte-identical to the source, `.notdef`
  included — it keeps its 83 bytes, never going to 0. The five composites
  print as "different" under a naive glyph-by-glyph diff only because
  subsetting renumbers glyph IDs and their component references move with it
  (`uniA78F` → `glyph00099`); the instructions themselves do not change;
- and it generalises further: on the full 11172-syllable hangul subset, `fpgm`,
  `prep` and `cvt ` are again byte-identical and **all 11172** syllable
  programs match.

Recording that matters as much as the objection that follows: the next reader
will suspect the same thing first.

## Why it does not ship

`unicode-range` is lazy by construction — the browser fetches a chunk when a
codepoint in its range is first *used*. For flowed HTML that is invisible: text
reflows and repaints when the chunk lands. A canvas renderer does not repaint.

In `@xterm/xterm` 5.5.0, this repository's own pinned version:

- `TextureAtlas` rasterises each glyph with `fillText` the first time it is seen
  and caches the bitmap in `_cacheMap` / `_cacheMapCombined`
  (`browser/renderer/shared/TextureAtlas.ts`);
- `document.fonts` appears **nowhere** in the package — no `loadingdone`
  listener, no `fonts.ready` await;
- and the cache survives every event that looks like it would flush it. Resize,
  `devicePixelRatio` change and an options change all route to
  `acquireTextureAtlas()` (`browser/renderer/shared/CharAtlasCache.ts:26`),
  which reuses an entry when `configEquals` holds. That function compares
  `devicePixelRatio`, `customGlyphs`, `lineHeight`, `letterSpacing`,
  `fontFamily`, `fontSize`, `fontWeight`, `fontWeightBold`,
  `allowTransparency`, `deviceCharWidth`, `deviceCharHeight`,
  `drawBoldTextInBrightColors`, `minimumContrastRatio`, and the foreground,
  background and 16 ANSI colours — and nothing else. Notably not the cell
  dimensions, which `ICharAtlasConfig` carries but `configEquals` never reads.
  A chunk finishing its download changes none of the compared fields: the CSS
  `font-family` string is the same string, and only the browser's internal font
  resolution moved. So a later resize or theme change does **not** clear the
  stale bitmaps either.

The only path that discards the cache is `clearTextureAtlas()`, exposed on the
renderer, and nothing in the library calls it when a font arrives.

So the first frame containing hangul rasterises in whatever fallback the browser
had at that instant, and that bitmap is what the atlas keeps. It is not a flash
that resolves. And because the fallback is not on this font's 1:2 grid, what
persists is a cell-alignment error, not merely a wrong typeface.

Measured from the source, not from a browser. The code path is unambiguous but
the artefact has not been reproduced on screen, and it should be before any of
this is built.

One limit on this evidence, stated rather than left to be discovered.
`@xterm/addon-webgl` is **not a dependency of this repository** at any depth, so
the addon source read here came from another checkout on the same machine, at a
version this repo does not pin. Nor is the addon a copy of what is pinned: it
vendors its own flat fork of the atlas code, and of the 8 files with
counterparts in `shared/` only 2 are byte-identical — `TextureAtlas.ts` differs
by 68 lines, and `CharAtlasCache.ts` and `CharAtlasUtils.ts` both thread a
`deviceMaxTextureSize` the core does not have. What transfers is narrower than
the file: `configEquals`'s compared-field list is byte-identical between the
two, and `document.fonts` is absent from both. The mechanism holds in the fork;
the code around it is not the same code.

## What the gate would not catch

`verify.py` discovers its subjects with `glob("dist/*.ttf")`. Every one of the
166 checks reads TTF. Split WOFF2 chunks would be artefacts that ship to users
and that the gate never opens — the shape
[0013](0013-the-width-table-must-cover-what-the-build-declares.md) and 0017 are
both instances of, arriving in a new place.

`package_npm.py` names its four WOFF2 files literally, and `SHA256SUMS` plus the
CI byte-reproduction check are written over exactly eight artefacts. None of
that is hard to extend; all of it has to be extended deliberately, and a
hundred-chunk split makes each of those a hundred-row problem.

## Decision

Do not adopt `cn-font-split`, and do not split per-chunk.

`cn-font-split` is declined on its mechanism, not for want of a flag: version
7.4.3's only display-related option is `css.fontDisplay`, which controls swap
timing *after* a chunk is already being fetched. It has no eager mode and emits
no `preload` tags, so `unicode-range`'s laziness is not something it can be
configured out of.

If the load cost becomes worth paying, the shape that fits this project is a
**three-way split done with the tools already pinned** — `hb-subset` is present
and fontTools is already a build dependency, so this adds no toolchain:

- `core`: the terminal-hot ranges above — 35.0 KiB
- `hangul` + `kana` — 1299.6 KiB
- everything else, han included — 3414.8 KiB

Three chunks are few enough to `preload` all of them, and preload is the point:
`<link rel="preload" as="font">` fetches eagerly regardless of whether a
codepoint in the range has been used, so the laziness that breaks the atlas is
gone while `unicode-range` still keeps ASCII painting off the han chunk's
arrival. At 1.004× the bytes are free.

What that does **not** do is eliminate the race, and the first draft of this
record said "sidesteps entirely", which was too strong. `font-display: block`
blocks for a limited period and then substitutes; if a preload has not resolved
by then, the browser paints a fallback and the atlas caches it exactly as
before. Preload removes the window `unicode-range`'s on-demand fetch created and
narrows what remains to a network race. Narrowing is not eliminating.

Nor is chunk ordering automatic. Three `preload` links at equal priority let a
3.4 MiB chunk compete with a 35 KiB one, and "the 35 KiB still paints first"
assumes a priority this record has not argued for. Whoever builds it should give
`core` `fetchpriority="high"` and measure, rather than trust link order.

The alternative mitigation — the consuming app listening on `document.fonts` and
calling `terminal.clearTextureAtlas()` — is available and is worse. It pushes
correctness of the font package into every consumer, and it buys a full-screen
re-rasterisation the first time the user types hangul.

## Reopen trigger

A measurement that the 4.7 MiB first load actually hurts in the Harena app —
not an assumption that it must. Or `unicode-range` becoming safe here, which
means xterm.js invalidating its atlas on font load; if that lands upstream, the
per-chunk split becomes ordinary and this record is what it overrides.

## The recurring shape

**A tool's core being sound says nothing about the seam it lands in.** The
subsetting is correct, the hinting survives, the sizes are what they promise.
The defect is entirely in the contract between lazy font loading and a renderer
that caches bitmaps — a place neither the font nor the subsetter can see.
