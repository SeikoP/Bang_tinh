#!/usr/bin/env python
"""
Automatic versioning and changelog generation script.

This script analyzes git commit messages to determine version bumps
and generates changelog entries based on conventional commits.

Conventional Commit Format:
- feat: New feature (minor version bump)
- fix: Bug fix (patch version bump)
- BREAKING CHANGE: Breaking change (major version bump)
- docs: Documentation changes (no version bump)
- chore: Maintenance tasks (no version bump)
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class Version:
    """Semantic version representation"""

    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, version_str: str) -> "Version":
        """Parse version from string like '2.0.0' or 'v2.0.0'"""
        version_str = version_str.lstrip("v")
        parts = version_str.split(".")
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))

    def bump_major(self) -> "Version":
        """Bump major version (breaking changes)"""
        return Version(self.major + 1, 0, 0)

    def bump_minor(self) -> "Version":
        """Bump minor version (new features)"""
        return Version(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "Version":
        """Bump patch version (bug fixes)"""
        return Version(self.major, self.minor, self.patch + 1)


class CommitAnalyzer:
    """Analyzes git commits for versioning and changelog"""

    COMMIT_PATTERNS = {
        "breaking": re.compile(r"BREAKING CHANGE:", re.IGNORECASE),
        "feat": re.compile(r"^feat(\(.+?\))?:", re.IGNORECASE),
        "fix": re.compile(r"^fix(\(.+?\))?:", re.IGNORECASE),
        "docs": re.compile(r"^docs(\(.+?\))?:", re.IGNORECASE),
        "chore": re.compile(r"^chore(\(.+?\))?:", re.IGNORECASE),
        "refactor": re.compile(r"^refactor(\(.+?\))?:", re.IGNORECASE),
        "test": re.compile(r"^test(\(.+?\))?:", re.IGNORECASE),
        "perf": re.compile(r"^perf(\(.+?\))?:", re.IGNORECASE),
    }

    def __init__(self):
        self.commits = []

    def get_commits_since_tag(self, tag: str = None) -> List[str]:
        """Get all commits since the last tag"""
        if tag:
            cmd = ["git", "log", f"{tag}..HEAD", "--pretty=format:%H|%s|%b"]
        else:
            cmd = ["git", "log", "--pretty=format:%H|%s|%b"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                commits.append(line)
        return commits

    def analyze_commits(self, commits: List[str]) -> Dict[str, List[str]]:
        """Categorize commits by type"""
        categorized = {
            "breaking": [],
            "features": [],
            "fixes": [],
            "performance": [],
            "refactoring": [],
            "documentation": [],
            "other": [],
        }

        for commit in commits:
            parts = commit.split("|")
            if len(parts) < 2:
                continue

            commit_hash = parts[0][:7]
            subject = parts[1]
            body = parts[2] if len(parts) > 2 else ""

            # Check for breaking changes
            if self.COMMIT_PATTERNS["breaking"].search(body) or self.COMMIT_PATTERNS[
                "breaking"
            ].search(subject):
                categorized["breaking"].append(f"- {subject} ({commit_hash})")
            # Check for features
            elif self.COMMIT_PATTERNS["feat"].match(subject):
                categorized["features"].append(f"- {subject} ({commit_hash})")
            # Check for fixes
            elif self.COMMIT_PATTERNS["fix"].match(subject):
                categorized["fixes"].append(f"- {subject} ({commit_hash})")
            # Check for performance
            elif self.COMMIT_PATTERNS["perf"].match(subject):
                categorized["performance"].append(f"- {subject} ({commit_hash})")
            # Check for refactoring
            elif self.COMMIT_PATTERNS["refactor"].match(subject):
                categorized["refactoring"].append(f"- {subject} ({commit_hash})")
            # Check for documentation
            elif self.COMMIT_PATTERNS["docs"].match(subject):
                categorized["documentation"].append(f"- {subject} ({commit_hash})")
            else:
                categorized["other"].append(f"- {subject} ({commit_hash})")

        return categorized

    def determine_version_bump(self, categorized: Dict[str, List[str]]) -> str:
        """Determine version bump type based on commits"""
        if categorized["breaking"]:
            return "major"
        elif categorized["features"]:
            return "minor"
        elif categorized["fixes"] or categorized["performance"]:
            return "patch"
        else:
            return "none"


class ChangelogGenerator:
    """Generates changelog from categorized commits"""

    def __init__(self, changelog_path: Path = Path("CHANGELOG.md")):
        self.changelog_path = changelog_path

    def generate_entry(
        self, version: Version, categorized: Dict[str, List[str]]
    ) -> str:
        """Generate changelog entry for a version"""
        date = datetime.now().strftime("%Y-%m-%d")
        entry = f"\n## [{version}] - {date}\n\n"

        if categorized["breaking"]:
            entry += "### ⚠️ BREAKING CHANGES\n\n"
            entry += "\n".join(categorized["breaking"]) + "\n\n"

        if categorized["features"]:
            entry += "### ✨ Features\n\n"
            entry += "\n".join(categorized["features"]) + "\n\n"

        if categorized["fixes"]:
            entry += "### 🐛 Bug Fixes\n\n"
            entry += "\n".join(categorized["fixes"]) + "\n\n"

        if categorized["performance"]:
            entry += "### ⚡ Performance Improvements\n\n"
            entry += "\n".join(categorized["performance"]) + "\n\n"

        if categorized["refactoring"]:
            entry += "### ♻️ Code Refactoring\n\n"
            entry += "\n".join(categorized["refactoring"]) + "\n\n"

        if categorized["documentation"]:
            entry += "### 📚 Documentation\n\n"
            entry += "\n".join(categorized["documentation"]) + "\n\n"

        return entry

    def update_changelog(self, version: Version, categorized: Dict[str, List[str]]):
        """Update CHANGELOG.md with new version entry"""
        entry = self.generate_entry(version, categorized)

        if self.changelog_path.exists():
            content = self.changelog_path.read_text(encoding="utf-8")
            # Insert after the header
            lines = content.split("\n")
            header_end = 0
            for i, line in enumerate(lines):
                if line.startswith("# Changelog") or line.startswith("# CHANGELOG"):
                    header_end = i + 1
                    break

            lines.insert(header_end, entry)
            self.changelog_path.write_text("\n".join(lines), encoding="utf-8")
        else:
            # Create new changelog
            header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n"
            self.changelog_path.write_text(header + entry, encoding="utf-8")


def get_latest_tag() -> str:
    """Get the latest git tag"""
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def create_tag(version: Version, message: str = None):
    """Create a new git tag"""
    tag_name = f"v{version}"
    tag_message = message or f"Release {version}"

    subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_message])
    print(f"Created tag: {tag_name}")


def main():
    """Main execution"""
    print("🔍 Analyzing commits for versioning...")

    # Get latest tag
    latest_tag = get_latest_tag()
    if latest_tag:
        print(f"Latest tag: {latest_tag}")
        current_version = Version.from_string(latest_tag)
    else:
        print("No tags found, starting from 1.0.0")
        current_version = Version(1, 0, 0)

    # Analyze commits
    analyzer = CommitAnalyzer()
    commits = analyzer.get_commits_since_tag(latest_tag)

    if not commits:
        print("No new commits since last tag")
        return

    print(f"Found {len(commits)} commits since last tag")

    categorized = analyzer.analyze_commits(commits)
    bump_type = analyzer.determine_version_bump(categorized)

    if bump_type == "none":
        print("No version bump needed (only docs/chore commits)")
        return

    # Calculate new version
    if bump_type == "major":
        new_version = current_version.bump_major()
    elif bump_type == "minor":
        new_version = current_version.bump_minor()
    else:
        new_version = current_version.bump_patch()

    print(f"\n📦 Version bump: {current_version} → {new_version} ({bump_type})")

    # Generate changelog
    print("\n📝 Generating changelog...")
    changelog_gen = ChangelogGenerator()
    changelog_gen.update_changelog(new_version, categorized)
    print(f"Updated {changelog_gen.changelog_path}")

    # Update version in config
    config_path = Path("core/config.py")
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8")
        content = re.sub(
            r'app_version=os\.getenv\([\'"]APP_VERSION[\'"],[^\)]+\)',
            f"app_version=os.getenv('APP_VERSION', '{new_version}')",
            content,
        )
        config_path.write_text(content, encoding="utf-8")
        print(f"Updated version in {config_path}")

    print(f"\n✅ Version {new_version} ready!")
    print("\nNext steps:")
    print("1. Review CHANGELOG.md")
    print(
        f"2. Commit changes: git add . && git commit -m 'chore: bump version to {new_version}'"
    )
    print(f"3. Create tag: git tag -a v{new_version} -m 'Release {new_version}'")
    print("4. Push: git push && git push --tags")


if __name__ == "__main__":
    main()
