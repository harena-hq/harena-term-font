# Harena Term

A terminal monospace font where Korean, Japanese and English are all first-class,
on a strict 1:2 cell grid.

**English** | [日本語](README.ja.md) | [한국어](README.ko.md)

![The same Korean text in Sarasa Term K and in Harena Term K, at the same cell width](docs/specimen.png)

Most CJK terminal fonts set every full-width glyph to one cell and let the
letterspacing fall where it falls. For hangul that is far looser than the source
designer drew it — Sarasa Term K sits at a gap-to-ink ratio of `T = 0.264` where
proportional Pretendard sits at `0.1287`, more than twice as loose.

Harena Term scales each script so that its **native advance lands exactly on the
cell**, which reproduces that script's own letterspacing as an identity rather
than an approximation. Measured on the shipped face: hangul `T = 0.1260`, **52%
tighter than Sarasa**, inside a grid that is still exactly 1:2.

It is built by merging [Iosevka Term Nerd Font Mono](https://github.com/be5invis/Iosevka)
(Latin, symbols, box drawing, Braille, Powerline, Nerd Font icons) with
[Pretendard JP](https://github.com/orioncactus/pretendard) (hangul, han, kana),
with [M PLUS 1p](https://github.com/coz-m/MPLUS_FONTS) and
[Noto Sans KR](https://github.com/notofonts/noto-cjk) filling the gaps neither
covers at full width.

## Download

Grab the latest release from [**Releases**](../../releases/latest).

> **1.0.0.** The three conditions this project set for a stable number are met:
> a release workflow proven by a real release, the weighting defect 0.9.0
> shipped with [fixed](docs/adr/0014-the-compensation-target-erases-the-source-relative-weighting.md),
> and Windows [run and measured](docs/adr/0017-windows-verified.md) rather than
> assumed. What the number does not mean is that nothing is left — the
> [known limitations](CHANGELOG.md#known) are listed, and each is a decision
> with a record behind it. See [the road to 1.0](CHANGELOG.md#the-road-to-10).

| | |
|---|---|
| `HarenaTerm-ttf.zip` | desktop — terminals, editors, word processors |
| `HarenaTerm-woff2.zip` | web — browser-based terminals via `@font-face` |

Each holds four faces: `Harena Term K` and `Harena Term J`, Regular and Bold.

## Install

Unzip and use your system's font installer — Font Book on macOS, select the
files and right-click → Install on Windows. Or put them where the system looks:

```sh
# macOS
cp *.ttf ~/Library/Fonts/

# Linux
cp *.ttf ~/.local/share/fonts/ && fc-cache -f
```

This project ships no install script. The OS already does this well, and for
the rest a package manager beats a script we would have to maintain and could
not test on every platform — see [ADR 0016](docs/adr/0016-no-install-scripts.md).

## The two cuts: K and J

Korean and Japanese draw many of the same han differently. The clearest case is
the walking radical at the lower left of 運 進 週 選 過 達 通 連 遠 — Korean keeps
its traditional two dots, the Japanese shinjitai uses one.

Unicode encodes these as the *same* codepoint, so the difference is a glyph
choice, not an encoding one. It normally lives in an OpenType `locl` feature that
fires on a language tag. **A terminal cannot reach that**: texture-atlas renderers
build their font string from plain CSS with no `font-feature-settings` and no
language tag, and almost no native terminal tags runs by language either.

So the regional forms are baked into `cmap` and two faces ship.

| | |
|---|---|
| **Harena Term K** | Korean forms. Pick this for Korean text, or if you are unsure. |
| **Harena Term J** | Japanese forms. Pick this if you read Japanese. |

They differ in **611 codepoints of 37652**, all inside han, with **zero advance
differences** — so the two can be mixed on one screen without shearing a row.
Hangul, kana, Latin, symbols, box drawing and Braille are byte-identical between
them.

## Coverage

**37652 codepoints** across **86 Unicode blocks**, 38478 glyphs per face. Full
per-block attribution in [`docs/COVERAGE.md`](docs/COVERAGE.md).

| | |
|---|---|
| hangul syllables | **11172** — complete, plus 67 conjoining jamo |
| han | **7138** — JIS X 0208, cp932 and KS X 1001 complete |
| kana | hiragana 90, katakana 94, halfwidth katakana 63 |
| Braille | **256/256** — agent TUIs draw spinners with these |
| box drawing / blocks / geometric / arrows | 128 · 32 · 96 · 112 |
| Nerd Font icons | Powerline, Font Awesome, Devicons, Octicons, Material and more |
| codepage coverage | cp932 **100%**, cp949 **99.98%** |

The font also **composes NFD hangul itself**, through 11172 `ccmp` ligatures.
macOS stores filenames in NFD, so every Korean filename in an `ls` listing
arrives as conjoining jamo; a font that leaves this to the shaper renders them
stacked on top of one another under CoreText.

### One compatibility note worth reading

Advance widths follow the Unicode 11 East Asian Width table as implemented by
xterm.js's `unicode11` provider. That resolves **Ambiguous-width characters to
one cell** — `♥ ○ → ± ′` and 1197 others.

A terminal configured `ambiguous = wide` reserves **two** cells for those, and
this font draws one, which will shear those rows. Sarasa makes the opposite
choice. A font has one advance per glyph and cannot serve both readings; if your
terminal is set to `ambiguous = wide`, this font is not the right one for it.

## Building it yourself

The build is **byte-reproducible from pinned sources**, and the eight artefacts
it produces are recorded in `SHA256SUMS`.

```sh
pip install -r requirements.txt
pnpm install
scripts/fetch_sources.sh      # pinned URLs, SHA-256 verified; builds the Latin
python3 scripts/build.py      # merge Latin and CJK onto the grid
python3 scripts/postbuild.py  # hint, re-stamp, WOFF2, SHA256SUMS
python3 scripts/verify.py     # the gate
cd dist && sha256sum -c ../SHA256SUMS
```

`verify.py` **asserts rather than reports** — its exit code is the gate, and it
runs **158 checks** across all four faces: every advance re-derived from the
binary and checked against the width provider across all 21349 covered
codepoints, every full-width glyph scanned for cell overflow, all 11172 NFD
syllables walked through the `ccmp` ligature tree, letterspacing and the
hangul-to-han stroke ratio measured against Pretendard's own, `OS/2` script
declarations, and the reproducibility stamp on the shipped bytes.

Set `SOURCE_DATE_EPOCH` to override the build stamp. CI runs the whole sequence
and checks the hashes on every push.

Why the project makes each choice it does — with the measurement that settled it
and the trigger that would reopen it — is in [`PLAN.md`](PLAN.md) and
[`docs/adr/`](docs/adr/).

## Credits

This font is a merge. Everything it draws was drawn by someone else; what is
original here is the fitting, the grid and the gate.
[`docs/LINEAGE.md`](docs/LINEAGE.md) traces each source through every hand it
passed through.

| | drawn by | what it draws here |
|---|---|---|
| [Iosevka](https://github.com/be5invis/Iosevka) | Belleve Invis | Latin, symbols, box drawing, Braille |
| [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) | Ryan L McIntyre and contributors | the icon sets |
| [Pretendard JP](https://github.com/orioncactus/pretendard) | Kil Hyung-jin | hangul, han, kana |
| [M PLUS 1p](https://github.com/coz-m/MPLUS_FONTS) | Coji Morishita | brackets, halfwidth katakana, 〇 〒 〓 |
| [Noto Sans KR](https://github.com/notofonts/noto-cjk) | Adobe / Google | enclosed and squared forms, archaic jamo |

Pretendard's own name table credits Inter for its Latin, Noto Sans CJK
(Source Han Sans) for hangul and han, and M PLUS 1p for kana — so several of
these appear twice in the lineage, once directly and once by way of Pretendard.

## Licence

Split by what the thing is, following JetBrains Mono and Nerd Fonts.

| | covers |
|---|---|
| [`OFL.txt`](OFL.txt) — SIL Open Font License 1.1 | **the fonts**, wherever they are: the release artefacts and anything built from this tree |
| [`LICENSE`](LICENSE) — Apache License 2.0 | **the build system**: the scripts, the build plans, the documentation |
| [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) + [`licenses/`](licenses/) | the Nerd Fonts icon sets, which are neither — several are MIT or CC-BY-4.0, and two require attribution |

**`Harena Term` is a Reserved Font Name** under the OFL. You may modify and
redistribute the fonts freely; a modified version must carry a different name.

Copyright © 2026 Jeeyong Um. The upstream copyrights are retained in `OFL.txt` as
OFL §2 requires.
