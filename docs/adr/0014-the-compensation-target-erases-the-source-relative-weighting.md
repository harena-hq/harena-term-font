# 0014 — The compensation target erases the source's relative script weighting

Status: **open**. Measured, reproduced, and deliberately not acted on in v0.9.0 —
the change lands on top of a released baseline rather than inside the first
release, for the reason given at the end.

**This is one of the two things 1.0.0 is waiting on.** The other is Windows
verification; the third condition, a real run of the release workflow, was met
by v0.9.0.

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

## Severity

The tempting way to rate this low is [0006](0006-two-regional-cuts-with-ss05-baked-in.md)'s
observation that Korean terminal text is effectively pure hangul, so hangul and
han rarely share a dense line. That argument is about hangul beside **han**. It
says nothing about hangul beside **kana**, which is the pairing the katakana row
above inverts — and that is the one a reader notices on screen, unprompted and
without any measurement in front of them.

## The change, specified but not made

1. Stop targeting the Latin stem for every script. Anchor one script to the
   Latin and hold the **source's** ratios for the others. With hangul as the
   anchor: han 0.881 of hangul, katakana 0.971, hiragana 0.982.
2. Retarget the gate. It currently asserts `hangul stroke == han stroke` and
   passes at 1.000x, so it does not merely miss this — **it enforces it.** An
   assertion that locks in a defect is worse than an absent one.
3. Add horizontal strokes to the gate. It measures vertical stems only, and
   the largest divergences are horizontal.

Deferred deliberately, and the reason is release hygiene rather than doubt about
the measurement. v0.9.0 is byte-reproducible from pinned sources and gated at
154/154. This change alters every CJK outline in all four faces and invalidates
every hash in `SHA256SUMS`, so it belongs on top of a released baseline where the
diff is attributable to one decision — not folded into a first release where it
would be indistinguishable from everything else.

## The recurring shape

This is one of the shapes catalogued in [README](README.md#recurring-shapes), and
the sharpest form of it: **a gate can assert the wrong thing.** The blind-spot
cases are about ranges the authority never listed. This one is listed, measured,
and asserted — at a value that erases a deliberate design decision. Passing at
`1.000×` reads as precision. It is the defect, written down as a requirement.
