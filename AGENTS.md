# AGENTS.md

Operating brief for any AI coding agent working in this repository. Claude Code
reads it through the `CLAUDE.md` symlink beside it.

`harena-term-font` builds a dual-script terminal typeface. What the build does and
why each decision was taken is in `docs/adr/` — read the ADR before proposing a
change it already settled. `PLAN.md` is the current shape of the work.

Artifacts — code, docs, comments, commit messages — are written in **English**.

## Private context and publishable history

Assume this repository's history will be published. Write tracked content —
code, docs, commit messages — so that opening the repository later requires no
history rewrite. The unit of exposure is the commit, not the working tree:
deleting a file in a later commit publishes it just as surely as leaving it.

Private context lives in `.private/`, untracked. Read it like any other
context, and treat it as **input only** — nothing from `.private/` reaches a
tracked file, commit message, PR, or issue unless it is first restated in a
form that would be fine published. A rationale worth keeping is *promoted* to a
commit trailer or an ADR in publishable form, never copied across.

`.private/README.md` states what belongs there for this project.

**Run this once per clone**, before the first commit from it:

```sh
git config core.hooksPath .githooks
```

`.gitignore` stops an accidental `git add .`; the tracked `.githooks/pre-commit` is the layer
that survives `git add -f`. That hook only runs if `core.hooksPath` points at it, and git
does not carry local config across a clone — so a fresh clone starts with the guard off,
silently, on a machine where everything else looks configured.
