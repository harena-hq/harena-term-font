# 0017 — Windows verified, and what the screenshots do not settle

Status: **accepted**. Closes the last of the three conditions
[CHANGELOG](../../CHANGELOG.md#why-0x) set for 1.0.0.

## What was run

| | |
|---|---|
| terminal | Windows Terminal 1.24.11911.0, Windows PowerShell |
| face | Harena Term K, Regular and Bold, from the ADR 0014 build |
| reported | size 11, 100% scale, 2560 × 1600 — over Remote Desktop |
| measured | em 29.5 device px, i.e. **200%**; see below |
| method | `Get-Content -Encoding utf8 sample.txt`, three PNG captures |

Nothing was installed but the four TTFs; the sample is `docs/sample.txt`
verbatim.

## What it settles

Measured off the captures rather than eyeballed, since "looks right" is what a
gate exists to replace.

**The grid holds.** The 48-column frame in block 4 has its right edge at exactly
the same x on the top border, all six mixed-script content rows, and the bottom
border — hangul beside Latin, han beside Latin, halfwidth katakana beside
fullwidth Latin, a timestamp, and a code line with Korean comments. Zero column
shear. This was the risk that mattered: DirectWrite could have rounded advances
per run and sheared rows that macOS keeps straight.

**Ambiguous width agrees.** The 40-column ruler and the 40-column symbol row end
within 2 px of one another (614 and 616 against a 14.75 px cell). Windows
Terminal resolves those characters to one cell, which is what this font draws —
so the disagreement documented in the README is with a *setting*, not with the
platform default.

**NFD composes.** The NFC and NFD lines are indistinguishable. The `ccmp`
ligature tree runs under DirectWrite as it does under CoreText.

**Box drawing joins.** Double, heavy and rounded frames all close at the
corners, the three weights are visibly distinct from one another, and the block
ramp tiles with no seam. Braille renders.

**Bold shares Regular's advances.** Differencing the Regular and Bold captures
pixel by pixel gives ink in identical positions with only the stroke weight
changed — no accumulated drift along the row, which is the failure a font with
a mis-set Bold advance would produce.

**0014's fix is visible on screen.** Hangul reads heavier than the kana beside
it, which is the relationship Pretendard draws and the one v0.9.0 inverted. It
was measured on outlines; this is the first time it has been seen rendered by
an engine that was not the one it was designed on.

## What it does not settle, and this is the honest part

**The size the captures were taken at is not the size that was set.** The
session was a Remote Desktop one with its scaling set to 100%, but the setting
did not reach the renderer: RDP forwards the *client's* scale factor, and the
client's won.

The captures are their own evidence for this, so it is measured rather than
inferred from the reported settings — which is the point, since the reported
settings were wrong.

| | |
|---|---|
| adjacent identical columns, ink only | **0.5%** |
| adjacent identical rows, ink only | **1.8%** |
| stem profile across one row | `204 204 204 165 12` — one AA edge |

A nearest-neighbour ×2 upscale would put both duplication figures near 50%, a
×1.35 near 26%. At 0.5% the PNGs are **device pixels, not a resampled bitmap**,
which makes the measurements below real rather than an artefact of the capture:
the cell is 14.75 px and the em 29.5. Size 11 at 96 DPI gives an em of 14.67.
The ratio is **2.00** — the session rendered DPI-aware at 200%.

That also disposes of the reported 2560 × 1600: a 3456 px wide window cannot
exist on a 2560 px desktop.

That matters because **ttfautohint's grid-fitting is what
[0010](0010-ttfautohint-hints-y-only.md) bought, and it earns its keep below
about 16 px per em.** At 29.5 px — twice the size that was asked for — there is
so much room that hinting barely arbitrates.

So the split is clean. **Layout is closed at every size**, because advances are
integers and do not care what the em is. **Rendering is closed only at the size
shown**, and that size is the one where hinting matters least.

Two smaller gaps, recorded rather than waved past:

- **conhost (GDI) was not run.** ttfautohint's default `-a qsq` gives GDI the
  strong mode and DirectWrite the quantized one, so they are deliberately not
  the same rendering. Only the second was seen. The first attempt mojibaked,
  which is worth recording because it looks like a font defect and is not one:
  conhost decodes output with the system ANSI code page — 949 on a Korean
  install — and this sample is UTF-8. `chcp 65001` first. The sample now says
  so in its own header. Telling a reader to run a file that garbles on the
  platform's default console is an instruction that fails in a way that blames
  the font.
- **Word was not run.** The `OS/2` codepage bits are asserted by the gate and
  their point is that Word may set East Asian text in this face; that has never
  been observed, only declared.

Neither blocks 1.0.0. The condition set in the CHANGELOG was TUI rendering
without column shear, including the Braille spinner and the box-drawn frames,
and that is exactly what these captures show.

## What the run caught

Block 8 of `docs/sample.txt` was titled "NERD FONT ICONS — Powerline and the
icon sets" and **contained no Nerd Font glyph at all** — its content was `✔ ⚡ ⚪
⚫`, four ordinary Unicode symbols, against 3518 private-use glyphs in the font
including all 40 Powerline separators. On screen it rendered as a nearly empty
line, so a reader checking icon coverage would have concluded the font has none.

Fixed with real separators and icon-set glyphs, every one width-checked against
the shipped `hmtx`. Same shape as the defect this file's own block 6 had before
release: **a check whose title claims more than its body tests, which is worse
than an absent check because it reports success.**

## Downstream

The trigger to reopen this is a new rendering path rather than a new version:
Windows Terminal changing its text renderer, or a report of shear from conhost,
WSL under a different terminal, or a DPI setting not covered here. A capture at
100% scale and 11 px or smaller would close the hinting question that this one
leaves open, and is worth taking if anyone runs the font at that size.
