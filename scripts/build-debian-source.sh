#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f debian/changelog ]; then
  echo "ERROR: debian/changelog is required"
  exit 1
fi

UPSTREAM_VERSION=$(dpkg-parsechangelog --show-field Version | cut -d'-' -f1)
ORIG_TARBALL="omixforge_${UPSTREAM_VERSION}.orig.tar.gz"
ORIG_TARBALL_PATH="$(pwd)/../$ORIG_TARBALL"

if [ ! -f "$ORIG_TARBALL_PATH" ]; then
  echo "Creating upstream tarball $ORIG_TARBALL_PATH"
  tmpdir=$(mktemp -d)
  git archive --format=tar HEAD | tar -x -C "$tmpdir"
  tar czf "$ORIG_TARBALL_PATH" --transform "s,^,omixforge-${UPSTREAM_VERSION}/," -C "$tmpdir" .
  rm -rf "$tmpdir"
fi

OUTPUT_DIR="$(pwd)"
rm -f ../omixforge_*_source.changes ../omixforge_*_1.debian.tar.xz ../omixforge_*_1.dsc

yes | debuild -S -sa -us -uc

mv ../omixforge_*_source.changes "$OUTPUT_DIR/" 2>/dev/null || true
mv ../omixforge_*_1.debian.tar.xz "$OUTPUT_DIR/" 2>/dev/null || true
mv ../omixforge_*_1.dsc "$OUTPUT_DIR/" 2>/dev/null || true

if ls "$OUTPUT_DIR"/omixforge_*_source.changes >/dev/null 2>&1; then
  echo "Source package built successfully."
  ls -1 "$OUTPUT_DIR"/omixforge_*_source.changes "$OUTPUT_DIR"/omixforge_*_1.debian.tar.xz "$OUTPUT_DIR"/omixforge_*_1.dsc || true
else
  echo "ERROR: source package artifacts were not found in $OUTPUT_DIR"
  exit 1
fi
