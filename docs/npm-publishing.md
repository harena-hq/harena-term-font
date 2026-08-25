# npm publishing

The npm package is `@harena-hq/term-font`. It is a web distribution containing
the four WOFF2 faces and CSS entry points; desktop TTFs remain GitHub Release
assets.

## Layout

`npm/` is tracked and holds the public package contract: metadata, exports, CSS
and its README and changelog. `dist/` is ignored build output.
`scripts/package_npm.py` joins the two under the ignored
`build/npm-package/` directory and copies the license notices that must travel
with the fonts.

Do not put `package.json` directly in `dist/`. The build output can be deleted
and reconstructed, while package metadata is reviewed source and must remain in
git.

The package and the font have separate versions because CSS, exports or package
metadata can change without changing a glyph. `npm/package.json` records both:

```json
{
  "version": "1.0.1",
  "harena": { "fontVersion": "1.0.0" }
}
```

`version` is the npm package version. `harena.fontVersion` identifies the font
release inside it. `package_npm.py` checks the latter against
`scripts/build.py`, reads the embedded version back from all four WOFF2 files,
then checks their bytes against the tracked `SHA256SUMS`. A CSS-only package
patch therefore reuses byte-identical fonts without restamping or republishing
the TTFs, but cannot silently package stale or locally modified font output.

`scripts/build.py` remains the source of truth for the font version.
`scripts/font_version.py` is its dependency-free reader for release checks: it
parses the file without importing the font build or fontTools and requires
exactly one top-level literal `VERSION` assignment. Normal CI runs it with
`python -S`, so adding an accidental third-party import fails before a tag.

## Inspect locally

Run this after `scripts/postbuild.py` has produced `dist/*.woff2`:

```sh
python3 scripts/package_npm.py
npm pack ./build/npm-package --dry-run
```

To test the exact tarball consumers will install:

```sh
mkdir -p /tmp/harena-npm-pack
npm pack ./build/npm-package --pack-destination /tmp/harena-npm-pack
npm install --ignore-scripts --no-audit --no-fund \
  --prefix /tmp/harena-npm-smoke \
  /tmp/harena-npm-pack/harena-hq-term-font-1.0.0.tgz
```

## Registry bootstrap

Before enabling automatic publication:

1. Create the `harena-hq` organization on npmjs.com.
2. Confirm ownership of `@harena-hq/term-font` and publish its first version
   with an npm account protected by two-factor authentication if npm requires a
   package to exist before its trusted publisher can be configured.
3. In the package settings, register GitHub Actions trusted publishing for
   `harena-hq/harena-term-font` and the workflow `release.yml`.
4. Add the GitHub repository variable `NPM_PUBLISH` with the value `true`.

The already-published `v1.0.0` GitHub Release predates this workflow, so its npm
package must be bootstrapped manually. Re-dispatching that tag would stop when
`gh release create` finds the existing release. Automation starts with the next
tag.

With `NPM_PUBLISH` absent or false, a tag still builds, packs and installs the
npm tarball but does not contact the registry. With it true, the build job
uploads the verified tarball to a separate publisher job. Only that minimal job
has `id-token: write`; it checks out no source and installs no dependencies
before publishing through npm trusted publishing. No long-lived `NPM_TOKEN` is
stored.

Before building, an enabled release confirms through the public registry that
the package version is unused. A version already present in npm fails the
workflow before GitHub assets are published; connectivity and registry errors
also fail rather than being mistaken for an unused version. The publisher job
requires Node 22.14.0 or later and npm 11.5.1 or later.

An `npm-v*` run with `NPM_PUBLISH` disabled remains a full dry run: it rebuilds,
verifies and packs the package, then writes an explicit “nothing was published”
notice to the Actions job summary.

## Versions and tags

A font release changes outlines, metrics, OpenType data or the embedded font
version. Increment the font version, set `harena.fontVersion` to it, and also
increment the npm package according to the package's own SemVer history:

```text
scripts/build.py VERSION = 1.100
npm/package.json harena.fontVersion = 1.1.0
tag = v1.1.0

# if npm 1.0.1 was already a CSS-only patch, for example:
npm/package.json version = 1.1.0
```

This path publishes the TTF and WOFF2 GitHub assets and the npm package.
The two versions may happen to be equal, but the workflow does not require it.
Requiring equality would collide as soon as a CSS-only release consumed a
number later needed by the font.

An npm-only release changes CSS, exports, documentation or package metadata.
Increment only the package version and use an npm tag:

```text
scripts/build.py VERSION = 1.000
npm/package.json version = 1.0.1
npm/package.json harena.fontVersion = 1.0.0
tag = npm-v1.0.1
```

This path rebuilds and verifies the recorded 1.0.0 font bytes, then publishes
only npm 1.0.1. It creates no GitHub font release and does not change TTF or
WOFF2 hashes. It does create a notes-only GitHub Release for the `npm-v*` tag,
using the matching entry from `npm/CHANGELOG.md`; the npm tarball remains a
registry artifact rather than a duplicate GitHub asset. The notes release is
created only after npm publishing succeeds, so an OIDC or registry failure
cannot advertise a package version that does not exist. It is created with
`--latest=false`, preserving `/releases/latest` as the font release that holds
the downloadable TTF and WOFF2 archives.

Every npm publication needs a previously unused, increasing package version.
A font release therefore bumps the npm version from its current value rather
than copying the font version. Choose patch, minor or major from the effect the
new payload has on npm consumers.

Every npm version, whether published beside `v*` or by `npm-v*`, must have a
matching `npm/CHANGELOG.md` entry. The release workflow extracts it before the
font build, so missing package history cannot fail late.

If npm publishing succeeds but the notes-only GitHub Release fails, regenerate
`npm-release-notes.md` with `scripts/release_notes.py` and recover with:

```sh
gh release create npm-vX.Y.Z \
  --latest=false \
  --title "@harena-hq/term-font X.Y.Z" \
  --notes-file npm-release-notes.md
```
