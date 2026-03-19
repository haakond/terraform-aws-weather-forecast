"""
Property-based test infrastructure for .kiro/steering/ files.

Helper functions only — test functions are added in Task 2.
"""

import re
from pathlib import Path

import pytest
import yaml

STEERING_DIR = Path(".kiro/steering")


def steering_files() -> list[Path]:
    """Return a list of Path objects for all .md files in .kiro/steering/."""
    return sorted(STEERING_DIR.glob("*.md"))


def parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter from a steering file.

    Returns a dict of the frontmatter fields, or an empty dict if the file
    has no frontmatter (i.e. does not start with '---').
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    # Find the closing '---' delimiter
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    raw_yaml = text[3:end].strip()
    try:
        result = yaml.safe_load(raw_yaml)
        return result if isinstance(result, dict) else {}
    except yaml.YAMLError:
        return {}


def extract_headings(path: Path) -> list[str]:
    """Extract all ##-level (and deeper) section headings from the file body.

    Frontmatter is excluded. Returns a list of heading strings (without the
    leading '#' characters or surrounding whitespace).
    """
    text = path.read_text(encoding="utf-8")

    # Strip frontmatter if present
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]  # skip past the closing '---\n'

    headings = []
    for line in text.splitlines():
        match = re.match(r"^(#{2,})\s+(.+)", line)
        if match:
            headings.append(match.group(2).strip())
    return headings


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------

# Feature: steering-optimization, Property 1: only approved files use inclusion: always
APPROVED_ALWAYS = {"product.md", "workflow.md"}


def test_only_approved_files_are_always_included():
    """Validates: Requirements 1.1, 2.1, 2.2"""
    for path in steering_files():
        fm = parse_frontmatter(path)
        if fm.get("inclusion") == "always":
            assert path.name in APPROVED_ALWAYS, (
                f"{path.name} uses inclusion: always but is not in the approved set {APPROVED_ALWAYS}"
            )


# Feature: steering-optimization, Property 2: every auto file has unique kebab-case name and description
def test_auto_files_have_valid_name_and_description():
    """Validates: Requirements 1.4, 4.1, 4.2"""
    names = []
    for path in steering_files():
        fm = parse_frontmatter(path)
        if fm.get("inclusion") == "auto":
            name = fm.get("name", "")
            description = fm.get("description", "")
            assert re.match(r"^[a-z][a-z0-9-]*$", name), (
                f"{path.name}: name '{name}' does not match kebab-case pattern ^[a-z][a-z0-9-]*$"
            )
            assert len(description.strip()) > 0, (
                f"{path.name}: description is empty"
            )
            names.append(name)
    assert len(names) == len(set(names)), (
        f"auto file names are not unique: {names}"
    )


# Feature: steering-optimization, Property 3: every fileMatch file has a fileMatchPattern
def test_filematch_files_have_pattern():
    """Validates: Requirements 1.5, 3.1, 3.2"""
    for path in steering_files():
        fm = parse_frontmatter(path)
        if fm.get("inclusion") == "fileMatch":
            pattern = fm.get("fileMatchPattern")
            assert pattern is not None, (
                f"{path.name}: fileMatchPattern is missing"
            )
            assert pattern != "" and pattern != [], (
                f"{path.name}: fileMatchPattern is empty"
            )


# Feature: steering-optimization, Property 4: no section heading appears in more than one steering file
def test_no_duplicate_section_headings():
    """Validates: Requirements 5.1, 5.2, 5.3"""
    seen: dict[str, str] = {}
    for path in steering_files():
        for heading in extract_headings(path):
            assert heading not in seen, (
                f"Heading '{heading}' appears in both '{seen[heading]}' and '{path.name}'"
            )
            seen[heading] = path.name


# Feature: steering-optimization, Property 5: each steering file maps to exactly one domain
DOMAIN_MAP = {
    "product.md": "product",
    "workflow.md": "workflow",
    "python.md": "python",
    "terraform.md": "terraform",
    "frontend.md": "frontend",
    "tech.md": "tech-stack",
    "structure.md": "project-structure",
    "mcp.md": "mcp",
    "subagent-delegation.md": "subagent-delegation",
    "specs-issue-workflow.md": "specs-workflow",
    "github-mcp.md": "github-mcp",
}


def test_each_file_maps_to_one_domain():
    """Validates: Requirements 8.1, 8.2, 8.3"""
    for path in steering_files():
        assert path.name in DOMAIN_MAP, (
            f"{path.name} has no domain assignment in DOMAIN_MAP"
        )


# Feature: steering-optimization, Property 6: all steering filenames are kebab-case
def test_steering_filenames_are_kebab_case():
    """Validates: Requirements 8.5"""
    for path in steering_files():
        stem = path.stem
        assert re.match(r"^[a-z][a-z0-9-]*$", stem), (
            f"{path.name}: stem '{stem}' is not kebab-case"
        )
