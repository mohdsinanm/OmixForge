#!/usr/bin/env python3
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
VERSION_FILE = ROOT / "src/utils/version.py"
CHANGELOG = ROOT / "debian/changelog"


def update_pyproject(version: str) -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    new_text, count = re.subn(r'(?m)^version\s*=\s*"[^"]+"', f'version = "{version}"', text, count=1)
    if count != 1:
        raise ValueError("Could not find project version line in pyproject.toml")
    PYPROJECT.write_text(new_text, encoding="utf-8")


def update_version_file(version: str) -> None:
    text = VERSION_FILE.read_text(encoding="utf-8")
    new_text, count = re.subn(r'(?m)^APP_VERSION\s*=\s*"[^"]+"', f'APP_VERSION = "{version}"', text, count=1)
    if count != 1:
        raise ValueError("Could not find APP_VERSION in src/utils/version.py")
    VERSION_FILE.write_text(new_text, encoding="utf-8")


def update_changelog(version: str, release_note: str | None = None) -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines:
        raise ValueError("debian/changelog is empty")

    first = lines[0]
    if not first.startswith("omixforge ("):
        raise ValueError("debian/changelog does not start with an omixforge package entry")

    current_version_match = re.match(r"^omixforge \((\d+\.\d+\.\d+)", first)
    if current_version_match and current_version_match.group(1) == version:
        return

    entry = re.sub(r'^omixforge \([^)]+\)', f'omixforge ({version}-1)', first, count=1)
    if entry == first:
        raise ValueError("Could not update the version in debian/changelog")

    lines[0] = entry
    CHANGELOG.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if release_note is not None:
        date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        new_entry = (
            f"omixforge ({version}-1) noble; urgency=medium\n\n"
            f"  * {release_note}\n\n"
            f" -- Sinan <mohamedysf@bicpu.edu.in>  {date}\n\n"
            f"{CHANGELOG.read_text(encoding='utf-8')}"
        )
        CHANGELOG.write_text(new_entry, encoding="utf-8")


def main() -> None:
    release_note = None
    args = sys.argv[1:]
    if not args:
        print("Usage: python scripts/sync_version.py [--release <note>] <version>")
        raise SystemExit(2)

    if args[0] == "--release":
        if len(args) < 3:
            print("Usage: python scripts/sync_version.py --release \"Release note\" 1.2.0")
            raise SystemExit(2)
        release_note = args[1]
        version = args[2].strip()
    else:
        version = args[0].strip()

    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Version must use semantic format like 1.2.0")

    update_pyproject(version)
    update_version_file(version)
    update_changelog(version, release_note)
    print(f"Synced version to {version}")


if __name__ == "__main__":
    main()
