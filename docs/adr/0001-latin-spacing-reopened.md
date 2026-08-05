# 0001 — Latin letterspacing is set parametrically, never by scaling

Status: **permanent**.

## Context

The Latin base is treated as a finished system: a monospace face ships with its
spacing, stroke weight, hinting and box-drawing set already consistent with one
another, and rescaling any part of it breaks that consistency. Scaling the Latin
ink by the ×1.123 that would reach Pretendard's density also thickens its strokes
by 12.3%, which leaves text heavier than a box-drawing frame that cannot follow —
block elements must tile the cell exactly, so they cannot be rescaled at all.

That reasoning is about **scaling**, and it is the reason the CJK is fitted to the
Latin rather than the other way round.

It does not carry over to the parametric route. Iosevka is generated from
parameters, and `sb` (side bearing) is one of them: lowering it redraws the
letters wider at **unchanged stroke weight**. Nothing in the argument above is
violated by that, so the Latin's letterspacing is in scope after all — through
`metricOverride`, and only through it.

## Decision

The Latin's letterspacing is adjusted through `metricOverride.sb` in
`latin/private-build-plans.toml`, never by scaling outlines.

## Measured

One sample throughout: letters and digits, `T = (advance − ink) / ink`.

| | `sb` | mean ink | T | vs Pretendard |
|---|---|---|---|---|
| Pretendard 400, proportional | — | 0.4748 | **0.2116** | — |
| Iosevka stock | 60 | 0.3792 | 0.3184 | +50% |
| | 40 | 0.4215 | 0.1863 | **−12%, tighter** |
| | 45 | 0.4050 | 0.2345 | +11% |
| | 50 | 0.3963 | 0.2615 | +24% |

`sb = 40` overshoots: it makes the terminal Latin tighter than the proportional
face it is meant to sit beside, which reads as cramped.

The mean is not the whole story, and the two metrics disagree. What is actually
felt is the **widest letters**, whose gap is bounded below by `sb`:

| `sb` | min gap | p10 | median |
|---|---|---|---|
| 60 (stock) | 0.070 | 0.096 | 0.120 |
| 40 | 0.040 | 0.054 | 0.072 |
| 45 | 0.050 | 0.060 | 0.082 |
| 50 | 0.060 | 0.068 | 0.092 |

So 45 is closest on overall colour and 50 is closest on the extremes. In a fixed
cell those pull apart and no `sb` satisfies both; narrowing the letterforms is
the only move that helps both at once, and that is a different parameter.

## Alternatives rejected

- **Leave `sb` at Iosevka's default 60.** The Latin stays 50% looser than
  Pretendard, which forfeits the unification the parametric build exists for.
- **Scale the Latin instead.** Strokes thicken and the box-drawing frame cannot
  follow. See above.

## Downstream

`sb` is a build-plan parameter, so any future Latin cut must state it and
re-measure. The stroke is set by `shape` and is independent of both `sb` and
`cap`, so changing `sb` alone does not disturb the CJK weight compensation of
[0003](0003-stroke-weight-compensated-through-wght.md).
