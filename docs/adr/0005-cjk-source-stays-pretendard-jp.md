# 0005 — The CJK source stays Pretendard JP; M PLUS 1 Code is not a better fit

Status: **permanent**. Records the han-coverage decision and the M PLUS 1 Code evaluation.

## Context

Two questions keep arriving together, and both rest on a wrong premise about the
lineage. What Pretendard's own name table says:

- **hangul and han** — Noto Sans CJK / Source Han Sans
- **kana** — M PLUS 1p
- Latin base glyphs — Inter

So the han are *not* M PLUS. Measured against Sarasa after size normalisation,
IoU is 0.951 for hangul and 0.950 for han — the same drawings. Kana are the
exception at 0.585 / 0.526, which is exactly the M PLUS provenance showing.
(An earlier claim that Pretendard's kanji were *not* Source Han, argued from
contour counts — 鬱 at 26 against 8 — was wrong: Sarasa's build merges overlaps.)

The two questions:

1. Han coverage is 7138 against Sarasa's 20992. Is that a regression?
2. M PLUS ships **M PLUS 1 Code**, a monospace redesign. For a monospace font,
   would that not be the better source for kana and brackets?

## Decision on coverage: accept 7138, graft nothing

The 7138 is not an arbitrary subset:

| set | covered |
|---|---|
| JIS X 0208 kanji | **6356 / 6356** |
| cp932 (incl. NEC/IBM extensions) | **6682 / 6682** |
| KS X 1001 hanja | **4620 / 4620** |
| JIS X 0212 supplement | 597 / 5801 |
| JIS X 0213 level 3–4 | 81 / 567 |

Practical Japanese and Korean are complete. What is lost is rare name-kanji and
Chinese-only hanzi, and Chinese coverage is an explicit non-goal. Grafting a
third source would import a fourth set of letterforms to reconcile, for glyphs
that will essentially never render.

## Decision on M PLUS 1 Code: no

**The monospace property buys nothing here.** This build does not use the
source's advance at all — [0002](0002-advance-normalisation-is-an-identity.md)
scales each script so its native advance lands exactly on the two-cell box. M
PLUS 1 Code happens to be upm 1000 with Latin 500 and CJK 1000, i.e. already on
our grid, so the scale would be 1.0 instead of 1.0667. Same result. What matters
is the drawing, not the metrics.

And the drawings have converged. Kana, `T = (advance − ink) / ink`:

| source | T | mean ink height |
|---|---|---|
| M PLUS 1 Code w400 | 0.2064 | 0.8074 em |
| M PLUS 1p, unmodified | 0.2605 | 0.7939 em |
| Pretendard JP w399, ×1.0667 | 0.2037 | 0.8059 em |
| **Harena Term K, shipped** | **0.1957** | **0.8111 em** |

Pretendard tightened M PLUS 1p's kana from 0.2605 to 0.2037 when it adopted
them. M PLUS later redesigned for code and arrived at 0.2064. Two independent
paths to the same place — both pulled by the full-width box. What ships is 5%
tighter than M PLUS 1 Code and 0.5% taller: below perception.

Two reasons it would be actively worse:

**Bracket coverage.** Brackets are the only thing taken from M PLUS directly
(see the graft in `scripts/build.py`), and M PLUS 1 Code has 6 of the 18:

```
        「 」 『 』 【 】 〔 〕 〘 〙 〚 〛 （ ） ［ ］ ｛ ｝
1 Code   o  o  o  o  .  .  .  .  .  .  .  .  o  o  .  .  .  .    6/18
1p       o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o   18/18
```

Fill is identical where both have a glyph (「 at 0.383 either way), so there is
no quality gain to offset the loss.

**Harmony.** The han are Source Han Sans. Pretendard's kana were already sized
and weighted against those han by its designers. Grafting M PLUS 1 Code kana raw
discards that tuning and leaves the same cross-family pairing, so it adds work
without fixing anything. M PLUS 1 Code also carries 5289 han and no hangul, so
it cannot serve any other role.

## Downstream

The general trap: **a monospace source is not an advantage to a monospace build
when the build normalises advances.** Any future source is judged on letterform
proportion, coverage and harmony with the han — never on whether it is already
fixed-width.
