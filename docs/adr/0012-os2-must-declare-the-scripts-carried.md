# 0012 — `OS/2` must declare the scripts the font actually carries

Status: **permanent**. Records a shipped defect that no glyph-level check could
have caught.

## Context

Reported from MS Word: applying Harena Term K to a mixed string moved the Latin
and the spaces into the face, but the **hangul stayed in D2Coding**. Word behaved
as though the font had no Korean in it.

It effectively said so. `OS/2` carries two claims about what a font can set —
`ulUnicodeRange1..4` and `ulCodePageRange1..2` — and Word, along with the rest of
the Windows font machinery, uses them to decide whether a face may serve East
Asian text. Both are inherited from the base binary, and the base is Iosevka,
which has no CJK.

Measured on the shipped face against Sarasa Term K, which Word handles correctly:

| | Harena Term K | Sarasa Term K |
|---|---|---|
| codepages | 1252 Latin-1 **only** | 1252, **949 Korean Wansung**, 1361 Korean Johab |
| CJK unicode range bits | **none set** | all set |

19000 CJK glyphs, declared as a Latin font.

## Decision

`declare_scripts()` recomputes both from the merged `cmap`, after the CJK, the
jamo and the `ccmp` composition are all in place:

```python
os2.recalcUnicodeRanges(base, pruneOnly=False)
os2.recalcCodePageRanges(base, pruneOnly=False)
```

Eleven unicode range bits turn on — Hangul Jamo, Hangul Compatibility Jamo,
Hangul Syllables, Hiragana, Katakana, CJK Symbols and Punctuation, CJK Unified
Ideographs, CJK Compatibility Ideographs, Halfwidth and Fullwidth Forms,
Non-Plane 0 and Private Use planes 15–16 (the last two are the Nerd Font Material
icons at U+F0001+). Codepages 932, 949 and 1361 turn on.

## Chinese is pruned back out

`recalcCodePageRanges` also set **950 Chinese Traditional**, because Big5 shares
much of its han with JIS and KS. Measured coverage of the shipped font:

| codepage | covered |
|---|---|
| cp949 Korean | **98.9%** |
| cp932 Japanese | **87.5%** |
| cp950 Chinese Traditional | 46.9% |
| cp936 Chinese Simplified | 36.2% |

Chinese is an explicit non-goal ([0005](0005-cjk-source-stays-pretendard-jp.md)),
and a declared codepage is an invitation for the OS to select this face for text
it cannot set — half of which would be tofu. Bits 18 and 20 are cleared after the
recalc.

The cp932 figure measured 87.5% when this was written, and investigating why
found a separate defect — see
[0013](0013-the-width-table-must-cover-what-the-build-declares.md). Excluding
cp932's private-use gaiji rows, which no font carries, coverage is now **99.4%**
and the gap is 39 characters, all in the enclosed and squared blocks. Kanji and
kana are complete.

## The gate

Five assertions per face, because these bits are invisible in every rendered
sample: all nine CJK blocks declared, codepages 949 and 932 declared, codepages
936 and 950 **not** declared.

## The recurring shape

This is [0009](0009-the-name-table-is-rebuilt-never-patched.md) again with a
different table. **A merged font inherits its base's claims about itself, and
those claims describe the base.** `name` said the font was called after an
Iosevka build plan; `OS/2` said it could not set Korean. Both were silent in the
build, invisible in every glyph-level check, and visible only on a user's
machine.

The generalisation for anything added later: after merging, ask what each
inherited table *asserts*, not just what it stores.

## Not the whole story on Word

Word also keeps a separate "Asian text font" slot per run (`w:rFonts/@w:eastAsia`)
which the font dropdown does not always overwrite. With these bits corrected the
face is at least eligible for that slot; a document that already pinned another
font there may still need it set explicitly.
