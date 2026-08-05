#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
"""Emit THIRD_PARTY_NOTICES.md from the actual bytes on disk.

Every hash is computed here rather than copied, so the notice cannot drift
from what was really built. Run after scripts/build.py.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import subprocess

# Files that are build inputs but not the entry named in SOURCES: listed under
# their parent so the manifest covers every byte the build reads, not just the
# one file per source that happens to be representative.
EXTRA_FILES = {
    "M PLUS 1p": [
        ("sources/mplus1p/MPLUS1p-Medium.ttf",
         "https://raw.githubusercontent.com/google/fonts/"
         "d714b17ce2379f06daf6295617f961df605dccb5/ofl/mplus1p/"
         "MPLUS1p-Medium.ttf",
         "drives the 700 weight, as Regular drives the 400"),
    ],
}

# The parametric Latin is built from source rather than downloaded, so it is
# pinned by commit instead of by hash. A tag can be moved; a commit cannot.
GIT_SOURCES = [
    ("Iosevka (source)", "https://github.com/be5invis/Iosevka.git",
     "v34.8.0", "ca3ad8e280e2f0b614a5a7721b047daaf023713d",
     "OFL-1.1", "licenses/Iosevka-OFL-1.1.md",
     "The shipping Latin, built from this source with "
     "`latin/private-build-plans.toml` — shape 500, sb 45, cap 808, "
     "xHeight 572, leading 1350. This is a build input, not a download: the "
     "Nerd Font archive above supplies the symbols and the advance reference, "
     "but every Latin outline in the shipped fonts comes from here. "
     "Dependencies install with `npm ci` against upstream's "
     "`package-lock.json`."),
]

SOURCES = [
    ("Iosevka Term Nerd Font Mono", "sources/cand/IosevkaTerm.tar.xz",
     "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/IosevkaTerm.tar.xz",
     "OFL-1.1", "licenses/Iosevka-OFL-1.1.md",
     "Latin, digits, punctuation, box drawing, block elements, geometric "
     "shapes, arrows, Braille and Powerline. Taken untouched apart from "
     "subsetting and the advance corrections described below."),
    ("M PLUS 1p", "sources/mplus1p/MPLUS1p-Regular.ttf",
     "https://raw.githubusercontent.com/google/fonts/"
     "d714b17ce2379f06daf6295617f961df605dccb5/ofl/mplus1p/MPLUS1p-Regular.ttf",
     "OFL-1.1", "licenses/MPLUS1p-OFL-1.1.txt",
     "The eighteen CJK bracket forms, Regular for the 400 weight and Medium "
     "for the 700. Pretendard draws these for proportional setting and ships "
     "no `palt` to tighten the box, so in a grid they sit at 0.221 of the cell "
     "against Sarasa's 0.315; M PLUS is fuller than either. Taken from the same "
     "source Pretendard's kana already come from, at 1.0211 of its em. That is "
     "intended as Pretendard's own resize composed with this build's 1.0667; "
     "measured, the relationship is not a uniform scale, so see "
     "docs/LINEAGE.md for what it actually is."),
    ("Noto Sans KR (Source Han Sans)", "sources/notosanskr/NotoSansKR[wght].ttf",
     "https://raw.githubusercontent.com/google/fonts/"
     "b38c5c93af322c45f633e17ac440ec1e6c94d489/ofl/notosanskr/"
     "NotoSansKR%5Bwght%5D.ttf",
     "OFL-1.1", "licenses/NotoSansKR-OFL-1.1.txt",
     "The enclosed and squared blocks U+3200–33FF and the archaic compatibility "
     "jamo U+3165–318E — 544 glyphs. Pretendard has 81 of these but draws every "
     "one proportionally, at 2280–3638 units against the cell's 1920, because it "
     "is an Inter-based proportional face; a CJK-native font draws them "
     "full-width, and all of these sit at exactly one em here, so they import "
     "with no compression. This is the font Pretendard's own hangul and han "
     "derive from — measured against the shipped face, it matches our hangul as "
     "closely as Pretendard does (IoU 0.915 against 0.916). Its licence carries "
     "Adobe's Reserved Font Name 'Source'; only glyphs are used, never the name. "
     "Two transforms solved against the shipped face: wght 440/640, scale "
     "0.9993/0.9992, +11 units for the enclosed forms against our han, and wght "
     "480/700, scale 1.0988/1.0779, −1 unit for the jamo against our hangul."),
    ("Pretendard JP 1.3.9", "sources/PretendardJP-1.3.9.zip",
     "https://github.com/orioncactus/pretendard/releases/download/v1.3.9/PretendardJP-1.3.9.zip",
     "OFL-1.1", "licenses/PretendardJP-OFL-1.1.txt",
     "Hangul, kana, han, CJK punctuation and fullwidth forms, except the "
     "eighteen brackets listed above. Instanced from the variable font and "
     "scaled; see PLAN.md D2 and D3. Pretendard's own name table credits Inter "
     "for the Latin base glyphs, Noto Sans CJK (Source Han Sans) for hangul and "
     "han, and M PLUS 1p for kana."),
]

# The Nerd Fonts symbol glyphs are an aggregation, not one work: each set
# arrives under its own upstream licence, and several are not OFL. Punting to
# "see the LICENSE.md inside the archive" was wrong twice over -- that file
# carries Iosevka's OFL and nothing else, so it does not cover the symbols at
# all, and the obligation follows the act of distribution rather than the
# project, so it lands on anyone who ships these binaries onward.
#
# Licence column taken from the Nerd Fonts license audit
# (https://github.com/ryanoasis/nerd-fonts/blob/master/license-audit.md);
# copyright lines read from each upstream's own licence file. Where an upstream
# ships no copyright line, that is recorded as such rather than guessed.
NERD_SETS = {
    "pom": ("Pomicons", "https://github.com/gabrielelana/pomicons",
            "SIL OFL 1.1", "Copyright (c) 2021, Gabriele Lana", "", "Pomicons-OFL-1.1.txt"),
    "pl": ("Powerline Symbols", "https://github.com/powerline/powerline",
           "MIT", "Copyright 2013 Kim Silkebækken and other contributors", "", "PowerlineSymbols-MIT.txt"),
    "ple": ("Powerline Extra Symbols",
            "https://github.com/ryanoasis/powerline-extra-symbols",
            "MIT", "Copyright (c) 2016 Ryan L McIntyre", "", "PowerlineExtraSymbols-MIT.txt"),
    "seti": ("Seti-UI", "https://github.com/jesseweed/seti-ui",
             "MIT", "Copyright (c) 2014 Jesse Weed",
             "as modified by the Nerd Fonts project", "SetiUI-MIT.txt"),
    "custom": ("Nerd Fonts originals (Seti-UI derived)",
               "https://github.com/ryanoasis/nerd-fonts",
               "MIT", "Copyright (c) 2014 Jesse Weed",
               "the audit lists these as 'Original Source (Seti-UI but "
               "modified)'", "SetiUI-MIT.txt"),
    "indentation": ("Nerd Fonts originals (Seti-UI derived)",
                    "https://github.com/ryanoasis/nerd-fonts",
                    "MIT", "Copyright (c) 2014 Jesse Weed", "", "SetiUI-MIT.txt"),
    "dev": ("Devicons", "https://github.com/vorillaz/devicons",
            "MIT", "upstream ships the MIT text with no copyright line; "
            "attributed to the Devicons project", "", "Devicons-MIT.txt"),
    "cod": ("Codicons", "https://github.com/microsoft/vscode-codicons",
            "CC BY 4.0", "Copyright (c) Microsoft Corporation",
            "the licence text carries no copyright line; holder taken from the "
            "repository owner. **Attribution is a condition of this licence.**", "Codicons-CC-BY-4.0.txt"),
    "md": ("Material Design Icons",
           "https://github.com/Templarian/MaterialDesign",
           "Apache-2.0", "Copyright (c) Pictogrammers",
           "shipped under the 'Pictogrammers Free License', which redistributes "
           "the icons under Apache 2.0. **Apache-2.0 requires that a copy of "
           "the licence travel with the work, and that any NOTICE file be "
           "reproduced.**", "MaterialDesignIcons-PictogrammersFreeLicense.txt"),
    "fa": ("Font Awesome Free", "https://github.com/FortAwesome/Font-Awesome",
           "CC BY 4.0", "Copyright (c) 2024 Fonticons, Inc.",
           "Font Awesome Free is tri-licensed; only the icons are used here and "
           "those are CC BY 4.0. **Attribution is a condition.**", "FontAwesome-Free.txt"),
    "fae": ("Font Awesome Extension",
            "https://github.com/AndreLZGava/font-awesome-extension",
            "MIT", "Copyright (c) 2017 André Luiz Gava", "", "FontAwesomeExtension-MIT.txt"),
    "oct": ("Octicons", "https://github.com/primer/octicons",
            "MIT", "Copyright (c) GitHub Inc.", "", "Octicons-MIT.txt"),
    "weather": ("Weather Icons",
                "https://github.com/erikflowers/weather-icons",
                "SIL OFL 1.1", "Copyright (c) Erik Flowers",
                "the licence is stated in the project README; the repository "
                "ships no licence file and is unmaintained", "WeatherIcons-OFL-1.1.txt"),
    "linux": ("Font Logos (formerly Font Linux)",
              "https://github.com/lukas-w/font-logos",
              "The Unlicense", "released into the public domain",
              "the Nerd Fonts audit records this as 'Unlicensed', which is "
              "ambiguous: the upstream file is the Unlicense, a public domain "
              "dedication. **The logos themselves remain trademarks of their "
              "respective owners; the dedication covers the artwork, not the "
              "marks.**", "FontLogos-Unlicense.txt"),
    "iec": ("IEC Power Symbols", "https://unicodepowersymbol.com/",
            "MIT", "not stated in a machine-readable licence file",
            "the licence is recorded by the Nerd Fonts audit; the upstream "
            "publishes no licence file, so none is reproduced here and the "
            "audit is the citation", None),
}


def nerd_inventory(font_path: str, source_path: str):
    """Which symbol sets are actually in the shipped font, measured.

    Driven off the source's glyph names rather than a hand-kept list, so the
    notice cannot claim a set the build dropped, or omit one it kept.
    """
    from fontTools.ttLib import TTFont
    if not os.path.exists(source_path):
        return None
    src = TTFont(source_path, lazy=True)
    ours = TTFont(font_path, lazy=True)
    scmap, ocmap = src.getBestCmap(), ours.getBestCmap()
    found = {}
    for cp, name in scmap.items():
        prefix = (name or "").split("-")[0]
        if prefix not in NERD_SETS or cp not in ocmap:
            continue
        found.setdefault(prefix, []).append(cp)
    src.close()
    ours.close()
    return {k: (len(v), min(v), max(v)) for k, v in found.items()}


NOTE = """\
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

"""


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    lines = [NOTE]
    for name, archive, url, lic, lic_path, use in SOURCES:
        lines.append(f"### {name}\n")
        lines.append(f"- Upstream: {url}")
        if os.path.exists(archive):
            lines.append(f"- SHA-256 of `{archive}`: `{sha256(archive)}`")
        for extra, extra_url, why in EXTRA_FILES.get(name, []):
            lines.append(f"- Also `{os.path.basename(extra)}` — {why}")
            lines.append(f"  - Upstream: {extra_url}")
            if os.path.exists(extra):
                lines.append(f"  - SHA-256: `{sha256(extra)}`")
        lines.append(f"- License: {lic}"
                     + (f" (text: `{lic_path}`)" if os.path.exists(lic_path) else ""))
        lines.append(f"- Used for: {use}\n")

    for name, url, tag, commit, lic, lic_path, use in GIT_SOURCES:
        lines.append(f"### {name}\n")
        lines.append(f"- Upstream: {url}")
        lines.append(f"- Tag: `{tag}`, asserted at commit `{commit}`")
        lines.append(f"- License: {lic}"
                     + (f" (text: `{lic_path}`)" if os.path.exists(lic_path) else ""))
        lines.append(f"- Used for: {use}\n")

    lines.append("""\
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

""")

    inv = nerd_inventory("dist/HarenaTermK-Regular.ttf",
                         "sources/cand/IosevkaTerm/"
                         "IosevkaTermNerdFontMono-Regular.ttf")
    if inv:
        # Merged by project: two prefixes can name the same upstream, and
        # listing it twice reads as two separate grants.
        merged: dict[str, list] = {}
        for key, (count, lo, hi) in inv.items():
            project = NERD_SETS[key][0]
            row = merged.setdefault(project, [0, lo, hi, key])
            row[0] += count
            row[1] = min(row[1], lo)
            row[2] = max(row[2], hi)
        lines.append(f"{sum(n for n, _, _ in inv.values())} symbol glyphs "
                     f"across {len(merged)} sets:\n")
        lines.append("| Set | Glyphs | Range | License | Copyright "
                     "| License text |")
        lines.append("|---|---:|---|---|---|---|")
        for project in sorted(merged, key=lambda p: -merged[p][0]):
            count, lo, hi, key = merged[project]
            _, url, lic, copy, _, licfile = NERD_SETS[key]
            rng = (f"U+{lo:04X}" if lo == hi else f"U+{lo:04X}–U+{hi:04X}")
            ref = f"[`{licfile}`](licenses/{licfile})" if licfile else "— *(see note)*"
            lines.append(f"| [{project}]({url}) | {count} | `{rng}` | "
                         f"{lic} | {copy} | {ref} |")
        lines.append("")
        notes = [(NERD_SETS[k][0], NERD_SETS[k][4])
                 for k in sorted(inv, key=lambda k: NERD_SETS[k][0])
                 if NERD_SETS[k][4]]
        notes = list(dict.fromkeys(notes))
        if notes:
            lines.append("Notes on individual sets:\n")
            for project, note in notes:
                lines.append(f"- **{project}** — {note}")
            lines.append("")
        lines.append("""\
Two of these sets sit partly **outside the private use area**, at ordinary
Unicode codepoints that appear in normal text — IEC Power Symbols at
U+23FB–U+23FE and U+2B58, and two Octicons at U+2665 `♥` and U+26A1 `⚡`. Any
future subsetting has to work from a codepoint list rather than a set name, or
it will silently remove real characters.
""")
    else:
        lines.append("> **The set table could not be generated**: the Nerd "
                     "Fonts source archive was not found. Re-run after "
                     "fetching sources, and do not distribute without it.\n")

    lines.append("""\
## License texts included

Several of the licences above require their text to travel with the work rather
than be linked — Apache-2.0 §4(a) explicitly, and the OFL and CC BY 4.0 in
substance. The full texts are in `licenses/`:

""")
    for p in sorted(glob.glob("licenses/*")):
        lines.append(f"- [`{os.path.basename(p)}`]({p}) — "
                     f"{os.path.getsize(p) / 1024:.1f} KB")
    lines.append("""
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

""")

    for p in sorted(glob.glob("dist/*") + glob.glob("dist/hinted/*")):
        if os.path.isdir(p):
            continue
        lines.append(f"- `{os.path.relpath(p, 'dist')}` — "
                     f"{os.path.getsize(p) / 1e6:.2f} MB — `{sha256(p)}`")

    if os.path.exists("build/build-report.json"):
        rep = json.load(open("build/build-report.json"))
        lines.append("\n## Base binaries consumed\n")
        seen = set()
        for r in rep.values():
            if r["base"] not in seen:
                seen.add(r["base"])
                lines.append(f"- `{r['base']}` — `{r['base_sha256']}`")

    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
        if rev:
            lines.append(f"\nBuilt from commit `{rev}`.")
    except Exception:  # noqa: BLE001
        pass

    with open("THIRD_PARTY_NOTICES.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote THIRD_PARTY_NOTICES.md")


if __name__ == "__main__":
    main()
