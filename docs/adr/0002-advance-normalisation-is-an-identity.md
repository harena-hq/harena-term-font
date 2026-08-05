# 0002 — Per-script advance normalisation reproduces the source's spacing exactly

Status: **permanent**.

## Context

A monospace CJK font normally sets every CJK glyph to one cell width and lets
the letterspacing fall where it falls. That discards the source's own spacing,
and it is why Sarasa Term K's hangul sits at `T = 0.264` where proportional
Pretendard sits at `0.1287` — more than twice as loose. Closing that gap is the
reason this project exists.

The useful property is that **Pretendard's CJK advances are already uniform
within each script**: every hangul syllable is 1770 units at upm 2048 (0.8643
em), every han and kana glyph is 1920 (0.9375 em).

`T = (advance − ink) / ink` is scale-invariant. So if a whole script is scaled
by one factor, `T` does not move. Choosing that factor to land the script's
native advance exactly on the two-cell box therefore **reproduces the source's
own letterspacing as an identity**, not as an approximation.

## Decision

Scale each script by `cell / native_advance`, computed in source font units:

| script | native | scale | resulting T | Pretendard's own T |
|---|---|---|---|---|
| hangul | 1770 | ×1.1571 | 0.1287 | **0.1287** |
| han | 1920 | ×1.0667 | 0.0925 | **0.0925** |
| kana | 1920 | ×1.0667 | 0.1871 | **0.1871** |

Two scale groups, because hangul and han/kana have different native advances.
That is a design judgement, not a build flag: it is the only arrangement that
gives both scripts their own spacing.

## Alternatives rejected

- **One uniform ×1.0667 for all CJK.** Tempting — one scale group, Pretendard's
  inter-script proportions preserved untouched, hangul height barely moving
  (h/cap 1.247 against Sarasa's 1.218), han ink landing on Sarasa's 0.916
  exactly. But hangul `T` only reaches **0.224**, still 74% looser than
  Pretendard, which forfeits the stated first priority.
- **Per-glyph fitting.** Would break the identity: `T` is only preserved when one
  factor covers a whole script.

## Accepted cost

Hangul reads about 10% taller against the Latin than in Sarasa (h/cap 1.346
against 1.218 before the parametric Latin raised `cap`). Direct consequence of
prioritising spacing. Clearance to collision is measured, not assumed: the gate
scans every full-width glyph and asserts hangul and han stay at or below 0.99 of
the cell, and that nothing anywhere exceeds 1.0.

## Downstream

The scale is derived from the **source advance in font units**, never from the
em-relative figure. At upm 2048 → 1000 the em figure rounds, and a rounded scale
would put the advance a unit off the cell, which accumulates across a terminal
row. Anything that changes the CJK source must re-read `native_adv` rather than
reuse 1770 / 1920.
