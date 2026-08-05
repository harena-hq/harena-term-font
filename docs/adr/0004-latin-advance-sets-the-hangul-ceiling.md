# 0004 — The Latin advance sets a ceiling on hangul density

Status: **permanent**. Records why the Latin base cannot be swapped for a
0.600-advance face, and why the ratio complaint is not Iosevka's fault.

## Context

The recurring proposal is to replace the Latin base — usually with JetBrains
Mono, Commit Mono or Geist Mono, whose letterforms are less condensed than
Iosevka's and so look better next to Pretendard. The proposal keeps coming back
because the objection to Iosevka is real: its letterforms are 24% more condensed
than Pretendard's Latin.

It cannot work, and the reason is arithmetic rather than taste.

## The constraint

Holding a hangul-to-Latin-cap ratio `R`, the achievable hangul fill is

```
fill = R × (cap / 2a) × (ink_w / ink_h)
```

`cap / 2a` — the Latin's cap height against the CJK cell — is a **ceiling**, and
no choice of CJK source moves it. Widening the Latin advance `a` lowers it.

At `R = 1.23`:

| base | adv | cap | cap/2a | fill | hangul T | vs Sarasa |
|---|---|---|---|---|---|---|
| **Iosevka Term** | 0.500 | 0.735 | **0.735** | 0.806 | **0.241** | 9% tighter |
| CommitMono | 0.600 | 0.700 | 0.583 | 0.639 | 0.564 | **114% looser** |
| GeistMono | 0.600 | 0.710 | 0.592 | 0.649 | 0.542 | 105% looser |
| JetBrainsMono | 0.600 | 0.730 | 0.608 | 0.667 | 0.500 | 89% looser |

A 0.600 Latin held at the correct proportion produces hangul **more than twice
as loose as Sarasa** — the exact defect this font exists to remove. It also costs
20% of the columns at equal font size.

Iosevka is not the cause of the ratio problem. It has the **highest** `cap/2a` of
everything surveyed.

## Decision

The Latin base is a 0.500-advance face. `cap` is the lever that raises the
ceiling, and raising it parametrically (735 → 808) redraws the letters at
unchanged stroke weight instead of scaling them, so the box-drawing frame stays
matched. Widening `a` is structurally excluded.

## Also decisive: Braille

Of twelve candidates surveyed, U+2800–28FF is complete only in Iosevka, ZedMono
(an Iosevka derivative), CascadiaMono and CommitMono. JetBrains Mono, Geist, IBM
Plex, Monaspace, Hack and IntelOne all measure **0/256**. Agent TUIs emit a
Braille spinner, so this is a hard requirement, not a nicety.

## Worth recording

At `R = 1.23` on **any** base, Pretendard buys almost nothing over Sarasa on
spacing — Sarasa already sits exactly on that curve
(1.218 × 0.735 × 0.8836 = 0.791 ✓). The spacing win only exists **above** the
reference ratio. That is the real tension in this project, and it is not about
the Latin base at all.

## Downstream

Any future base swap is checked against `cap / 2a` **first**. If it is below
0.735 the hangul spacing regresses no matter what else is done, and the
comparison stops there.
