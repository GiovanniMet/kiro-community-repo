#!/usr/bin/env bash
set -euo pipefail

rm -rf site
mkdir -p site
cp -a dists site/
cp -a public site/
cp KEYS site/KEYS
cp index.html site/index.html
: > site/.nojekyll

# Intentionally do not copy pool/: GitHub Pages serves metadata only.
if find site -name '*.deb' -print | grep -q .; then
  echo 'ERROR: a .deb would be published to GitHub Pages' >&2
  exit 1
fi
