#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
"""Assemble the publishable npm package from tracked metadata and WOFF2 output.

`npm/` is the reviewed package contract. `dist/` is reproducible, ignored build
output. This script joins them under `build/npm-package/`, keeping generated
binaries out of git and build-only files out of the registry. It also verifies
the declared font version and every WOFF2 hash; the npm wrapper version remains
independent so CSS-only patches do not restamp unchanged fonts.

Usage: python3 scripts/package_npm.py [--out build/npm-package]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from font_version import read_version, semver

FONT_VERSION = read_version()

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_SOURCE = ROOT / "npm"
DIST = ROOT / "dist"
EXPECTED_FONTS = (
    "HarenaTermJ-Bold.woff2",
    "HarenaTermJ-Regular.woff2",
    "HarenaTermK-Bold.woff2",
    "HarenaTermK-Regular.woff2",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def recorded_hashes(path: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for line in path.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        hashes[name] = digest
    return hashes


def embedded_version(path: Path) -> tuple[float, set[str]]:
    with TTFont(path, lazy=True) as font:
        revision = font["head"].fontRevision
        names = {record.toUnicode() for record in font["name"].names
                 if record.nameID == 5}
    return revision, names


def validate_package(package: dict[str, object]) -> tuple[str, str]:
    package_version = package.get("version")
    if not isinstance(package_version, str) or not package_version:
        raise ValueError("npm/package.json has no package version")
    metadata = package.get("harena")
    font_version = metadata.get("fontVersion") if isinstance(metadata, dict) else None
    expected_font_version = semver(FONT_VERSION)
    if font_version != expected_font_version:
        raise ValueError(
            "npm/package.json harena.fontVersion does not match the font: "
            f"{font_version!r} != {expected_font_version!r}"
        )
    return package_version, expected_font_version


def copy_tree_contents(source: Path, destination: Path) -> None:
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "build/npm-package")
    args = parser.parse_args()
    out = args.out.resolve()

    package = json.loads((PACKAGE_SOURCE / "package.json").read_text())
    try:
        package_version, font_version = validate_package(package)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    missing = [name for name in EXPECTED_FONTS if not (DIST / name).is_file()]
    if missing:
        print(f"missing WOFF2 build output: {', '.join(missing)}", file=sys.stderr)
        return 1

    hashes = recorded_hashes(ROOT / "SHA256SUMS")
    mismatched = []
    for name in EXPECTED_FONTS:
        actual = sha256(DIST / name)
        if hashes.get(name) != actual:
            mismatched.append(name)
    if mismatched:
        print(
            "WOFF2 build output does not match SHA256SUMS: "
            f"{', '.join(mismatched)}",
            file=sys.stderr,
        )
        return 1

    wrong_version = []
    for name in EXPECTED_FONTS:
        revision, names = embedded_version(DIST / name)
        if (abs(revision - float(FONT_VERSION)) >= 1 / 65536
                or names != {f"Version {FONT_VERSION}"}):
            wrong_version.append(name)
    if wrong_version:
        print(
            "WOFF2 embedded version does not match harena.fontVersion: "
            f"{', '.join(wrong_version)}",
            file=sys.stderr,
        )
        return 1

    if out == ROOT or ROOT not in out.parents:
        print(f"refusing output outside the repository: {out}", file=sys.stderr)
        return 1
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    copy_tree_contents(PACKAGE_SOURCE, out)
    (out / "fonts").mkdir()
    for name in EXPECTED_FONTS:
        shutil.copy2(DIST / name, out / "fonts" / name)
    shutil.copy2(ROOT / "OFL.txt", out / "OFL.txt")
    shutil.copy2(ROOT / "THIRD_PARTY_NOTICES.md", out / "THIRD_PARTY_NOTICES.md")
    shutil.copytree(ROOT / "licenses", out / "licenses")

    size = sum(path.stat().st_size for path in out.rglob("*") if path.is_file())
    print(
        f"assembled {package['name']}@{package_version} with Harena Term "
        f"{font_version} in {out} "
        f"({size / 1_000_000:.2f} MB, {len(EXPECTED_FONTS)} fonts)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
