#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Jeeyong Um

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: install/install-unix.sh [--from <dir> | --version <tag>]

Install Harena Term TrueType fonts. Without options, fonts are downloaded
from the latest GitHub release.
USAGE
}

from_dir=''
version=''
while [ "$#" -gt 0 ]; do
  case "$1" in
    --from)
      if [ "$#" -lt 2 ]; then
        printf 'error: --from requires a directory\n' >&2
        exit 2
      fi
      from_dir=$2
      shift 2
      ;;
    --version)
      if [ "$#" -lt 2 ]; then
        printf 'error: --version requires a tag\n' >&2
        exit 2
      fi
      version=$2
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

if [ -n "$from_dir" ] && [ -n "$version" ]; then
  printf 'error: --from and --version cannot be used together\n' >&2
  exit 2
fi

system=$(uname -s)
case "$system" in
  Darwin) dest="$HOME/Library/Fonts";;
  Linux) dest="${XDG_DATA_HOME:-$HOME/.local/share}/fonts";;
  *)
    printf 'error: unsupported system: %s\n' "$system" >&2
    exit 1
    ;;
esac
mkdir -p "$dest"

tmp_dir=''
cleanup() {
  if [ -n "$tmp_dir" ]; then
    rm -rf "$tmp_dir"
  fi
}
trap cleanup EXIT

ttf_files=()
if [ -n "$from_dir" ]; then
  if [ ! -d "$from_dir" ]; then
    printf 'error: source directory does not exist: %s\n' "$from_dir" >&2
    exit 1
  fi
  while IFS= read -r -d '' file; do
    ttf_files+=("$file")
  done < <(find "$from_dir" -maxdepth 1 -type f -name '*.ttf' -print0)
else
  tmp_dir=$(mktemp -d)
  archive="$tmp_dir/HarenaTerm-ttf.zip"
  extract_dir="$tmp_dir/extracted"
  if [ -n "$version" ]; then
    url="https://github.com/harena-hq/harena-term-font/releases/download/$version/HarenaTerm-ttf.zip"
  else
    url='https://github.com/harena-hq/harena-term-font/releases/latest/download/HarenaTerm-ttf.zip'
  fi
  curl -fSL --retry 3 -o "$archive" "$url"
  mkdir -p "$extract_dir"
  unzip -q -o "$archive" -d "$extract_dir"
  while IFS= read -r -d '' file; do
    ttf_files+=("$file")
  done < <(find "$extract_dir" -type f -name '*.ttf' -print0)
fi

if [ "${#ttf_files[@]}" -eq 0 ]; then
  if [ -n "$from_dir" ]; then
    printf 'error: source directory contains no .ttf files: %s\n' "$from_dir" >&2
  else
    printf 'error: downloaded archive contains no .ttf files\n' >&2
  fi
  exit 1
fi

installed=0
for file in "${ttf_files[@]}"; do
  target="$dest/$(basename "$file")"
  cp "$file" "$target"
  printf 'installed %s\n' "$target"
  installed=$((installed + 1))
done

if [ "$system" = Linux ] && command -v fc-cache >/dev/null 2>&1; then
  fc-cache -f "$dest"
fi
printf 'Installed %d fonts to %s\n' "$installed" "$dest"
