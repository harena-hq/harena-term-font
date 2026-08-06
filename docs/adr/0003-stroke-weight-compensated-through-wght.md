# 0003 — Stroke weight is compensated through the source's `wght` axis

Status: **the mechanism is permanent, the target was wrong** and was replaced by
[0014](0014-the-compensation-target-erases-the-source-relative-weighting.md).
Depends on [0002](0002-advance-normalisation-is-an-identity.md). The numbers
below are v0.9.0's; the reasoning that produced them is kept, because the error
is in it and is worth being able to find.

## Context

Uniform scaling multiplies stroke weight along with size. Two scale groups
therefore produce two different colours on one line: hangul lands **+14.4%**
against the Latin stem and **+14.3%** against han. On a terminal row of mixed
Korean, Japanese and English that reads as the hangul being bolder, which is a
defect even though every glyph is individually correct.

The first half of that is right and the second half is not, which took a
release to notice. Hangul running heavy against the **Latin** is this build's
doing. Hangul running heavy against **han** is Pretendard's doing, deliberately,
and the +14.3% is not an artefact to remove but the designer's decision measured
in the correct unit — see 0014, which shows it is `1.0533 × 1920/1770` exactly.

## Decision

Instance the more-scaled script at a **lighter** `wght` so its post-scale stroke
matches. This uses the source's own design space rather than distorting
outlines: Pretendard ships a variable `wght` axis, and interpolating within it
is what its designers drew for.

Reference stem throughout: Iosevka's `|` — 0.0780 em Regular, 0.1120 em Bold.

Values as shipped in v0.9.0, against the parametric Latin at `shape = 500`:

| | scale | `wght` Regular | `wght` Bold |
|---|---|---|---|
| hangul | ×1.1571 | 403.7 | 585.8 |
| han / kana | ×1.0667 | 474.6 | 684.0 |

Result: the hangul/han stroke ratio goes native 1.0533 → uncompensated 1.1426 →
**compensated 1.0000**. The gate asserts hangul, han and Latin stems agree
within 8%; measured, all three sit at 1.000×.

**That 1.0000 is the defect, not the result.** 0014 replaces the per-script
target with one source weight for the whole CJK — hangul 439.9/638.8, han/kana
440.6/632.6 — and the gate now asserts the source's ratio instead of parity.
The mechanism here is untouched: the correction still runs through the source's
`wght` axis, for the reasons given above, which is why this record stays.

## Cost

Lightening hangul narrows its ink slightly, which loosens the spacing 0002 was
built to win: `T` moves 0.1287 → 0.1363, **+5.9%**. Still 48% tighter than
Sarasa. The gate caps this rather than leaving it open — the measured `T` may
not exceed Pretendard's own by more than 10%.

Under 0014's target the sign flips: hangul is instanced *heavier*, its ink
widens, and `T` lands at 0.1260 — 2.1% **tighter** than Pretendard rather than
5.9% looser, and 52% tighter than Sarasa. The cap above is one-sided and was
always the right shape for it, since tighter is the direction this project is
travelling in; what bounds it going the other way is the cell-clearance check.

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

The weights are constants in `scripts/build.py`, and the gate re-derives the
*result* from the shipped binary on every build, so a stale constant fails
rather than ships. What it re-derives changed with 0014: the CJK still has to
sit within 8% of the Latin stem, but between the scripts the assertion is now
Pretendard's own ratio on both axes rather than parity on one.
