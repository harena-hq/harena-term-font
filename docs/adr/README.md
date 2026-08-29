# Decision records

Each of these records a decision that someone — including a future us — could
otherwise arrive at wrongly a second time. They carry the measurement that
settled it and the trigger that would reopen it.

[`PLAN.md`](../../PLAN.md) holds the decisions in one place and is the better
starting point. These exist for the reasoning that does not fit there: the
alternatives that lost and why, and the mistakes that produced a rule.

## Grid and geometry

| ADR | decision |
|---|---|
| [0002](0002-advance-normalisation-is-an-identity.md) | Per-script advance normalisation reproduces the source's letterspacing **exactly**, because `T` is scale-invariant and Pretendard's advances are uniform within a script. Two scale groups follow from that. |
| [0003](0003-stroke-weight-compensated-through-wght.md) | Two scales mean two stroke weights on one line. Compensated through the source's own `wght` axis, not by distorting outlines. The mechanism stands; the target it aimed at was replaced by 0014. |
| [0004](0004-latin-advance-sets-the-hangul-ceiling.md) | `fill = R × (cap/2a) × (ink_w/ink_h)`. The Latin advance is a **ceiling** on hangul density, so a 0.600 base is structurally excluded no matter how well its letterforms match. |
| [0001](0001-latin-spacing-reopened.md) | The Latin's letterspacing is set through `metricOverride.sb`, which redraws at unchanged stroke weight. Scaling it instead thickens the strokes past a box-drawing frame that cannot follow. |

## Sources

| ADR | decision |
|---|---|
| [0005](0005-cjk-source-stays-pretendard-jp.md) | Pretendard JP stays. Han coverage of 7138 is complete for practical Japanese and Korean. **M PLUS 1 Code is not a better fit**: a monospace source is no advantage when the build normalises advances, the kana have converged anyway, and it has 6 of the 18 brackets. |
| [0006](0006-two-regional-cuts-with-ss05-baked-in.md) | Korean and Japanese cuts, with `ss05` baked into `cmap` because a terminal cannot reach an OpenType feature at runtime. 611 codepoints differ, all inside han, zero advance differences. |

## Correctness under real renderers

| ADR | decision |
|---|---|
| [0007](0007-the-font-composes-nfd-hangul-itself.md) | The font composes NFD hangul itself, through 11172 `ccmp` ligatures. **HarfBuzz cannot test this** — its Hangul shaper normalises before any lookup runs — and CoreText, which has no such shaper, draws the jamo stacked. Every Korean filename on macOS. |
| [0008](0008-advances-are-driven-by-the-provider-table.md) | Advances are *driven* by the width provider's own table across all 21349 covered codepoints, not checked against a hand-written list. Zero mismatches becomes structural. Found 23 inherited defects a list would have missed. |
| [0009](0009-the-name-table-is-rebuilt-never-patched.md) | The name table is cleared and reconstructed. Patched, it keeps the base's `nameID 21`, and both platforms group by WWS family when present — so all four faces read as one family to the OS. |
| [0013](0013-the-width-table-must-cover-what-the-build-declares.md) | The build silently skips any codepoint the width table lacks, and two declared ranges were never extracted — dropping `￥` among others. The gate now asserts the two lists agree. Recovered 81 glyphs including all 63 halfwidth katakana. |
| [0012](0012-os2-must-declare-the-scripts-carried.md) | `OS/2` is recomputed from the merged `cmap`. Inherited from Iosevka it declares **no CJK at all**, so Word sets hangul in a fallback while leaving Latin in this face. Chinese is pruned back out — 46.9% of cp950 against 98.9% of cp949. |

## Rendering

| ADR | decision |
|---|---|
| [0010](0010-ttfautohint-hints-y-only.md) | ttfautohint hints in **y only** — measured, horizontal strokes gain +21 to +36 and vertical strokes gain nothing. No `-a` value touches x, so that search space is closed. VTT is the tool that could. **The reopen trigger fired — see [0019](0019-the-hinting-failure-was-position-not-width.md). The unqualified "do not sweep `-a`" was too broad (slot 3 does change the render); `-a` still keeps its value, for a different reason, and "ship the defaults" is superseded.** |

## Distribution

| ADR | decision |
|---|---|
| [0016](0016-no-install-scripts.md) | **No install scripts.** One of the four reference repositories ships them; the two with the widest reach use package managers instead. The OS already installs a font, a package manager also handles upgrade and uninstall, and the download path coupled the project to its own URL shape — which failed silently, returning 404, for as long as the repository was private. The Windows script was shipped having never been executed. |
| [0018](0018-npm-wraps-an-immutable-font-release.md) | The npm package is a **versioned wrapper around an immutable font release**. Its package version may advance for CSS or metadata while `harena.fontVersion` and `SHA256SUMS` pin the unchanged font bytes. `v*` tags release fonts plus npm; `npm-v*` tags release only the wrapper. Publishing happens in a minimal OIDC job that never runs the upstream build. |
| [0019](0019-the-hinting-failure-was-position-not-width.md) | The hinting failure was stroke **position**, not stroke width: a bar's edges rounded together and its height became zero, so `ㅌ` lost a bar and `텰` read as `뎔`. `-x 20 -X 15` move blue-zone rounding and fix it; `-a` stays where 0010 put it. The gate rasterises all 11172 syllables at 13-18 ppem and asserts no bar is erased. |
| [0017](0017-windows-verified.md) | **Windows verified**, closing the last 1.0.0 condition. The 48-column frame's right edge lands on the same x for all eight rows — zero shear under DirectWrite — ambiguous width agrees with the terminal's default, NFD composes, box joins close, and Bold shares Regular's advances. A second round on the physical machine closed it at an em of **14 px**, in Windows Terminal and conhost both, after the first rendered at 200% because a Remote Desktop scale setting is not the scale it renders at. One platform difference found: conhost gives every conjoining jamo a cell, so NFD Korean runs wider there than the 2/0/0 the font declares and Windows Terminal honours. Word was not run. |
| [0015](0015-ttf-and-woff2-only.md) | TTF and WOFF2 only. OTF is declined structurally — CFF discards the ttfautohint work on all 36859 hinted glyphs, curve conversion moves points the cell measurements have no room for, and the 166 checks read `glyf`. TTC is declined on arithmetic: a collection shares byte-identical **tables**, not glyphs, and 611 differing glyphs keep all 17.66 MB of `glyf` duplicated — **0.6% saved**. |

## Identity

| ADR | decision |
|---|---|
| [0011](0011-naming-harena-term.md) | `Harena Term K` / `Harena Term J`, vendor `HRNA`. What a name here must clear (`Pretendard` and `Source` are reserved), and the open risk that a commercial display face named Harena already exists. |

## Open

| ADR | decision |
|---|---|
| [0014](0014-the-compensation-target-erases-the-source-relative-weighting.md) | Compensating every script to the **Latin stem** divided out the relative weighting the source's designers built between scripts, and the gate asserted the flattened value rather than missing it. 0003's own `1.0533 → 1.1426` turns out to be `× 1920/1770` exactly — one drawing in two units, not a distortion to remove. Fixed by instancing the whole CJK at one source weight; ratio restored on both axes, and the horizontal one was never solved for. |

## Recurring shapes

Four of the defects recorded here are one defect wearing different clothes.
They are collected because the pattern is easier to check for than the instances
are to remember.

- **A range absent from the authority is a blind spot, not a pass.** The width
  table drives the build, so a range it omits is a range the build skips in
  silence and the gate cannot check. Three times: the jamo range (0007, 0008),
  then U+FE30–FE4F and U+FFE0–FFE6, which dropped `￥` without a word (0013).
  Related: **a test that runs through a layer which fixes the defect is not a
  test** — `hb-shape` proves nothing about NFD composition, because HarfBuzz
  composes before the font is asked.
- **Setting the fields you know about leaves the fields you do not.** The `name`
  table (0009) and `OS/2`'s script declarations (0012). A merged font inherits
  its base's claims *about itself*, and those claims describe the base. After
  merging, ask what each inherited table **asserts**, not just what it stores.
- **Sampling hides the extreme.** A collision check that sampled every 17th
  syllable reported 0.986 where the true maximum was 0.997, and scanned two of
  the five full-width ranges (0008). The same shape produced a wrong number a
  third time in 0014: single-stroke glyphs put the hangul/han error at 5%, where
  225 glyphs put it at 13.5%.
- **A gate can assert the wrong thing.** The blind-spot cases above are about
  ranges the authority never listed. 0014 is the opposite: listed, measured, and
  asserted — at a value that erases a deliberate design decision. Passing at
  `1.000×` reads as precision; it is the defect written down as a requirement.
- **A check whose title claims more than its body tests.** Worse than an
  absent check, because it reports success. `docs/sample.txt` block 8 was
  titled "Nerd Font icons" and contained none of the font's 3518 private-use
  glyphs (0017); the letterspacing gate asserted a one-sided bound under a
  label announcing a two-sided band (0014).
