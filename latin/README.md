# Parametric Latin

`private-build-plans.toml` is the source of the shipping Latin. It is tracked
here because `sources/` is gitignored, and without it the build is not
reproducible — the binaries would be the only record of what `cap`, `sb` and
`shape` were set to.

It holds **one plan, `HarenaLatin`** — the cut that ships. The comparison cuts
from the parameter search are recorded below as parameters rather than kept as
plans, since a plan file with seven entries builds seven fonts and six of them
lost.

To build:

```sh
scripts/fetch_sources.sh
```

That clones Iosevka at the pinned tag, asserts the commit, installs with
`npm ci` against upstream's lockfile, writes the `ttfautohint` shim and runs
`ttf::HarenaLatin`. It used to be four manual commands here, two of which were
not reproducible: a `--depth 1` clone of the default branch pins nothing, and
`npm install` resolves whatever satisfies the ranges today.

`ttfautohint` is not packaged with a CLI entry point, so the shim written to
`build/bin/` wraps the `ttfautohint-py` module (`pip install ttfautohint-py`).
Without it Iosevka refuses the hinted target, and the Nerd Font binaries merged
alongside it *are* hinted, so an unhinted Latin would not compare fairly at
13px.

The shipping plan is `shape = 500`, `sb = 45`, `cap = 808`, `xHeight = 572`,
`leading = 1350`, with width and slope pinned to a single value.

The search that arrived there, all sharing `cap = 808` unless noted:

| `shape` | `sb` | `cap` | outcome |
|---|---|---|---|
| 400 | 40 | 808 | the first redraw; reads 22% lighter than Pretendard |
| 500 | 40 | 808 | weight matched to −10.8%; spacing too tight |
| 600 | 40 | 808 | weight matched to −0.9%; Bold hangul runs out of cell |
| **500** | **45** | **808** | **ships** — letterspacing on Pretendard (+0.3%) |
| 500 | 50 | 808 | more air on the widest letters |
| 500 | 45 | 785 | shorter letters, same widths |
| 500 | 45 | 760 | shorter still |

`shape` sets the stroke and is independent of both `cap` and `sb`, so changing
either alone leaves the CJK weight compensation valid.

`cap` and `sb` are not interchangeable. `sb` sets the glyph widths and so the
letterspacing; `cap` sets only the height. Measured across `cap` 808, 785 and 760
the letterspacing is identical to four decimals — T 0.2123, minimum gap 0.0500,
mean gap 0.0875 — while `cap/advance` moves 1.616 → 1.570 → 1.520. Lowering
`cap` makes the letters shorter at unchanged width, which opens vertical space
and reads heavier, and raises the hangul-to-cap ratio because the hangul does
not follow.
