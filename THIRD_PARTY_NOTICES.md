# Third-party notices — Harena Term

Harena Term is a derivative work. It is **not** distributed by, endorsed by or
verified against any upstream project, and no upstream checksum can validate
the shipped binaries — they are new files.

Every input below is pinned, and the pins are executable rather than
documentary: `scripts/fetch_sources.sh` downloads each one and refuses to
continue unless the bytes match. Downloads are pinned by SHA-256 and the one
input built from source is pinned by commit. To reproduce:

```sh
scripts/fetch_sources.sh && python3 scripts/build.py && python3 scripts/postbuild.py
```

No upstream Reserved Font Name is used. Pretendard JP reserves "Pretendard JP"
and Noto Sans KR carries Adobe's "Source"; Iosevka and M PLUS 1p reserve none.
Only glyphs are taken, never a name. The output family is **Harena Term**,
which is itself a Reserved Font Name — see `OFL.txt`.

## Sources


### Iosevka Term Nerd Font Mono

- Upstream: https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/IosevkaTerm.tar.xz
- SHA-256 of `sources/cand/IosevkaTerm.tar.xz`: `cad9da572d25e3413f7a15a319d2f3c9e7e915ee016baa99e0d88fc08cf5b781`
- License: OFL-1.1 (text: `licenses/Iosevka-OFL-1.1.md`)
- Used for: Latin, digits, punctuation, box drawing, block elements, geometric shapes, arrows, Braille and Powerline. Taken untouched apart from subsetting and the advance corrections described below.

### M PLUS 1p

- Upstream: https://raw.githubusercontent.com/google/fonts/d714b17ce2379f06daf6295617f961df605dccb5/ofl/mplus1p/MPLUS1p-Regular.ttf
- SHA-256 of `sources/mplus1p/MPLUS1p-Regular.ttf`: `2f294ad496432b1608f070d310e3aa2adcf1de4af429f4901df97ec4bd361ed1`
- Also `MPLUS1p-Medium.ttf` — drives the 700 weight, as Regular drives the 400
  - Upstream: https://raw.githubusercontent.com/google/fonts/d714b17ce2379f06daf6295617f961df605dccb5/ofl/mplus1p/MPLUS1p-Medium.ttf
  - SHA-256: `28b2f52a40ae988064810b71d67e127df75a16e08d7df4e192d1006e4075394f`
- License: OFL-1.1 (text: `licenses/MPLUS1p-OFL-1.1.txt`)
- Used for: The eighteen CJK bracket forms, Regular for the 400 weight and Medium for the 700. Pretendard draws these for proportional setting and ships no `palt` to tighten the box, so in a grid they sit at 0.221 of the cell against Sarasa's 0.315; M PLUS is fuller than either. Taken from the same source Pretendard's kana already come from, at 1.0211 of its em. That is intended as Pretendard's own resize composed with this build's 1.0667; measured, the relationship is not a uniform scale, so see docs/LINEAGE.md for what it actually is.

### Noto Sans KR (Source Han Sans)

- Upstream: https://raw.githubusercontent.com/google/fonts/b38c5c93af322c45f633e17ac440ec1e6c94d489/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf
- SHA-256 of `sources/notosanskr/NotoSansKR[wght].ttf`: `194018e6b2b293a7964f037b25c0249ce1418bc9ab3c971060a03aa57861e252`
- License: OFL-1.1 (text: `licenses/NotoSansKR-OFL-1.1.txt`)
- Used for: The enclosed and squared blocks U+3200–33FF and the archaic compatibility jamo U+3165–318E — 544 glyphs. Pretendard has 81 of these but draws every one proportionally, at 2280–3638 units against the cell's 1920, because it is an Inter-based proportional face; a CJK-native font draws them full-width, and all of these sit at exactly one em here, so they import with no compression. This is the font Pretendard's own hangul and han derive from — measured against the shipped face, it matches our hangul as closely as Pretendard does (IoU 0.915 against 0.916). Its licence carries Adobe's Reserved Font Name 'Source'; only glyphs are used, never the name. Two transforms solved against the shipped face: wght 440/640, scale 0.9993/0.9992, +11 units for the enclosed forms against our han, and wght 480/700, scale 1.0988/1.0779, −1 unit for the jamo against our hangul.

### Pretendard JP 1.3.9

- Upstream: https://github.com/orioncactus/pretendard/releases/download/v1.3.9/PretendardJP-1.3.9.zip
- SHA-256 of `sources/PretendardJP-1.3.9.zip`: `8dab678c371a1530106ca643b76b2b80d47653d5ba670b01265b48e4c6615d63`
- License: OFL-1.1 (text: `licenses/PretendardJP-OFL-1.1.txt`)
- Used for: Hangul, kana, han, CJK punctuation and fullwidth forms, except the eighteen brackets listed above. Instanced from the variable font and scaled; see PLAN.md D2 and D3. Pretendard's own name table credits Inter for the Latin base glyphs, Noto Sans CJK (Source Han Sans) for hangul and han, and M PLUS 1p for kana.

### Iosevka (source)

- Upstream: https://github.com/be5invis/Iosevka.git
- Tag: `v34.8.0`, asserted at commit `ca3ad8e280e2f0b614a5a7721b047daaf023713d`
- License: OFL-1.1 (text: `licenses/Iosevka-OFL-1.1.md`)
- Used for: The shipping Latin, built from this source with `latin/private-build-plans.toml` — shape 500, sb 45, cap 808, xHeight 572, leading 1350. This is a build input, not a download: the Nerd Font archive above supplies the symbols and the advance reference, but every Latin outline in the shipped fonts comes from here. Dependencies install with `npm ci` against upstream's `package-lock.json`.

### Nerd Fonts symbol sets

The Iosevka archive above is the Nerd Fonts *patched* build, and its symbol
glyphs are an **aggregation of separately licensed works** — not part of
Iosevka's OFL grant. The `LICENSE.md` inside that archive carries Iosevka's OFL
and nothing else, so it does not cover any of the sets below.

Every set listed here is present in the shipped binaries. The table is
generated by measuring the built font against the source's glyph names, so it
cannot drift from what actually shipped.

**These obligations follow the binaries.** Anyone who redistributes these fonts
— including an application that bundles or serves them — carries the same
notice requirements, and reproducing this file alongside the font files
discharges them.


10374 symbol glyphs across 14 sets:

| Set | Glyphs | Range | License | Copyright | License text |
|---|---:|---|---|---|---|
| [Material Design Icons](https://github.com/Templarian/MaterialDesign) | 6880 | `U+F0001–U+F1AF0` | Apache-2.0 | Copyright (c) Pictogrammers | [`MaterialDesignIcons-PictogrammersFreeLicense.txt`](licenses/MaterialDesignIcons-PictogrammersFreeLicense.txt) |
| [Font Awesome Free](https://github.com/FortAwesome/Font-Awesome) | 1475 | `U+ED00–U+F2FF` | CC BY 4.0 | Copyright (c) 2024 Fonticons, Inc. | [`FontAwesome-Free.txt`](licenses/FontAwesome-Free.txt) |
| [Devicons](https://github.com/vorillaz/devicons) | 496 | `U+E700–U+E8EF` | MIT | upstream ships the MIT text with no copyright line; attributed to the Devicons project | [`Devicons-MIT.txt`](licenses/Devicons-MIT.txt) |
| [Codicons](https://github.com/microsoft/vscode-codicons) | 438 | `U+EA60–U+EC1E` | CC BY 4.0 | Copyright (c) Microsoft Corporation | [`Codicons-CC-BY-4.0.txt`](licenses/Codicons-CC-BY-4.0.txt) |
| [Octicons](https://github.com/primer/octicons) | 310 | `U+2665–U+F533` | MIT | Copyright (c) GitHub Inc. | [`Octicons-MIT.txt`](licenses/Octicons-MIT.txt) |
| [Weather Icons](https://github.com/erikflowers/weather-icons) | 228 | `U+E300–U+E3E3` | SIL OFL 1.1 | Copyright (c) Erik Flowers | [`WeatherIcons-OFL-1.1.txt`](licenses/WeatherIcons-OFL-1.1.txt) |
| [Font Awesome Extension](https://github.com/AndreLZGava/font-awesome-extension) | 170 | `U+E200–U+E2A9` | MIT | Copyright (c) 2017 André Luiz Gava | [`FontAwesomeExtension-MIT.txt`](licenses/FontAwesomeExtension-MIT.txt) |
| [Seti-UI](https://github.com/jesseweed/seti-ui) | 160 | `U+E600–U+E6AA` | MIT | Copyright (c) 2014 Jesse Weed | [`SetiUI-MIT.txt`](licenses/SetiUI-MIT.txt) |
| [Font Logos (formerly Font Linux)](https://github.com/lukas-w/font-logos) | 130 | `U+F300–U+F381` | The Unlicense | released into the public domain | [`FontLogos-Unlicense.txt`](licenses/FontLogos-Unlicense.txt) |
| [Powerline Extra Symbols](https://github.com/ryanoasis/powerline-extra-symbols) | 33 | `U+E0A3–U+E0D7` | MIT | Copyright (c) 2016 Ryan L McIntyre | [`PowerlineExtraSymbols-MIT.txt`](licenses/PowerlineExtraSymbols-MIT.txt) |
| [Nerd Fonts originals (Seti-UI derived)](https://github.com/ryanoasis/nerd-fonts) | 31 | `U+E5FA–U+E6B8` | MIT | Copyright (c) 2014 Jesse Weed | [`SetiUI-MIT.txt`](licenses/SetiUI-MIT.txt) |
| [Pomicons](https://github.com/gabrielelana/pomicons) | 11 | `U+E000–U+E00A` | SIL OFL 1.1 | Copyright (c) 2021, Gabriele Lana | [`Pomicons-OFL-1.1.txt`](licenses/Pomicons-OFL-1.1.txt) |
| [Powerline Symbols](https://github.com/powerline/powerline) | 7 | `U+E0A0–U+E0B3` | MIT | Copyright 2013 Kim Silkebækken and other contributors | [`PowerlineSymbols-MIT.txt`](licenses/PowerlineSymbols-MIT.txt) |
| [IEC Power Symbols](https://unicodepowersymbol.com/) | 5 | `U+23FB–U+2B58` | MIT | not stated in a machine-readable licence file | — *(see note)* |

Notes on individual sets:

- **Codicons** — the licence text carries no copyright line; holder taken from the repository owner. **Attribution is a condition of this licence.**
- **Font Awesome Free** — Font Awesome Free is tri-licensed; only the icons are used here and those are CC BY 4.0. **Attribution is a condition.**
- **Font Logos (formerly Font Linux)** — the Nerd Fonts audit records this as 'Unlicensed', which is ambiguous: the upstream file is the Unlicense, a public domain dedication. **The logos themselves remain trademarks of their respective owners; the dedication covers the artwork, not the marks.**
- **IEC Power Symbols** — the licence is recorded by the Nerd Fonts audit; the upstream publishes no licence file, so none is reproduced here and the audit is the citation
- **Material Design Icons** — shipped under the 'Pictogrammers Free License', which redistributes the icons under Apache 2.0. **Apache-2.0 requires that a copy of the licence travel with the work, and that any NOTICE file be reproduced.**
- **Nerd Fonts originals (Seti-UI derived)** — the audit lists these as 'Original Source (Seti-UI but modified)'
- **Seti-UI** — as modified by the Nerd Fonts project
- **Weather Icons** — the licence is stated in the project README; the repository ships no licence file and is unmaintained

Two of these sets sit partly **outside the private use area**, at ordinary
Unicode codepoints that appear in normal text — IEC Power Symbols at
U+23FB–U+23FE and U+2B58, and two Octicons at U+2665 `♥` and U+26A1 `⚡`. Any
future subsetting has to work from a codepoint list rather than a set name, or
it will silently remove real characters.

## License texts included

Several of the licences above require their text to travel with the work rather
than be linked — Apache-2.0 §4(a) explicitly, and the OFL and CC BY 4.0 in
substance. The full texts are in `licenses/`:


- [`Apache-2.0.txt`](licenses/Apache-2.0.txt) — 11.1 KB
- [`Codicons-CC-BY-4.0.txt`](licenses/Codicons-CC-BY-4.0.txt) — 18.8 KB
- [`Devicons-MIT.txt`](licenses/Devicons-MIT.txt) — 1.0 KB
- [`FontAwesome-Free.txt`](licenses/FontAwesome-Free.txt) — 7.3 KB
- [`FontAwesomeExtension-MIT.txt`](licenses/FontAwesomeExtension-MIT.txt) — 1.0 KB
- [`FontLogos-Unlicense.txt`](licenses/FontLogos-Unlicense.txt) — 1.2 KB
- [`Iosevka-OFL-1.1.md`](licenses/Iosevka-OFL-1.1.md) — 4.4 KB
- [`MPLUS1p-OFL-1.1.txt`](licenses/MPLUS1p-OFL-1.1.txt) — 4.3 KB
- [`MaterialDesignIcons-PictogrammersFreeLicense.txt`](licenses/MaterialDesignIcons-PictogrammersFreeLicense.txt) — 1.0 KB
- [`NotoSansKR-OFL-1.1.txt`](licenses/NotoSansKR-OFL-1.1.txt) — 4.3 KB
- [`Octicons-MIT.txt`](licenses/Octicons-MIT.txt) — 1.0 KB
- [`Pomicons-OFL-1.1.txt`](licenses/Pomicons-OFL-1.1.txt) — 4.3 KB
- [`PowerlineExtraSymbols-MIT.txt`](licenses/PowerlineExtraSymbols-MIT.txt) — 1.0 KB
- [`PowerlineSymbols-MIT.txt`](licenses/PowerlineSymbols-MIT.txt) — 1.1 KB
- [`PretendardJP-OFL-1.1.txt`](licenses/PretendardJP-OFL-1.1.txt) — 4.3 KB
- [`SetiUI-MIT.txt`](licenses/SetiUI-MIT.txt) — 1.0 KB
- [`WeatherIcons-OFL-1.1.txt`](licenses/WeatherIcons-OFL-1.1.txt) — 4.5 KB

`Apache-2.0.txt` is the full Apache License 2.0, required by Material Design
Icons: the file Pictogrammers ships is a short grant that *refers* to Apache
2.0 without reproducing it, so both are included.

## Redistribution

The obligations above attach to the act of distribution, not to this
repository. Anyone shipping these fonts onward — a desktop application that
bundles them, a web application that serves the WOFF2 — redistributes every
icon set inside them and carries the same requirements.

Reproducing this file together with the `licenses/` directory alongside the
font files discharges them. Neither needs to be rewritten; the point is that
they reach whoever receives the binaries.

## Modifications made

1. The Latin base is subsetted to its cmap-reachable glyphs. Iosevka ships
   52823 glyphs of which 34996 are `cv01`–`cv99` / `ss01`–`ss20` alternates
   reachable only through OpenType features; xterm.js builds `ctx.font` from a
   plain CSS shorthand with no `font-feature-settings`, so those are
   unreachable at runtime and would also overflow the uint16 glyph count once
   the CJK is merged.
2. CJK glyphs are imported from Pretendard JP, scaled so each script's advance
   lands exactly on the two-cell box, and instanced at a compensating `wght`
   so the post-scale stroke matches the Latin stem. See PLAN.md D2/D3.
3. 23 advances inherited from Iosevka are corrected to agree with the
   unicode11 provider: eight zero-width formatting characters (U+200B–200D,
   U+2060–2064) drawn a full cell wide, and fifteen Emoji_Presentation symbols
   (U+231A, U+231B, U+2329, U+232A, U+23E9–23EC, U+23F0, U+23F3, U+25FD,
   U+25FE, U+26A1, U+26AA, U+26AB) drawn one cell where the provider reserves
   two. Both shear a terminal row. Not introduced by this build.
4. For the `K` faces, Pretendard's `ss05` Korean regional forms are baked into
   `cmap`, because the renderer cannot reach an OpenType feature at runtime.
   537 hanja differ between the K and J faces.

## Build

```
python3 scripts/build.py --region both --weight 400,700
python3 scripts/verify.py          # conformance gate; exit 0 == sealable
```

## Outputs


- `HarenaTermJ-Bold.ttf` — 18.86 MB — `65818e911e9e7d5532ecb764f997510a96cf7d73a2c128ece8e55bf5a4948080`
- `HarenaTermJ-Bold.woff2` — 4.96 MB — `107b365f219f857e8063e18522d92e2076207f2a0ea0b9274ec91434f157ef58`
- `HarenaTermJ-Regular.ttf` — 18.16 MB — `8bd0d42dc6dadc2a895e6623dd07f92d53c0b7f5a0ef474aafa127bada7322d7`
- `HarenaTermJ-Regular.woff2` — 4.84 MB — `d61b9d0cf250fbce455aa65a236295a1cf4a484499d0a741a9d6f3c4922a5b9f`
- `HarenaTermK-Bold.ttf` — 18.88 MB — `36a01d44d6f77ddf4c709c3b4951eeb016dead301cf9d16087272c293537d3bf`
- `HarenaTermK-Bold.woff2` — 4.96 MB — `644e3a1c43edc541643428c54d006ff004658f154aa68e85a50a83304e7347b5`
- `HarenaTermK-Regular.ttf` — 18.17 MB — `853fbe3cc048968193b15565de3441ed5ea9b21136cbdf6a6c47ac3792e5e8b7`
- `HarenaTermK-Regular.woff2` — 4.84 MB — `2e8ea6b2be35a8645bf6a02ae5f93a17d8d1ed97a96471b997ff187f644714d2`

## Base binaries consumed

- `sources/iosevka-src/dist/HarenaLatin/TTF/HarenaLatin-Regular.ttf` — `de003bd5ec2b99c54b45657ad4642dafcbf2d7fa39f3858e7fbb39b3c9158f38`
- `sources/iosevka-src/dist/HarenaLatin/TTF/HarenaLatin-Bold.ttf` — `456f969dc7af4bd91f188df7d7a754e4a8de06e37bc593606ed0f197f077c138`

Built from commit `7c3f713`.
