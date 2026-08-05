#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um
#
# Fetch every build input, pinned by SHA-256, and prepare the trees that
# scripts/build.py expects under sources/.
#
# The pins here are the executable form of THIRD_PARTY_NOTICES.md. If a hash
# changes, the upstream file changed and the notice is stale -- that is a
# finding, not a nuisance, because these bytes decide what the font is.
#
# Usage:
#   scripts/fetch_sources.sh              fetch everything and build the Latin
#   scripts/fetch_sources.sh --no-latin   skip the Iosevka build (slow, needs Node)
#   scripts/fetch_sources.sh --list       print the pinned files, one per line
#
# Optional: set HARENA_SOURCE_MIRROR to a base URL holding these files by
# basename. Used only when an upstream fetch fails, which is the failure mode a
# checksum cannot repair -- a hash detects a changed upstream and cannot
# resurrect a deleted one.

set -euo pipefail

cd "$(dirname "$0")/.."

BUILD_LATIN=1
LIST_ONLY=0
case "${1:-}" in
  --no-latin) BUILD_LATIN=0 ;;
  --list)     LIST_ONLY=1 ;;
esac

MIRROR="${HARENA_SOURCE_MIRROR:-}"

# --- pins --------------------------------------------------------------------
# google/fonts is a live repository, so its files are pinned to the commit that
# produced the bytes the shipped binaries were built from, never to a branch.
GF_MPLUS_COMMIT=d714b17ce2379f06daf6295617f961df605dccb5
GF_NOTO_COMMIT=b38c5c93af322c45f633e17ac440ec1e6c94d489

IOSEVKA_TAG=v34.8.0
IOSEVKA_COMMIT=ca3ad8e280e2f0b614a5a7721b047daaf023713d

# One table, read by both the fetcher and `--list`. Anything that needs to know
# what the build inputs are -- the release workflow's source mirror, most of all
# -- must ask this list rather than glob sources/, which also holds extracted
# trees and whatever a local experiment left behind.
#
#      url | sha256 | destination
PINS="\
https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/IosevkaTerm.tar.xz|cad9da572d25e3413f7a15a319d2f3c9e7e915ee016baa99e0d88fc08cf5b781|sources/cand/IosevkaTerm.tar.xz
https://github.com/orioncactus/pretendard/releases/download/v1.3.9/PretendardJP-1.3.9.zip|8dab678c371a1530106ca643b76b2b80d47653d5ba670b01265b48e4c6615d63|sources/PretendardJP-1.3.9.zip
https://raw.githubusercontent.com/google/fonts/$GF_MPLUS_COMMIT/ofl/mplus1p/MPLUS1p-Regular.ttf|2f294ad496432b1608f070d310e3aa2adcf1de4af429f4901df97ec4bd361ed1|sources/mplus1p/MPLUS1p-Regular.ttf
https://raw.githubusercontent.com/google/fonts/$GF_MPLUS_COMMIT/ofl/mplus1p/MPLUS1p-Medium.ttf|28b2f52a40ae988064810b71d67e127df75a16e08d7df4e192d1006e4075394f|sources/mplus1p/MPLUS1p-Medium.ttf
https://raw.githubusercontent.com/google/fonts/$GF_NOTO_COMMIT/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf|194018e6b2b293a7964f037b25c0249ce1418bc9ab3c971060a03aa57861e252|sources/notosanskr/NotoSansKR[wght].ttf
"

# --- helpers -----------------------------------------------------------------
say() { printf '\033[1m==>\033[0m %s\n' "$*"; }

verify() {  # verify <file> <sha256>
  local got
  got=$(sha256sum "$1" | cut -d' ' -f1)
  if [ "$got" != "$2" ]; then
    printf 'FAIL %s\n  expected %s\n  got      %s\n' "$1" "$2" "$got" >&2
    return 1
  fi
}

if [ "$LIST_ONLY" = 1 ]; then
  while IFS='|' read -r _url _sha dest; do
    [ -n "$dest" ] && printf '%s\n' "$dest"
  done <<EOF
$PINS
EOF
  exit 0
fi

fetch() {  # fetch <url> <sha256> <dest>
  local url=$1 sha=$2 dest=$3
  if [ -f "$dest" ] && verify "$dest" "$sha" 2>/dev/null; then
    say "have $(basename "$dest")"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  say "fetch $(basename "$dest")"
  if ! curl -fSL --retry 3 --connect-timeout 20 -o "$dest.part" "$url"; then
    if [ -n "$MIRROR" ]; then
      say "upstream failed; trying mirror"
      curl -fSL --retry 3 --connect-timeout 20 \
        -o "$dest.part" "$MIRROR/$(basename "$dest")"
    else
      printf 'upstream fetch failed and HARENA_SOURCE_MIRROR is unset\n' >&2
      return 1
    fi
  fi
  verify "$dest.part" "$sha"
  mv "$dest.part" "$dest"
}

# --- 1. every pinned download -------------------------------------------------
# Here-doc, not a pipe: a pipeline runs the loop in a subshell, where `set -e`
# on a failed fetch would kill the subshell and let the build carry on with a
# missing input.
while IFS='|' read -r url sha dest; do
  [ -n "$url" ] || continue
  fetch "$url" "$sha" "$dest"
done <<EOF
$PINS
EOF

# --- 2. the two archives that need unpacking ----------------------------------
if [ ! -f sources/cand/IosevkaTerm/IosevkaTermNerdFontMono-Regular.ttf ]; then
  say "extract IosevkaTerm"
  mkdir -p sources/cand/IosevkaTerm
  tar xJf sources/cand/IosevkaTerm.tar.xz -C sources/cand/IosevkaTerm
fi

if [ ! -f sources/pjp/public/variable/PretendardJPVariable.ttf ]; then
  say "extract PretendardJP"
  mkdir -p sources/pjp
  unzip -q -o sources/PretendardJP-1.3.9.zip -d sources/pjp
fi

# --- 3. the width provider ---------------------------------------------------
# Pinned exactly in package.json: this table sets every advance in the font.
if [ ! -d node_modules/@xterm/addon-unicode11 ]; then
  say "install the width provider"
  pnpm install --frozen-lockfile
fi

# --- 4. Iosevka source -- the parametric Latin --------------------------------
# Not a binary download: the shipping Latin is built from source with
# latin/private-build-plans.toml. Pinned to a tag and asserted by commit,
# because a tag can be moved and a commit cannot.
if [ ! -d sources/iosevka-src ]; then
  say "clone Iosevka $IOSEVKA_TAG"
  git clone --filter=blob:none --branch "$IOSEVKA_TAG" \
    https://github.com/be5invis/Iosevka.git sources/iosevka-src
fi

got_commit=$(git -C sources/iosevka-src rev-parse HEAD)
if [ "$got_commit" != "$IOSEVKA_COMMIT" ]; then
  printf 'FAIL sources/iosevka-src\n  expected %s\n  got      %s\n' \
    "$IOSEVKA_COMMIT" "$got_commit" >&2
  exit 1
fi
say "Iosevka at $IOSEVKA_COMMIT"

if [ "$BUILD_LATIN" = 0 ]; then
  say "done (Latin build skipped)"
  exit 0
fi

# ttfautohint-py ships the binary as a Python module with no console script,
# and Iosevka resolves the hinter through TTFAUTOHINT_PATH. Without it Iosevka
# refuses the hinted target, and the Nerd Font binaries merged alongside it are
# hinted, so an unhinted Latin would not compare fairly at 13px.
mkdir -p build/bin
cat > build/bin/ttfautohint <<'SHIM'
#!/bin/sh
exec python3 -m ttfautohint "$@"
SHIM
chmod +x build/bin/ttfautohint

if [ ! -f sources/iosevka-src/dist/HarenaLatin/TTF/HarenaLatin-Regular.ttf ]; then
  say "build the parametric Latin (slow)"
  cp latin/private-build-plans.toml sources/iosevka-src/
  # npm ci, not npm install: upstream ships package-lock.json, so the
  # dependency tree is pinned and the build input is not whatever resolved today.
  (cd sources/iosevka-src && npm ci)
  (cd sources/iosevka-src \
    && TTFAUTOHINT_PATH="$PWD/../../build/bin/ttfautohint" \
       npm run build -- ttf::HarenaLatin)
fi

say "done -- now: python3 scripts/build.py && python3 scripts/postbuild.py"
