# 0003 — Stroke weight is compensated through the source's `wght` axis

Status: **permanent**. Depends on [0002](0002-advance-normalisation-is-an-identity.md).

## Context

Uniform scaling multiplies stroke weight along with size. Two scale groups
therefore produce two different colours on one line: hangul lands **+14.4%**
against the Latin stem and **+14.3%** against han. On a terminal row of mixed
Korean, Japanese and English that reads as the hangul being bolder, which is a
defect even though every glyph is individually correct.

## Decision

Instance the more-scaled script at a **lighter** `wght` so its post-scale stroke
matches. This uses the source's own design space rather than distorting
outlines: Pretendard ships a variable `wght` axis, and interpolating within it
is what its designers drew for.

Reference stem throughout: Iosevka's `|` — 0.0780 em Regular, 0.1120 em Bold.

Shipping values, against the parametric Latin at `shape = 500`:

| | scale | `wght` Regular | `wght` Bold |
|---|---|---|---|
| hangul | ×1.1571 | **403.7** | **585.8** |
| han / kana | ×1.0667 | **474.6** | **684.0** |

Result: the hangul/han stroke ratio goes native 1.0533 → uncompensated 1.1426 →
**compensated 1.0000**. The gate asserts hangul, han and Latin stems agree
within 8%; measured, all three sit at 1.000×.

## Cost

Lightening hangul narrows its ink slightly, which loosens the spacing 0002 was
built to win: `T` moves 0.1287 → 0.1363, **+5.9%**. Still 48% tighter than
Sarasa. The gate caps this rather than leaving it open — the measured `T` may
not exceed Pretendard's own by more than 10%.

Bold hangul needs one more correction. It is drawn wider as well as heavier, and
normalising the advance already leaves the widest syllables (썞 쌦 쏎 쎖 썏) at
0.97 of the cell against Sarasa's comfortable 0.870. Added weight pushes those
into contact, so Bold trims the horizontal scale by 1.1362 to buy the clearance
back — which is what a CJK design does anyway. Cost: hangul `T` 0.102 → 0.121 in
Bold, still under half of Sarasa's 0.264.

## Alternatives rejected

- **Accept the colour split.** It is the most visible defect in a mixed line.
- **Thin the outlines directly.** Distorts letterforms the source drew; the
  `wght` axis exists precisely so this is unnecessary.
- **Match by scaling less.** That is the uniform-scale option 0002 rejected.

## Downstream

The compensation is solved against the Latin stem, so it is only valid for the
Latin cut it was solved for. Changing Iosevka's `shape` invalidates these
numbers; changing `sb` or `cap` does not, because in Iosevka the stroke is set by
`shape` and is independent of both.

The weights above are constants in `scripts/build.py`, and the gate re-derives
the *result* — hangul, han and Latin stems within 8% of one another — from the
shipped binary on every build, so a stale constant fails rather than ships. What
that target should be is itself under review; see
[0014](0014-the-compensation-target-erases-the-source-relative-weighting.md).
