# 0006 — Two regional cuts, with `ss05` baked into `cmap`

Status: **permanent**.

## Context

Korean and Japanese draw many of the same han differently. The most visible case
is the walking radical at the lower left of 運 進 週 選 過 達 連 遠 道 近 返 退 追
迎 逆 通 造 速 適 — Korean keeps its traditional two dots, the Japanese shinjitai
uses one.

(The radical itself, U+8FB5 and U+8FB6, is deliberately not in this font: it is
outside Pretendard JP's 7138 han, and a document that names it would render tofu
in the very face it describes.)

Pretendard JP carries the Korean forms properly, declaring a `hani` script with a
`KOR ` language system and shipping them in both `locl` (540 substitutions, 534
inside the han range) and `ss05` (608 — the same 534 plus punctuation).

The problem is that **a terminal cannot reach either at runtime.** xterm.js's
`WebglAddon` and `CanvasAddon` are both texture-atlas renderers that build
`ctx.font` from a plain CSS shorthand. There is no `font-feature-settings` and no
language tag in that string, so `locl` never fires and `ss05` is unreachable.
Native terminals are no better placed: almost none expose per-run language
tagging, which is what `locl` needs to fire at all.

## Decision

Ship two faces with the regional forms **baked into `cmap`**:

- **Harena Term K** — `ss05` applied
- **Harena Term J** — default forms

## Measured cost of the split

611 codepoints of the 37652 covered render differently, all inside han:

| | |
|---|---|
| CJK Unified | 537 |
| CJK Compatibility Ideographs (U+F900–FA68) | 74 |
| structurally different (contour or point count) | 556 |
| same skeleton, points moved | 55 |
| **advance differences** | **0** |

Everything else is identical: hangul 11172, kana, Latin, symbols, box drawing,
Braille, Powerline, vertical metrics, upm, weight class. `hmtx` differs only in
left side bearing, which follows the outline. The grid is untouched, so the two
faces can even be mixed on a screen without shearing a row.

## Alternatives rejected

- **One unified face.** It would have to default to the Japanese forms, since
  Japanese terminal text uses han constantly while Korean terminal text is
  effectively pure hangul. But a consumer picks one face and fetches only that
  one, so shipping two costs nothing at runtime — unification would trade a
  visible correctness loss for no gain.
- **Leave `ss05` as a feature and hope.** Measured unreachable; see above.

## The bake is scoped to han, and the gate holds it there

Applying `ss05` wholesale is wrong: only 534 of its 608 substitutions are han.
The rest are punctuation, and their targets are `.hang` proportional glyphs with
advance 698 against the cell's 1920. Bake those and the opening brackets land at
0.113–0.350 of the cell instead of 0.724–0.945 — and an advance validated
*before* substitution rather than after will not notice.

So the bake is restricted to the han range (`0x3400–0x9FFF`, `0xF900–0xFAFF`) and
the advance is validated after substitution. The gate asserts **K and J differ
only inside the han range**, which is what stops the split from silently widening
again.

## Downstream

Weights 400 and 700 only, no italic — the terminal renders SGR default and SGR 1
and has no notion of an intermediate weight.
