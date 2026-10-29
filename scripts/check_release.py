#!/usr/bin/env python3
import json
import os
import pathlib
import urllib.request

METADATA_URL = "https://prod.download.desktop.kiro.dev/stable/metadata-linux-x64-stable.json"
STATE_PATH = pathlib.Path("state/latest.json")


def main() -> int:
    request = urllib.request.Request(
        METADATA_URL,
        headers={"User-Agent": "kiro-community-repo/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        metadata = json.load(response)

    version = metadata.get("currentRelease")
    if not isinstance(version, str) or not version:
        raise SystemExit("ERROR: currentRelease missing from Kiro metadata")

    if STATE_PATH.exists():
        with STATE_PATH.open(encoding="utf-8") as state_file:
            state = json.load(state_file)
        state_version = state.get("version")
        if not isinstance(state_version, str) or not state_version:
            raise SystemExit("ERROR: version missing from state/latest.json")
    else:
        state_version = None

    update_required = version != state_version
    print(f"Latest Kiro version: {version}")
    print(f"Repository version: {state_version or 'not set'}")
    print(f"Update required: {update_required}")

    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"update-required={str(update_required).lower()}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
