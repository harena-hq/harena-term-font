# 0015 — TTF and WOFF2 only; OTF and TTC measured and declined

Status: **accepted**. OTF is declined structurally; TTC is declined on arithmetic
and can be revisited against a number recorded here.

## Decision

Two release artefacts: `HarenaTerm-ttf.zip` and `HarenaTerm-woff2.zip`.

## OTF (CFF outlines) — declined structurally

The outlines are TrueType quadratics, inherited from Iosevka and Pretendard and
then hinted. Producing CFF is not a re-wrap, it is a different font:

- **The hinting does not survive.** ttfautohint hints 36859 of the face's 38478
  glyphs ([0010](0010-ttfautohint-hints-y-only.md)), specifically so the face
  holds up under ClearType. CFF uses a different hinting model; TrueType
  instructions have nowhere to go. The Windows work would be discarded.
- **Curve conversion is an approximation.** Quadratic to cubic moves points, so
  every measurement taken against the cell boundary has to be retaken — the
  worst overflow currently sits at exactly 1.0000 and the widest CJK ink at
  0.9760, which is not margin to spend on a conversion.
- **The gate cannot run.** All 166 checks read `glyf`. A CFF font has none, so a
  large share of `verify.py` would need a second implementation, and the
  clean-room reproducibility proof would need a second path beside it.

The only real gain is file size, and that is already answered: WOFF2 for the web
at 4.9 MB, and desktop users get the TTF from Releases where 18 MB is not a
constraint.

## TTC (collection) — declined on the measurement

The intuition is strong and wrong. `Harena Term K` and `Harena Term J` differ in
only 611 codepoints of 37652 ([0006](0006-two-regional-cuts-with-ss05-baked-in.md)),
which suggests a collection would nearly halve the bytes.

**A TTC shares whole tables that are byte-identical, not glyphs.** Measured on
the shipped faces:

| K and J, Regular | |
|---|---|
| shareable — `GSUB` 0.104, `cmap` 0.092, `fpgm`, `GDEF`, `cvt`, `prep` | **0.203 MB** |
| not shareable — **`glyf` 17.66**, `loca` 0.154, `hmtx` 0.153, `name`, `head` | 18.0 MB |
| two files separately | 36.33 MB |
| as a TTC | 36.13 MB |
| **saved** | **0.6%** |

`glyf` is 97% of the file, and 611 differing glyphs are enough to make it not
byte-identical, so all 17.66 MB stays duplicated. `loca` and `hmtx` follow for
the same reason. Regular against Bold shares even less, every outline differing.

**A glyph-level path exists and was not measured.** Iosevka builds its own
collections with `otb-ttc-bundle`, which constructs a shared `glyf`; that could
approach the naive intuition. Measuring it means adding the toolchain, which is
the cost this decision is declining, so the number is genuinely unknown rather
than known to be bad.

Even if it were free, three costs remain:

- **The primary consumer cannot use it.** The target renderer is xterm.js
  loading WOFF2 through `@font-face`. WOFF2 has a collection form with
  effectively no browser support, so the case this project optimises for gains
  nothing.
- **The gate needs `fontNumber` indexing**, running all 166 checks per face
  inside the collection, and `SHA256SUMS` gains an artefact to prove.
- **Installation gets harder**, particularly per-face registration on Windows,
  and font pickers that show only the first face in a collection are common.

## The difference between the two refusals

OTF is a **no**: it discards work and forks the verification story to gain
something already solved.

TTC is a **not now**: the only thing wrong with it is that 0.6% does not pay for
the work. If someone asks for one-file-per-family installation, measure
`otb-ttc-bundle` against these faces first — that is the number this decision
turns on, and it is the one number here that was not taken.
