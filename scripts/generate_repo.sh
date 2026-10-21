#!/usr/bin/env bash
set -euo pipefail

DEB_FILE="build/kiro.deb"
STATE_FILE="state/latest.json"
DIST_DIR="dists/stable"
PACKAGES_DIR="${DIST_DIR}/main/binary-amd64"
POOL_DIR="pool/main/k/kiro"

[[ -s "$DEB_FILE" ]] || { echo "ERROR: $DEB_FILE missing" >&2; exit 1; }
[[ -s "$STATE_FILE" ]] || { echo "ERROR: $STATE_FILE missing" >&2; exit 1; }

VERSION="$(python3 -c 'import json; print(json.load(open("state/latest.json"))["version"])')"
FILENAME="$(python3 -c 'import json; print(json.load(open("state/latest.json"))["filename"])')"
PACKAGE_NAME="$(dpkg-deb -f "$DEB_FILE" Package)"
PACKAGE_VERSION="$(dpkg-deb -f "$DEB_FILE" Version)"
PACKAGE_ARCH="$(dpkg-deb -f "$DEB_FILE" Architecture)"

echo "Metadata version : $VERSION"
echo "Package version  : $PACKAGE_VERSION"
echo "Package architecture: $PACKAGE_ARCH"

[[ "$PACKAGE_ARCH" == "amd64" ]] || {
  echo "ERROR: expected amd64, got $PACKAGE_ARCH" >&2
  exit 1
}

echo "Generating metadata for ${PACKAGE_NAME} ${PACKAGE_VERSION} ${PACKAGE_ARCH}"
mkdir -p "$PACKAGES_DIR" "$POOL_DIR"
cp "$DEB_FILE" "${POOL_DIR}/${FILENAME}"

dpkg-scanpackages --arch amd64 pool /dev/null > "${PACKAGES_DIR}/Packages"
gzip -n -9 -c "${PACKAGES_DIR}/Packages" > "${PACKAGES_DIR}/Packages.gz"

# The binary is used only to derive trusted package metadata. It is never published.
rm -f "${POOL_DIR}/${FILENAME}"
find pool -type d -empty -delete 2>/dev/null || true

rm -f "${DIST_DIR}/InRelease" "${DIST_DIR}/Release" "${DIST_DIR}/Release.gpg"
apt-ftparchive \
  -o APT::FTPArchive::Release::Origin="Kiro Community Repository" \
  -o APT::FTPArchive::Release::Label="Kiro Community Repository" \
  -o APT::FTPArchive::Release::Suite="stable" \
  -o APT::FTPArchive::Release::Codename="stable" \
  -o APT::FTPArchive::Release::Architectures="amd64" \
  -o APT::FTPArchive::Release::Components="main" \
  -o APT::FTPArchive::Release::Description="Community-maintained package repository for Kiro IDE on Linux" \
  release "$DIST_DIR" > "${DIST_DIR}/Release"

cat "${PACKAGES_DIR}/Packages"
