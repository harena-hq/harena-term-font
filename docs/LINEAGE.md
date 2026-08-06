# Lineage — where the letterforms came from, and what was done to them

Every glyph in this font passed through at least one other designer's hands
before ours. This traces each path: the origin, what the intermediate did to it,
what this build did on top, and why.

`COVERAGE.md` says *which* source each codepoint came from. This says *what
happened to it on the way*.

All figures are measured from the actual binaries unless marked otherwise.

---

## The shape of it

```
Adobe / Google
  Source Han Sans ──┬─────────────────────────► Pretendard JP ──┐
   (Noto Sans CJK)  │   hangul, han                             │
                    │                                           ├─► Harena Term
                    └─────────────────────────────────────────► │
                        enclosed forms, archaic jamo — direct    │
                                                                 │
M+ FONTS Project                                                 │
  M PLUS 1p ────────┬─────────────────────────► Pretendard JP ──┘
                    │   kana                                     
                    └─────────────────────────────────────────► brackets,
                                                                 halfwidth kana

Renzhi Li
  Iosevka ──────────► parametric rebuild ─────────────────────► Latin, symbols
                       (our build plan)
  + Nerd Fonts patch ─────────────────────────────────────────► 14 icon sets
```

Two sources reach us **twice** — once filtered through Pretendard, once
directly. That is the interesting part of the lineage and the source of most of
the tuning below.

---

## Source Han Sans → Pretendard JP → hangul and han

**Origin.** Source Han Sans, by Adobe with Google, shipped by Google as Noto
Sans CJK. Pretendard's own name table credits it for hangul and han. Its licence
carries Adobe's Reserved Font Name `Source`; we use glyphs, never the name.

**What Pretendard did.** Redrew and re-spaced them to sit with Inter, which is
the Latin it is built around. The letterforms survive that closely — measured
against the shipped face at 96px, our hangul matches Noto Sans KR at IoU **0.915**
and Pretendard at **0.916**. They are the same drawings.

Pretendard set them at uniform advances **within each script**: hangul
`1770/2048` = 0.8643 em, han `1920/2048` = 0.9375 em.

**What we did, and why.** That uniformity is the lever. `T = (advance − ink)/ink`
is scale-invariant, so scaling a whole script by one factor does not move its
letterspacing. Choosing the factor that lands the script's native advance
exactly on the two-cell box therefore **reproduces Pretendard's own spacing as
an identity, not an approximation**:

| script | native | our scale | resulting T | Pretendard's own T |
|---|---|---|---|---|
| hangul | 1770 | ×1.1571 | 0.1287 | **0.1287** |
| han | 1920 | ×1.0667 | 0.0925 | **0.0925** |

*Intent:* the whole project exists because monospace CJK normally discards the
source's spacing and lets it fall where the cell puts it. Sarasa's hangul sits
at `T` 0.264 against Pretendard's 0.1287 — more than twice as loose. See
[ADR 0002](adr/0002-advance-normalisation-is-an-identity.md).

**The cost, and the second correction.** Two scales mean two stroke weights on
one line: hangul lands +14.4% against the Latin stem. So each script is
instanced at a *lighter* `wght` that cancels it — using Pretendard's own design
space rather than distorting outlines:

| | scale | `wght` Regular | `wght` Bold |
|---|---|---|---|
| hangul | ×1.1571 | 403.7 | 585.8 |
| han / kana | ×1.0667 | 474.6 | 684.0 |

Result in v0.9.0: hangul/han stroke ratio 1.0533 native → 1.1426 uncompensated
→ **1.0000**, at a cost of +5.9% on hangul `T`. That target was wrong — the
1.1426 is the source's own weighting rather than a scaling artefact — and
[ADR 0014](adr/0014-the-compensation-target-erases-the-source-relative-weighting.md)
replaced it with one source weight for the whole CJK: hangul 439.9/638.8,
han/kana 440.6/632.6, ratio restored to 1.1412 and `T` tightened to 0.1260. Bold
hangul additionally takes ×1.1362 horizontally, because added weight pushed the
widest syllables (썞 쌦 쏎) into contact with the cell wall. See
[ADR 0003](adr/0003-stroke-weight-compensated-through-wght.md).

---

## M PLUS 1p → Pretendard JP → kana

**Origin.** M PLUS 1p, by the M+ FONTS Project. Pretendard's name table credits
it for kana, and measurement agrees: against our shipped kana, M PLUS scores
**0.739** where Source Han scores 0.608. The kana are the one part of Pretendard
that is *not* Source Han.

**What Pretendard did — and it is not a resize.** The usual description, which
this repository also used to give, is that Pretendard scaled M PLUS down by
about 0.9572. Measured, that is a single number standing in for a relationship
that is not uniform:

| | ink width | ink height | advance |
|---|---|---|---|
| M PLUS 1p kana | 0.8057 em | 0.7939 em | 1.0000 em |
| Pretendard JP kana | 0.7897 em | 0.7556 em | 0.9375 em |
| ratio | **0.980** | **0.952** | 0.9375 |

The ink barely moved horizontally. **What Pretendard actually did was narrow the
box** — 6.25% — while leaving the drawing nearly its original width. That is
what tightened the kana: `T` went 0.2605 → 0.2037.

*Why it matters here:* our advance normalisation then reproduces *Pretendard's*
tightened spacing, not M PLUS's original. The kana you see are M PLUS
letterforms at M PLUS's proportions in Pretendard's rhythm.

---

## M PLUS 1p → directly → brackets, halfwidth katakana, five symbols

**Why a direct path exists at all.** Pretendard is an Inter-based *proportional*
face. It draws the CJK brackets for proportional setting and ships no `palt` to
tighten the box, so in a grid they sit at **0.221** of the cell — against
Sarasa's 0.315. M PLUS is fuller than either at **0.383**. It also has 〇 〒 〓,
which Pretendard lacks entirely, and draws 〈 〉 at a full-width advance where
Pretendard's are 698 units against the cell's 1920.

And it has all 63 halfwidth katakana at advance 500 of its 1000 em — **genuinely
half-width, not a full-width glyph to be squeezed**.

*Intent:* take from the source the kana already came from rather than introduce a
stranger. 89 glyphs.

**Our tuning: `MPLUS_SCALE = 1.0211`**, intended as Pretendard's resize composed
with our ×1.0667, so a glyph taken straight from M PLUS lands where one that
arrived through Pretendard does.

> **Honest note, and it was checked.** Since the Pretendard–M PLUS relationship
> is not a uniform scale, no single factor reproduces it. Matching ink *height*
> gives 0.952 × 1.0667 = **1.0152**; matching ink *width* gives
> 0.980 × 1.0667 = **1.0455**. The shipped 1.0211 sits near the height-matched
> value, so arithmetic alone leaves open whether the brackets sit ~2% small
> against the kana.
>
> **Read on screen, 2026-07-31, in the shipped face at terminal size.** Four
> things were looked for and none of them was there: the brackets read the right
> size beside kana, their strokes do not read thinner, they sit at the right
> height in the cell, and they do not disagree with any one script — kana, han
> or hangul — more than another. The specimen alternated `「あ」「い」「う」`,
> which is where a size mismatch shows first.
>
> Closed. The value stands, and the reason it is right is that the brackets were
> chosen on cell fill — 0.383 against Pretendard's 0.221 and Sarasa's 0.315 —
> not on matching the kana. Reopen only if a future change to the kana scale
> moves them apart.

---

## Source Han Sans → directly → enclosed forms and archaic jamo

**Why a direct path exists.** Pretendard has 81 of the enclosed and squared
forms but draws **every one proportionally**, at 2280–3638 units against the
cell's 1920. Fitting those to the grid needs 0.53×–0.84× horizontal compression,
which would turn ㈜'s enclosing circle into an ellipse. That is distortion, not
scaling, and this project refuses it.

A CJK-native font has no such problem: all 544 sit at exactly one em in Noto.

**This is not a fourth letterform system** — it is the well our hangul and han
came from in the first place. Against the shipped face:

| source | hangul | han | kana |
|---|---:|---:|---:|
| Pretendard JP — our primary source | 0.916 | 0.848 | 0.845 |
| **Noto Sans KR — Source Han Sans** | **0.915** | 0.892 | 0.608 |
| M PLUS 1p — already grafted from | — | 0.680 | 0.739 |

Noto is closer to what we ship than M PLUS 1p is, and we already graft from
M PLUS. (The han column flatters Noto: our han are instanced at `wght` 474.6, so
comparing both at 400 is not like for like. The hangul column is the solid one.)

**Our tuning.** Two transforms, each solved against the shipped face rather than
assumed — `wght` to match ink area, scale to match ink height, `dy` to match the
optical centre:

| | `wght` | scale | `dy` | matched against |
|---|---|---|---|---|
| enclosed and squared, U+3200–33FF | 440 / 640 | 0.9993 / 0.9992 | +11 | our han |
| archaic compatibility jamo, U+3165–318E | 480 / 700 | 1.0988 / 1.0779 | −1 | our hangul |

The jamo scale is larger because Noto sets hangul at 920 of its 1000 em against
our 1000 cell — the identity of ADR 0002 again, applied to a different source.

*Why one source for the whole family:* ㈱ and ㈲ were briefly taken from M PLUS
1 Code, which has those two and not ㈹. Measured, its enclosure is 1.3% wider
with a 10% thinner bracket, so ㈹ beside them would have read as a different
design. Noto draws all three identically. M PLUS 1 Code was dropped.

---

## Iosevka → parametric rebuild → Latin, symbols, everything half-width

**Origin.** Iosevka, by Renzhi Li. Taken as the Nerd Fonts *patched* build, which
adds 14 separately licensed icon sets — see `THIRD_PARTY_NOTICES.md`, which
carries each one's licence and copyright.

**Why this base.** Not letterform preference. Two measured constraints:

1. **Braille.** U+2800–28FF is complete in Iosevka and **0/256** in JetBrains
   Mono, Geist, IBM Plex, Monaspace, Hack and IntelOne. Agent TUIs emit a
   Braille spinner.
2. **The ceiling.** Achievable hangul density is `R × (cap/2a) × (ink_w/ink_h)`,
   and `cap/2a` — the Latin cap height against the CJK cell — caps it. Iosevka's
   0.500 advance gives 0.735, the highest of everything surveyed; a 0.600 base
   drops it to ~0.59 and produces hangul **more than twice as loose as Sarasa**.
   See [ADR 0004](adr/0004-latin-advance-sets-the-hangul-ceiling.md).

**What we did.** Iosevka is generated from parameters, so the Latin is rebuilt
rather than scaled — which changes the drawing at **unchanged stroke weight**,
where scaling would thicken the strokes and leave text heavier than a
box-drawing frame that cannot follow.

| parameter | stock | ours | intent |
|---|---|---|---|
| `cap` | 735 | **808** | raises `cap/2a`, bringing hangul/cap to 1.23 without touching the hangul |
| `xHeight` | 520 | **572** | held proportional to `cap` |
| `sb` | 60 | **45** | letterspacing onto Pretendard's — `T` 0.318 → 0.212 against Pretendard's 0.2116 |
| `leading` | 1250 | **1350** | hangul ink is 0.99 em; raising `cap` alone does not buy back the row spacing |
| `shape` | 400 | **500** | drawn heavier while still declared Regular — matches apparent weight at 13px against Pretendard at 15px |

*The `shape`/`menu` split is deliberate*: the letters are drawn at weight 500 and
reported to the OS as 400. See [ADR 0001](adr/0001-latin-spacing-reopened.md) and
`latin/README.md`.

**Taken untouched otherwise.** Box drawing, block elements, geometric shapes,
arrows, Braille and Powerline keep Iosevka's own spacing and hinting — block
elements in particular must tile the cell exactly, so nothing may rescale them.

---

## What we deliberately did *not* take

- **Pretendard's Latin.** It derives from Inter and is drawn for proportional
  setting. The Latin here is entirely Iosevka.
- **Pretendard's enclosed and squared forms** — proportional, see above.
- **Any third han source.** Pretendard JP's 7138 covers JIS X 0208, cp932 and
  KS X 1001 completely; what is missing is rare name-kanji and Chinese-only
  hanzi, and Chinese is an explicit non-goal. See
  [ADR 0005](adr/0005-cjk-source-stays-pretendard-jp.md).
- **☎ ☏ ♨.** One cell per the provider, full-width in every source, and halving
  a full-width design halves its stroke — even at Noto's maximum `wght` it
  reaches 0.46× the Latin stem. See PLAN.md D8.

---

## Reading the numbers

Every ratio here was measured, not estimated. The ones that decide whether a
build is correct — advances, letterspacing `T`, stroke ratios, cell clearance,
coverage counts — are re-derived from the shipped binary by `scripts/verify.py`
on every build, which fails if any of them has drifted. `coverage_table.py`
regenerates the per-block source attribution in
[`COVERAGE.md`](COVERAGE.md) the same way.

The remaining figures come from one-off surveys against source corpora that this
repository does not fetch: the twelve-candidate Latin comparison in
[ADR 0004](adr/0004-latin-advance-sets-the-hangul-ceiling.md), the `sb` sweep in
[0001](adr/0001-latin-spacing-reopened.md), the M PLUS 1 Code evaluation in
[0005](adr/0005-cjk-source-stays-pretendard-jp.md) and the Windows hinting probe
in [0010](adr/0010-ttfautohint-hints-y-only.md). Each is stated with the sample
size and the method that produced it, so it can be re-run against the same
corpus. The one that ships its own script is
[0014](adr/0014-the-compensation-target-erases-the-source-relative-weighting.md),
because it needs only what `fetch_sources.sh` already downloads.
