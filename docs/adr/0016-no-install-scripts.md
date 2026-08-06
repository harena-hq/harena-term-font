# 0016 — No install scripts; the OS and package managers do this better

Status: **accepted**. Reverses a decision made earlier in this project's life,
on evidence that was available at the time and read wrongly.

## Decision

The release ships fonts. It ships no installer.

## Context

`install/install-unix.sh` and `install/install-windows.ps1` existed and were
removed. They were added because `naver/d2-coding-font` has them and they were
cheap to write. That reasoning read one reference and called it a convention.

What the four references actually do:

| | distribution |
|---|---|
| [d2-coding-font](https://github.com/naver/d2-coding-font) | Releases + **install scripts** |
| [pretendard](https://github.com/orioncactus/pretendard) | Releases + CDN + npm + **Homebrew / AUR / Nix** |
| [JetBrainsMono](https://github.com/JetBrains/JetBrainsMono) | Releases + **Homebrew / Chocolatey** + ships in the IDE |
| [JetBrainsLxgwNerdMono](https://github.com/lvbibir/JetBrainsLxgwNerdMono) | Releases, three zips, nothing else |

**One of four.** The two with the widest distribution reach it through package
managers rather than scripts, and the fourth does nothing at all.

## Why the scripts do not earn their place

**The OS already does it.** Double-click a TTF and Font Book or the Windows font
viewer opens. `cp *.ttf ~/.local/share/fonts/ && fc-cache -f` is one line and
needs no maintenance. A script that wraps this saves a few clicks once.

**A package manager does the rest better.** Homebrew cask, Scoop, AUR and Nix
solve download, verification, upgrade and uninstall — the last two of which our
scripts never attempted. They are also maintained by an ecosystem rather than by
this repository.

**The download path couples us to our own URL shape.** The scripts hardcoded
`releases/latest/download/HarenaTerm-ttf.zip`. That is a second contract to keep
stable forever, and it fails silently: while this repository was private, the
documented install command returned 404 and nothing in the build could notice.

**The Windows script was never executed.** Sixty-five lines writing to
`HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts` and the user's font
directory, shipped without ever being run, because no PowerShell was available
where it was written. This project gates the font with 158 assertions and was
shipping unverified code that mutates a reader's machine. The asymmetry is the
argument: a defect in the font renders badly, a defect in an installer breaks
something that is not ours.

## Alternatives rejected

- **Keep the scripts and verify Windows first.** Verification would close the
  worst risk and leave the rest: the URL coupling, the maintenance, and a
  capability the OS already provides.
- **Keep only `--from dist`, for people who build it themselves.** The narrowest
  version, and the closest call. Rejected because anyone who has run
  `fetch_sources.sh`, a Node toolchain and a 20-minute build is not the person
  who needs help copying four files into a directory.

## Downstream

If frictionless install is wanted later, the answer is a **Homebrew cask and a
Scoop manifest**, not a script in this tree. Both are small, both live in their
own ecosystems, and both give upgrade and uninstall for free. Neither is needed
until the repository is public and the release URLs are stable.

`docs/COVERAGE.md`, the gate and the build are untouched by this. What changed
is that the repository now claims only what it does: it builds fonts and
publishes them.
