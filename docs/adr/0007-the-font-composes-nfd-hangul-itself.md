# 0007 — The font composes NFD hangul itself, because the shaper cannot be trusted to

Status: **permanent**. Also records why one obvious way to test this proves
nothing.

## Context

macOS stores filenames in **NFD**. Every Korean filename arrives as conjoining
jamo — `한` is `U+1112 U+1161 U+11AB`, not `U+D55C`. A terminal that lists a
directory on macOS is handling NFD hangul constantly.

Two separate things have to be true for that to render.

**Coverage, so the run stays in this face.** Chromium selects a font by `cmap`
coverage *before* shaping, so a face missing the jamo hands the whole run to a
fallback. `add_jamo()` registers the 67 modern jamo — 19 choseong, 21 jungseong,
27 jongseong — with advances following the shaping model: the lead carries the
full two cells, the vowel and tail are zero.

**Composition, so the three jamo become one syllable.** This is the part that is
easy to assume someone else does.

## Why the shaper cannot be relied on

HarfBuzz has a Hangul shaper that composes onto the precomposed syllables, which
makes it tempting to conclude that 11172 ligature entries would buy nothing.

**A test through HarfBuzz cannot support that conclusion.** Its Hangul shaper
normalises the buffer *before any lookup runs*, so the font is handed an
already-composed syllable and its own composition is never exercised. Feeding NFD
to `hb-shape` and getting the right glyph back proves the shaper works, not the
font.

CoreText has no Hangul shaper. It composes only what the font composes — which is
how Apple's own Korean faces do it, through an AAT `morx` state machine. Given a
font with neither, the three jamo are drawn on top of one another, because the
width model gives the lead the whole advance and leaves the vowel and tail at
zero.

Visible by taking the Hangul shaper out of the way:

```
NFD U+1112 1161 11AB  --script=hang  [gid29337=0+1000]                          ✓
NFD U+1112 1161 11AB  --script=Zyyy  [gid29992=0+1000|gid29993=1+0|gid30017=2+0] ✗
```

Note that Pretendard itself registers **no conjoining jamo at all**, so on macOS
it hands NFD hangul to a fallback and never has this exposure. Covering the jamo
is what makes the composition ours to provide.

## Decision

`add_jamo_ccmp()` builds the composition as `ccmp` ligatures, in the two stages
Unicode's own algorithm uses:

```
L + V   → LV syllable      19 × 21  =   399 rules
LV + T  → LVT syllable     399 × 27 = 10773 rules
                                      -----
                                      11172
```

The intermediate LV is a real glyph this font already has. Lookups apply in
`LookupList` index order, not feature order, so the two are appended in that
sequence. Registered under `hang` as well as the inherited `DFLT`, since an
engine that finds the run's own script in the font may never consult the default.

Attached to the existing `ccmp` feature records rather than a new one: the
`FeatureList` is ordered by tag and every `LangSys` refers to features by index,
so inserting one would renumber references across the table.

## What the gate asserts

Three assertions, none of which can be satisfied by a shaper doing the work:

1. walk the `ccmp` ligature tree directly and exhaustively — all 11172 syllables
   must resolve to their precomposed glyph
2. `ccmp` must be reachable under the `hang` script
3. `hb-shape` must collapse NFD to NFC with the Hangul shaper both **engaged and
   bypassed** (`--script=hang` and `--script=Zyyy`)

Survives hinting: `ccmp` is checked intact in the ttfautohint output.

## The general rule

**A test that runs through a layer which fixes the defect is not a test.** The
same shape appears again in the width table that drives the build: a range it
omits is a range the gate cannot check, so its absence reads as a pass. See
[0013](0013-the-width-table-must-cover-what-the-build-declares.md).

## Not covered

The 184 archaic jamo are deliberately not registered — there is no glyph for them
here, and a blank in `cmap` would turn a visible fallback into silent data loss.
`U+115F` / `U+1160` are blanks because those fillers are supposed to be
invisible. Halfwidth jamo U+FFA0–FFDC is 0: Pretendard has no halfwidth forms and
the compatibility glyphs are the wrong proportion for a single cell.
