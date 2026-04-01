#!/usr/bin/env python3
"""Automated semantic version bump and file synchronization.

Usage:
    python scripts/version.py [auto|major|minor|patch]

Default mode is auto.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_git(args: list[str], default: str = "") -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return default


def parse_version(v: str) -> tuple[int, int, int]:
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)$", v.strip())
    if not m:
        raise ValueError(f"Invalid version format: {v}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def detect_bump_type() -> str:
    latest_tag = run_git(["describe", "--tags", "--abbrev=0"], default="")
    rev_range = f"{latest_tag}..HEAD" if latest_tag else "HEAD"
    commits = run_git(["log", "--pretty=%s%n%b", rev_range], default="")
    text = commits.lower()

    if "breaking change" in text or re.search(r"\w+\(.+\)!:|\w+!:", text):
        return "major"
    if "feat:" in text or "feat(" in text:
        return "minor"
    return "patch"


def bump(version: tuple[int, int, int], bump_type: str) -> tuple[int, int, int]:
    major, minor, patch = version
    if bump_type == "major":
        return major + 1, 0, 0
    if bump_type == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def replace_regex(path: Path, pattern: str, repl: str) -> None:
    content = path.read_text(encoding="utf-8")
    new_content, count = re.subn(pattern, repl, content, flags=re.MULTILINE)
    if count == 0:
        raise RuntimeError(f"Pattern not found in {path}")
    path.write_text(new_content, encoding="utf-8")


def update_files(new_version: str) -> None:
    version_4 = f"{new_version}.0"
    major, minor, patch = new_version.split(".")

    replace_regex(
        ROOT / "pyproject.toml",
        r'^version\s*=\s*"[^"]+"$',
        f'version = "{new_version}"',
    )
    replace_regex(
        ROOT / "src" / "wms" / "__init__.py",
        r'^__version__\s*=\s*"[^"]+"$',
        f'__version__ = "{new_version}"',
    )
    replace_regex(
        ROOT / "src" / "wms" / "config" / "app.yaml",
        r'^(\s*version:\s*)"[^"]+"$',
        rf'\1"{new_version}"',
    )
    replace_regex(
        ROOT / ".env.example",
        r'^APP_VERSION=.*$',
        f'APP_VERSION={new_version}',
    )
    replace_regex(
        ROOT / "build" / "installer" / "setup.iss",
        r'^#define MyAppVersion "[^"]+"$',
        f'#define MyAppVersion "{new_version}"',
    )

    vi = ROOT / "build" / "version_info.txt"
    content = vi.read_text(encoding="utf-8")
    content = re.sub(r"filevers=\([^\)]*\)", f"filevers=({major}, {minor}, {patch}, 0)", content)
    content = re.sub(r"prodvers=\([^\)]*\)", f"prodvers=({major}, {minor}, {patch}, 0)", content)
    content = re.sub(r"StringStruct\(u'FileVersion',\s*u'[^']+'\)", f"StringStruct(u'FileVersion', u'{version_4}')", content)
    content = re.sub(r"StringStruct\(u'ProductVersion',\s*u'[^']+'\)", f"StringStruct(u'ProductVersion', u'{version_4}')", content)
    vi.write_text(content, encoding="utf-8")


def update_changelog(new_version: str) -> None:
    path = ROOT / "CHANGELOG.md"
    content = path.read_text(encoding="utf-8")
    marker = "## [Unreleased]"
    if marker not in content:
        return

    date_str = dt.date.today().isoformat()
    entry = (
        f"\n## [{new_version}] - {date_str}\n\n"
        "### Changed\n"
        "- Automated version bump via workflow\n"
    )

    if f"## [{new_version}]" in content:
        return

    content = content.replace(marker, marker + entry, 1)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    bump_arg = sys.argv[1].strip().lower() if len(sys.argv) > 1 else "auto"
    if bump_arg not in {"auto", "major", "minor", "patch"}:
        print("Invalid bump type. Use: auto|major|minor|patch", file=sys.stderr)
        return 2

    latest_tag = run_git(["describe", "--tags", "--abbrev=0"], default="v2.0.0")
    current_version = parse_version(latest_tag)
    bump_type = detect_bump_type() if bump_arg == "auto" else bump_arg
    new_version_tuple = bump(current_version, bump_type)
    new_version = f"{new_version_tuple[0]}.{new_version_tuple[1]}.{new_version_tuple[2]}"

    update_files(new_version)
    update_changelog(new_version)

    github_env = os.getenv("GITHUB_ENV")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as f:
            f.write(f"NEW_VERSION={new_version}\n")

    print(f"Bump type: {bump_type}")
    print(f"New version: {new_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
