# 0010 — ttfautohint hints in y only; the `-a` search space is closed

Status: **partly superseded**. The decision to leave `-a` alone survives; the
ground given for it, and the instruction to ship ttfautohint's defaults, do not.
The reopen trigger below fired — see
[0019](0019-the-hinting-failure-was-position-not-width.md).

## Context

The CJK arrives here as outlines — glyphs are imported through a pen and scaled,
which drops the source's instructions, and they would be wrong after scaling
anyway. So the merged font carries Iosevka's hinting on the Latin and symbols and
nothing at all on the ~19000 CJK glyphs. macOS does not care; CoreText largely
ignores TrueType instructions. ClearType does: GDI and DirectWrite grid-fit from
them at small sizes.

ttfautohint fills that gap and is used with its defaults, chosen after comparing
four cuts on Windows (`qsq`/`sss` × x-height inflation). Strong stem snapping
evens the strokes *inside* a glyph — the three bars of ㅍ — and then lets a
single glyph jump a pixel band and read bolder than its neighbours. Quantized
does the reverse. Inter-glyph uniformity mattered more to the reader, so `qsq`
ships.

Windows 11 Notepad then rendered the faces visibly worse than Windows Terminal
did. The hypothesis was ttfautohint's grayscale stem-width slot, so a cut was
built with `-a nsq` and tested. **It read identically in both applications.**

## The null result is structural

Measured as stroke crest intensity against the unhinted build of the same source
— 255 means the stroke landed exactly on the pixel grid. Over hangul:

| ppem | horizontal, unhinted → hinted | vertical, unhinted → hinted |
|---:|---|---|
| 13 | 186.3 → 222.0 **+35.7** | 201.1 → 208.9 +7.8 |
| 15 | 203.2 → 231.4 **+28.2** | 217.4 → 217.5 **+0.1** |
| 17 | 212.8 → 233.7 **+20.9** | 222.9 → 222.4 **−0.5** |

**ttfautohint hints in y only.** Horizontal strokes gain +21 to +36; vertical
strokes gain nothing. No `-a` value changes that: its three slots select stem
*width* quantisation, and for a y-only autohinter stem width is the thickness of
a horizontal stroke.

Measured against the shipping cut, the `-a nsq` build differs in **2 bytes of
`prep`** and nothing else — `glyf` (every glyph program), `fpgm` and `cvt`
are byte-identical, because `-a` compiles to a constant that `prep` branches on
at runtime.

## Why the two applications differ

ClearType gives 3× subpixel resolution in the **horizontal** direction —
precisely the axis the hinting leaves alone — so Windows Terminal covers for the
missing hints. Notepad is WinUI 3 and renders text with grayscale
antialiasing, where nothing does.

Mean |horizontal − vertical| gap over ppem 13–17: **ours ≈11, Sarasa ≈4.6**.
Sarasa's CJK hinting reaches x; ours cannot.

## Decision

**Do not sweep `-a` combinations** — the avenue is closed by the tool's design,
not by a near miss.

~~Ship ttfautohint defaults.~~ Superseded: the build passes `-x 20 -X 15`, which
act on blue-zone rounding rather than stem width. See the addendum below and
[0019](0019-the-hinting-failure-was-position-not-width.md).

The tool that could fix this is Microsoft Visual TrueType, which is free (GUI
closed and Windows-only; the compilers are MIT at `microsoft/VisualTrueType`).
It can hint x and pin every stroke to a shared CVT entry, which makes both
uniformity and vertical crispness structural. It needs hinting source per glyph,
so at 19000 CJK glyphs that means writing a generator — days, not hours.

## Trigger to reopen

A complaint about rendering **in a terminal**. The Notepad case is the only place
this has been seen, and a WinUI 3 text box is not what this font is for.

Where a browser-based terminal rasterises glyphs to an *opaque* Canvas2D surface,
Chromium's condition for letting Skia use LCD subpixel antialiasing is met, and
that is the favourable case — checked on Windows and acceptable. A transparent
surface falls back to grayscale, where the missing x hints show.

## Reopened, and what survived

The trigger fired: `텰` read as `뎔` in a terminal at 15 and 16 ppem. `-a` was
swept again, in contradiction of the instruction above, and the instruction was
the thing that turned out to be wrong. It was written unqualified from a single
cut, `-a nsq`, and generalised.

Two results, both in [0019](0019-the-hinting-failure-was-position-not-width.md):

- The `-a nsq` cut compared above moves slot 1, **grayscale**. The renderer
  takes slot 3, DirectWrite. That is why it read identically — the null result
  was real but it measured a slot nothing was using.
- Slot 3 does change the render, and does not fix the defect: the failure is a
  stroke *position* rounding to zero height, which stem-width quantisation
  cannot reach. It masks one symptom and costs glyph-to-glyph uniformity,
  exactly the trade this ADR weighed.

So `-a` keeps its shipping value, but not for the reason given here. "No `-a`
value changes that" is false of slot 3; what is true is that the change it makes
does not fix the defect and costs uniformity. And the bare instruction to "ship
ttfautohint defaults" no longer holds at all: the build passes `-x 20 -X 15`,
which act on blue-zone rounding rather than stem width.
