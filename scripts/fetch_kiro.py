#!/usr/bin/env python3
import json
import pathlib
import shutil
import sys
import urllib.error
import urllib.request

METADATA_URL = "https://prod.download.desktop.kiro.dev/stable/metadata-linux-x64-stable.json"
PACKAGE_URL = (
    "https://prod.download.desktop.kiro.dev/releases/stable/"
    "linux-x64/signed/{version}/deb/kiro-ide-{version}-stable-linux-x64.deb"
)
BUILD_DIR = pathlib.Path("build")
DEB_PATH = BUILD_DIR / "kiro.deb"
STATE_PATH = pathlib.Path("state/latest.json")


def request(url: str, method: str = "GET"):
    return urllib.request.Request(
        url,
        method=method,
        headers={"User-Agent": "kiro-community-repo/1.0"},
    )


def main() -> int:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(request(METADATA_URL), timeout=30) as response:
        metadata = json.load(response)

    version = metadata.get("currentRelease")
    if not version:
        print("ERROR: currentRelease missing from Kiro metadata", file=sys.stderr)
        return 1

    package_url = PACKAGE_URL.format(version=version)
    print(f"Latest Kiro release: {version}")
    print(f"Official package URL: {package_url}")

    try:
        with urllib.request.urlopen(request(package_url), timeout=180) as response:
            with DEB_PATH.open("wb") as output:
                shutil.copyfileobj(response, output)
    except urllib.error.HTTPError as error:
        print(f"ERROR: package download returned HTTP {error.code}", file=sys.stderr)
        return 1

    if DEB_PATH.stat().st_size == 0:
        print("ERROR: downloaded package is empty", file=sys.stderr)
        return 1

    filename = f"kiro-ide-{version}-stable-linux-x64.deb"
    STATE_PATH.write_text(
        json.dumps(
            {"version": version, "filename": filename, "url": package_url},
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
