#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
"""Cut one release's notes out of CHANGELOG.md and reflow them for GitHub.

Two steps, and the second is the one that was missing.

**Extract.** The notes come from the changelog entry for the tag, so the two
cannot disagree. The range stops at the next `## ` heading *or* the first link
reference definition, because the newest entry has no heading after it and a
range that only looks for one runs to the end of the file.

**Reflow.** GitHub renders a release body with hard breaks on: every single
newline becomes a `<br>`. The same text in a `.md` file in the repository
renders under CommonMark paragraph rules, where a single newline is a space.
So this file's own prose, wrapped at 78 columns like everything else here,
reads correctly in the repository and comes out ragged in a release -- which is
what v0.9.0 and v1.0.0 shipped.

The wrap is therefore a property of the source format, not of the content, and
undoing it belongs at the boundary where the two renderers differ rather than
in the file. Hard-wrapping the changelog is worth keeping: it is what makes a
diff show the sentence that changed instead of the paragraph.

What survives a reflow untouched: fenced code, table rows, headings, and the
line breaks between list items. What joins: the continuation lines inside one
paragraph, list item or block quote.

**Absolutise links.** The second half of the same problem. A relative link in a
release body is not resolved against the repository -- GitHub's own renderer
leaves `href="docs/adr/0014-....md"` alone, and the browser then resolves it
against the page, which is `/releases/tag/v1.0.0`. Every ADR link in the v0.9.0
and v1.0.0 notes was a 404 for that reason. They are rewritten to blob URLs at
**the tag**, not at the default branch, so a release's notes keep pointing at
the tree that release was cut from.

Both behaviours are checkable rather than assumed:

    gh api -X POST /markdown -f mode=gfm -f context=OWNER/REPO -f text='...'

Usage:  python3 scripts/release_notes.py 1.0.0 [--out release-notes.md]
"""

from __future__ import annotations

import argparse
import os
import re
import sys

CHANGELOG = "CHANGELOG.md"
# `](something)` where something is neither absolute, a fragment, nor a mail
# or protocol link -- i.e. a path inside this repository.
RELLINK = re.compile(r"\]\((?!https?://|mailto:|#)([^)\s]+)\)")

FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
TABLE = re.compile(r"^\s*\|")
LIST = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
QUOTE = re.compile(r"^\s*>")
# `[0.9.0]: ../../releases/tag/v0.9.0` and friends
LINKDEF = re.compile(r"^\[[^]]+\]:\s")


def extract(text: str, version: str) -> list[str]:
    out: list[str] = []
    on = False
    for line in text.split("\n"):
        if re.match(rf"^## \[{re.escape(version)}\]", line):
            on = True
            continue
        if on and (line.startswith("## ") or LINKDEF.match(line)):
            break
        if on:
            out.append(line)
    return out


def reflow(lines: list[str]) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    prefix = ""
    fenced = False

    def flush() -> None:
        nonlocal buf, prefix
        if buf:
            out.append(prefix + " ".join(buf))
            buf, prefix = [], ""

    for line in lines:
        if FENCE.match(line):
            flush()
            out.append(line)
            fenced = not fenced
            continue
        if fenced:
            out.append(line)
            continue
        if not line.strip():
            flush()
            out.append("")
            continue
        if HEADING.match(line) or TABLE.match(line):
            flush()
            out.append(line)
            continue
        if LIST.match(line) or QUOTE.match(line):
            # A list marker or a quote marker starts a new logical line; its
            # own continuations join onto it below. Two markers in a row must
            # not merge, which is why this flushes first.
            flush()
            m = LIST.match(line) or QUOTE.match(line)
            prefix = line[: m.end()]
            buf = [line[m.end():].strip()]
            continue
        # a continuation of whatever is open
        buf.append(line.strip())

    flush()
    while out and not out[-1].strip():
        out.pop()
    return out


def absolutise(lines: list[str], repo: str, ref: str) -> tuple[list[str], int]:
    base = f"https://github.com/{repo}/blob/{ref}/"
    n = 0

    def one(m: re.Match) -> str:
        nonlocal n
        n += 1
        return f"]({base}{m.group(1)})"

    return [RELLINK.sub(one, l) for l in lines], n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("version", help="e.g. 1.0.0, with no leading v")
    ap.add_argument("--out", default="release-notes.md")
    ap.add_argument("--changelog", default=CHANGELOG)
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""),
                    help="owner/name; defaults to GITHUB_REPOSITORY")
    ap.add_argument("--ref", default="",
                    help="git ref the links point at; defaults to v<version>")
    args = ap.parse_args()

    version = args.version.lstrip("v")
    raw = extract(open(args.changelog, encoding="utf-8").read(), version)
    if not any(l.strip() for l in raw):
        print(f"no CHANGELOG entry for {version}", file=sys.stderr)
        return 1
    body = reflow(raw)

    # The reflow may not lose or invent structure. Cheap to assert, and the
    # failure it guards against -- a table row swallowed into a paragraph --
    # is silent in the rendered output.
    for label, pat in (("table rows", TABLE), ("headings", HEADING),
                       ("list items", LIST)):
        a = sum(1 for l in raw if pat.match(l))
        b = sum(1 for l in body if pat.match(l))
        if a != b:
            print(f"reflow changed the number of {label}: {a} -> {b}",
                  file=sys.stderr)
            return 1

    links = 0
    if args.repo:
        body, links = absolutise(body, args.repo, args.ref or f"v{version}")
    else:
        left = sum(len(RELLINK.findall(l)) for l in body)
        if left:
            print(f"--repo not given and {left} relative links would 404 on a "
                  f"release page", file=sys.stderr)
            return 1

    text = "\n".join(body) + "\n"
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {args.out} — {len(body)} lines, longest {max(map(len, body))},"
          f" {links} links absolutised")
    return 0


if __name__ == "__main__":
    sys.exit(main())
