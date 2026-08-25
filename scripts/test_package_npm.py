#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um

import re
import tempfile
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

import font_version
import package_npm


class PackageMetadataTests(unittest.TestCase):
    def test_font_version_requires_one_literal_assignment(self) -> None:
        cases = {
            "VERSION = '1.000'\n": "1.000",
            "pass\n": None,
            "VERSION = '1.000'\nVERSION = '2.000'\n": None,
        }
        for source, expected in cases.items():
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "build.py"
                path.write_text(source)
                if expected is None:
                    with self.assertRaisesRegex(ValueError, "exactly one"):
                        font_version.read_version(path)
                else:
                    self.assertEqual(font_version.read_version(path), expected)

    def test_font_revision_converts_to_semver(self) -> None:
        cases = {
            "0.900": "0.9.0",
            "1.000": "1.0.0",
            "1.012": "1.0.12",
            "1.100": "1.1.0",
            "2.310": "2.3.10",
        }
        for revision, expected in cases.items():
            with self.subTest(revision=revision):
                self.assertEqual(package_npm.semver(revision), expected)

    def test_package_patch_may_reuse_the_same_font_release(self) -> None:
        current_font = package_npm.semver(package_npm.FONT_VERSION)
        package_version, font_version = package_npm.validate_package(
            {
                "version": "999.0.1",
                "harena": {"fontVersion": current_font},
            }
        )
        self.assertEqual(package_version, "999.0.1")
        self.assertEqual(font_version, current_font)

    def test_declared_font_version_must_match_the_build(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match the font"):
            package_npm.validate_package(
                {
                    "version": "1.0.1",
                    "harena": {"fontVersion": "not-the-build-version"},
                }
            )

    def test_css_urls_name_exactly_the_packaged_fonts(self) -> None:
        urls = []
        pattern = re.compile(r"url\(([^)]+)\)")
        for path in package_npm.PACKAGE_SOURCE.glob("*.css"):
            urls.extend(pattern.findall(path.read_text()))

        targets = []
        for value in urls:
            relative = value.strip().strip("\"'")
            self.assertTrue(
                relative.startswith("./fonts/"),
                f"font URL is not package-relative: {relative}",
            )
            targets.append(relative.removeprefix("./fonts/"))

        self.assertCountEqual(targets, package_npm.EXPECTED_FONTS)

    def test_css_faces_match_the_font_family_and_weight(self) -> None:
        face_pattern = re.compile(r"@font-face\s*{([^}]+)}", re.DOTALL)
        property_patterns = {
            "family": re.compile(r'font-family:\s*"([^"]+)"'),
            "url": re.compile(r'url\("\./fonts/([^"]+)"\)'),
            "weight": re.compile(r"font-weight:\s*(\d+)"),
        }
        checked = []
        for css_name, expected_family in (
                ("k.css", "Harena Term K"),
                ("j.css", "Harena Term J")):
            css = (package_npm.PACKAGE_SOURCE / css_name).read_text()
            for block in face_pattern.findall(css):
                values = {
                    name: pattern.search(block).group(1)
                    for name, pattern in property_patterns.items()
                }
                self.assertEqual(values["family"], expected_family)
                font_path = package_npm.DIST / values["url"]
                with TTFont(font_path, lazy=True) as font:
                    families = {record.toUnicode() for record in font["name"].names
                                if record.nameID in (1, 16)}
                    weight = font["OS/2"].usWeightClass
                self.assertIn(values["family"], families)
                self.assertEqual(int(values["weight"]), weight)
                checked.append(values["url"])

        self.assertCountEqual(checked, package_npm.EXPECTED_FONTS)


if __name__ == "__main__":
    unittest.main()
