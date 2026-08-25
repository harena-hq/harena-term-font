#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
"""Read the font VERSION without importing the build or its dependencies."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

BUILD = Path(__file__).resolve().parent / "build.py"


def read_version(path: Path = BUILD) -> str:
    tree = ast.parse(path.read_text(), filename=str(path))
    versions = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (isinstance(target, ast.Name) and target.id == "VERSION"
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            versions.append(node.value.value)
    if len(versions) != 1:
        raise ValueError(
            f"expected exactly one literal VERSION assignment in {path}; "
            f"found {len(versions)}"
        )
    return versions[0]


def semver(font_version: str) -> str:
    """Translate the font's X.YYY revision into the repository's X.Y.Z tag."""
    major, encoded = font_version.split(".", 1)
    if len(encoded) < 2 or not (major + encoded).isdigit():
        raise ValueError(f"unsupported font version: {font_version!r}")
    return f"{int(major)}.{int(encoded[0])}.{int(encoded[1:])}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semver", action="store_true")
    args = parser.parse_args()
    version = read_version()
    print(semver(version) if args.semver else version)


if __name__ == "__main__":
    main()
