# 0014 — The compensation target erases the source's relative script weighting

Status: **accepted and applied**, on top of v0.9.0. Measured there, deliberately
not acted on there, and fixed in the tree that follows it.

**The two things 1.0.0 waited on are now one: Windows verification.** The third
condition, a real run of the release workflow, was met by v0.9.0.

Reproduce with `python3 scripts/probe_script_weight.py`, from a tree where
`fetch_sources.sh` has run and `dist/` is built.

## Context

A Sandoll article on building the CJK cuts of *IBM Plex Sans* KR and JP states
the principle this record is about:

> Fewer strokes must be drawn **thicker and smaller**; more strokes **thinner
> and larger**. Japanese sets katakana thickest and smallest and kanji thinnest
> and largest, because a glyph with few strokes reads as a hole in the page's
> grayness at the same weight.

The goal is not that strokes measure the same. It is that scripts **read** the
same. Those are different targets, and this build asserts the first.

[0003](0003-stroke-weight-compensated-through-wght.md) solves a source `wght`
per group so that each script's stroke matches the Latin stem after its scale.
Hangul scales ×1.1571 and han/kana ×1.0667 — different scales, so different
compensations — and the shared target is the Latin stem. Whatever relative
weighting the source designer built **between** scripts is therefore divided
out by construction.

## What was measured

Two probes. The first used single-stroke glyphs (`一` `丨` `ー` `ㅡ` `ㅣ`),
where an ink dimension *is* a stroke, and put the hangul/han error at ~5%. That
was an underestimate: one glyph per script is one sample, and those particular
glyphs may be tuned individually.

The second estimates mean stroke width across a wide sample as
`2 × area / perimeter` — exact for a ring of radii R,r (it returns R−r) and
stable across glyphs in a way a single probe is not. 81 hangul, 54 han, 45
katakana, 45 hiragana, against Pretendard JP instanced at the matching weight,
everything normalised by **advance** rather than by em, because the design was
squeezed into a cell and the cell is the unit that matters.

The estimator over-reads on glyphs with many terminals, but the same glyphs are
measured in both fonts, so the bias cancels in every ratio below.

### The relative weighting, source against ours

| ratio | source | ours |
|---|---|---|
| hangul / han, Regular | **1.135** | 1.013 |
| hangul / han, Bold | **1.153** | 1.007 |
| katakana / hangul, Regular | **0.971** | **1.130** |
| katakana / hangul, Bold | 1.057 | **1.207** |
| katakana / han, Regular | 1.102 | 1.144 |
| katakana / han, Bold | 1.219 | 1.216 |

Pretendard draws hangul 13.5–15.3% heavier than han, consistently in both
weights. That is the article's principle applied: hangul carries fewer strokes
per glyph than han, so it is drawn heavier to read at the same grayness. **This
build flattens it to ~1%.**

The katakana row is worse than flat — it is inverted. The source draws katakana
slightly *lighter* than hangul at Regular (0.971); here it is 13% *heavier*
(1.130), and 20.7% at Bold.

### Where the error enters

Absolute stroke width, advance normalised to 1000:

| Regular | ours | source | ours/source |
|---|---|---|---|
| hangul | 72.5 | 72.0 | 1.006 |
| han | 71.5 | 63.5 | **1.128** |
| katakana | 81.9 | 69.9 | **1.171** |
| hiragana | 80.3 | 68.7 | **1.169** |

| Bold | ours | source | ours/source |
|---|---|---|---|
| hangul | 94.1 | 109.7 | **0.858** |
| han | 93.4 | 95.1 | 0.982 |
| katakana | 113.5 | 115.9 | 0.980 |
| hiragana | 111.6 | 113.9 | 0.980 |

Regular thickens han and kana by 12–17% and leaves hangul alone; Bold thins
hangul by 14% and leaves the rest. Opposite corrections, one consequence:
**hangul reads light against everything it is set with.**

## What is *not* wrong, checked because it was the obvious suspect

What this reads as on screen is kana looking slightly larger beside hangul, with
`セットアップ` in particular looking wide and vertically squashed. Size and shape
are not the cause — both are reproduced from the source almost exactly:

| | ours | source |
|---|---|---|
| katakana / hangul, ink height | 0.841 | 0.835 |
| katakana / hangul, ink width | 0.945 | 0.938 |
| `セ` w/h | 1.133 | 1.133 |
| `ト` w/h | 0.805 | 0.795 |
| `プ` w/h | 1.025 | 1.027 |
| hangul w/h | 0.937 | 0.938 |

Katakana really is wide and short — w/h 1.053 against hangul's 0.938 — but that
is Pretendard's drawing, carried through unchanged. Vertical ink extents match
the source to a few units per mille as well. **What changed is weight alone**,
and a glyph of the same size with heavier strokes reads larger.

### Faithful to the source, and the source is an outlier

"Same as our source" answers whether the transform distorted anything. It does
not answer whether the shape is ordinary, which is the next question anyone
asks. Widening the comparison, on the katakana sample and `w/h`, a unit-free
ratio that survives differing upm and advances:

| | katakana w/h | ink width / advance | `ト` w/h |
|---|---|---|---|
| ours | **1.059** | 0.837 | 0.805 |
| Pretendard JP | **1.059** | 0.830 | 0.795 |
| M PLUS 1p | 1.029 | 0.785 | 0.785 |
| Noto Sans KR | 1.016 | 0.771 | **0.644** |
| Sarasa Term J / K | 1.016 | 0.771 | **0.644** |

Ours reproduces Pretendard to three decimals, and **Pretendard is the widest of
the five**. Its kana came from M PLUS 1p, which is already wider than the
Noto/Sarasa line, and Pretendard widened it a further 3%. `ト` is the extreme
case: 0.795 against 0.644, a 23% difference in one of the six glyphs that made
this look wrong in the first place.

A third component is not weight or shape at all, but the flagship decision:

| ink height / advance | hangul | katakana | katakana / hangul |
|---|---|---|---|
| ours | **0.932** | 0.794 | **0.852** |
| Pretendard JP | 0.931 | 0.788 | 0.847 |
| Sarasa Term K | 0.839 | 0.767 | **0.914** |

Sarasa sets hangul small in the cell, so its kana sits close to it. This build
fills the cell with hangul, which is the point of
[0002](0002-advance-normalisation-is-an-identity.md) — and the same faithfully
sized kana therefore reads **7% smaller beside it**. That ratio matches
Pretendard's own to 0.6%, so it is the source's proportion, not a defect. It is
simply not the proportion a reader arrives from Sarasa expecting.

So three things make `セットアップ` look wrong, and only the first is ours:
stroke weight (this record), Pretendard's unusually wide kana (the source's
drawing), and a smaller kana-to-hangul ratio (0002 working as designed). The
change specified below fixes the first alone. The second and third would mean
redrawing or non-uniformly scaling the kana, which trades away 0002's identity —
a different decision, on a defect nobody has yet shown to exist.

## Severity

The tempting way to rate this low is [0006](0006-two-regional-cuts-with-ss05-baked-in.md)'s
observation that Korean terminal text is effectively pure hangul, so hangul and
han rarely share a dense line. That argument is about hangul beside **han**. It
says nothing about hangul beside **kana**, which is the pairing the katakana row
above inverts — and that is the one a reader notices on screen, unprompted and
without any measurement in front of them.

## The arithmetic that settles it

0003 records the hangul/han stroke ratio moving `native 1.0533 → uncompensated
1.1426 → compensated 1.0000`, which reads as a scaling artefact being undone.
It is not one:

```
1.0533 × (1920 / 1770) = 1.1426          exact, not approximate
```

1920 and 1770 are the two scripts' source advances. **Those are the same drawing
measured in two units** — 1.0533 against the em, 1.1426 against the advance —
and [0002](0002-advance-normalisation-is-an-identity.md) already established
that the advance is the unit that means anything here, because both advances
land on the same cell. So "uncompensated 1.1426" was never a distortion to
remove. It is Pretendard's own inter-script weighting, seen in the only unit
that shows it. The compensation drove it to 1.0000 and called that precision.

The correction follows from the same identity. If holding the source's ratio
means expressing both groups at one source weight, then solving each group
independently should land them on the same number. Solved — the vertical stem
ratio on target, the page's overall colour held to v0.9.0 — it does:

| | hangul `wght` | han/kana `wght` | apart |
|---|---|---|---|
| Regular | **439.9** | **440.6** | 0.16% |
| Bold | **638.8** | **632.6** | 1.0% |

against v0.9.0's 403.7/474.6 and 585.8/684.0, which are 18% and 17% apart. The
two numbers are kept separate in `build.py` rather than merged, because they are
solved independently and nothing guarantees they stay this close if the Latin,
the scales or the source move.

## The change, as made

1. **One source weight for the CJK, not one target per script.** The Latin stem
   is still what the CJK is fitted to, but as a body rather than script by
   script. Stroke moves +6.5% on hangul and −6.2% on han/kana, so the page keeps
   its colour and only the relationship between the scripts changes.
2. **The gate retargeted.** `hangul stroke == han stroke` is gone. In its place
   the ratio is asserted against Pretendard's own, per weight.
3. **Horizontal strokes added to the gate**, on `ㅡ` against `一`. This was the
   step most easily skipped and it is the one that proves the approach: the
   horizontal ratio is *not* solved for, and it lands anyway.

Measured on the shipped bytes, all four faces:

| | vertical | source | horizontal | source |
|---|---|---|---|---|
| Regular | 1.1412 | 1.1426 | 0.9647 | 0.9690 |
| Bold | 1.1391 | 1.1461 | 0.9386 | 0.9449 |

Within 0.7% everywhere, on both axes. v0.9.0 sat at 1.0000/0.8652 and
0.9919/0.8115 — the vertical erased, the horizontal 11–14% off with nothing
watching it.

Note the two axes point opposite ways: hangul verticals run 14% heavier than
han's, its horizontals 3–6% lighter. A single number could never have expressed
that, which is the structural reason the old check was wrong and not merely
mis-valued.

The gate is 158/158. Letterspacing improves as a side effect — han `T` −4.3% →
−1.8% against Pretendard — because the correction moves ink rather than
position.

### Why it was deferred out of v0.9.0

Release hygiene, not doubt about the measurement. v0.9.0 was byte-reproducible
from pinned sources and gated at 154/154. This change alters every CJK outline
in all four faces and invalidates every hash in `SHA256SUMS`, so it belongs on
top of a released baseline where the diff is attributable to one decision —
not folded into a first release where it would be indistinguishable from
everything else.

## The recurring shape

This is one of the shapes catalogued in [README](README.md#recurring-shapes), and
the sharpest form of it: **a gate can assert the wrong thing.** The blind-spot
cases are about ranges the authority never listed. This one is listed, measured,
and asserted — at a value that erases a deliberate design decision. Passing at
`1.000×` reads as precision. It is the defect, written down as a requirement.

A second shape sits underneath it, and it is what hid the first for so long:
**two numbers in different units, compared as though they shared one.** 1.0533
and 1.1426 are one measurement, and reading their difference as damage done by
the build is what made a design decision look like an artefact worth removing.
The tell was available — 0002 had already ruled on which unit governs here —
and 0003 simply did not apply its own conclusion one section later.
