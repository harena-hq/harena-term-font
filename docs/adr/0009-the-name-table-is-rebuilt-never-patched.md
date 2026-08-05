# 0009 — The name table is rebuilt from nothing, never patched over the base

Status: **permanent**.

## Context

The build opens a base binary and merges CJK into it, so the output inherits
every table the base had — including `name`. The obvious way to name the result
is to set the IDs you care about and let the rest through.

That is wrong here, and the failure is invisible until an end user hits it.

## What patching leaves behind

The base is an Iosevka build, so its `name` table describes an Iosevka build.
Setting IDs 1–6 leaves `nameID 8` and `9` naming Iosevka's author as this font's
manufacturer and designer, `nameID 10` carrying Iosevka's description, and —
worst — `nameID 21` still holding the internal name of the build plan the base
was compiled from.

`nameID 21`/`22` are not cosmetic. **Both macOS and Windows group faces by WWS
family when it is present**, and every face merged from the same base carries the
same one. K Regular, K Bold, J Regular and J Bold therefore look like a single
family to the OS, and a request for one can resolve to any of them. What that
looks like from the outside is "the font renders worse than it should" — the
wrong face being served, with nothing wrong in the outlines.

## Decision

Clear the table and reconstruct it:

```python
base["name"].names = []
for nid, value in names.items():
    set_name(base, nid, value)
```

Fourteen records, chosen deliberately: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 16,
17. **`21` and `22` are absent**, so the OS falls back to `1`/`16` — correct,
because the family/subfamily already follow the weight/width/slope model and WWS
has nothing to add.

Pairing is asserted rather than assumed: family identical within a region,
`usWeightClass` 400/700, `fsSelection` REGULAR/BOLD, `macStyle` 0/1.

## Why patching is the wrong shape in general

**Setting the fields you know about leaves the fields you do not.** That is fine
when you own the base and wrong when you inherit one — and a font base always
carries identity records for a different font. The same shape reaches `OS/2`,
where the consequence is larger still; see
[0012](0012-os2-must-declare-the-scripts-carried.md).

The rule generalises past the `name` table: a build report or manifest that
merges rather than replaces will keep publishing entries whose output no longer
exists. Anything that records what the build produced is written from the current
build, not accumulated across builds.

## Downstream

Renaming the family touches one constant and the naming block, nothing else. The
Latin build plan's own name never reaches the output, which is also what makes
the build reproducible: the Iosevka intermediate differs in `name` between runs,
and that difference is discarded rather than inherited.
