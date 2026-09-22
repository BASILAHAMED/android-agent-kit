#!/usr/bin/env python3
"""Validate every SKILL.md in this repo. Run from the repo root: python validate.py

Checks frontmatter parses, required fields exist, the description fits the budget
every agent host truncates at, directory names match, cross-references resolve, and
plugin manifest versions agree.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("pyyaml required: pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent
SKILLS = ROOT / "plugins/android-agent-kit/skills"
REQUIRED_FIELDS = ("name", "description", "version", "license")
REQUIRED_SECTIONS = ("## When to Use", "## Pitfalls", "## Verification")
MAX_DESC = 60

problems: list[str] = []
names: set[str] = set()
rows: list[tuple] = []


def fail(msg: str) -> None:
    problems.append(msg)


for path in sorted(SKILLS.rglob("SKILL.md")):
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        fail(f"{rel}: frontmatter must start at byte 0")
        continue
    try:
        end = text.index("\n---\n", 3)
    except ValueError:
        fail(f"{rel}: frontmatter never closes")
        continue

    try:
        fm = yaml.safe_load(text[3:end])
    except yaml.YAMLError as e:
        # An unquoted colon in the description is the usual cause.
        fail(f"{rel}: frontmatter is not valid YAML ({e.__class__.__name__}) -- "
             f"quote any description containing a colon")
        continue

    body = text[end + 5:]
    name = fm.get("name", "")
    desc = fm.get("description", "")
    names.add(name)

    for field in REQUIRED_FIELDS:
        if field not in fm:
            fail(f"{rel}: missing required field '{field}'")
    if name != path.parent.name:
        fail(f"{rel}: name '{name}' does not match directory '{path.parent.name}'")
    if len(desc) > MAX_DESC:
        fail(f"{rel}: description is {len(desc)} chars, max {MAX_DESC}")
    if desc and not desc.endswith("."):
        fail(f"{rel}: description must end with a period")
    for section in REQUIRED_SECTIONS:
        if section not in body:
            fail(f"{rel}: missing section '{section}'")
    if text.count("```") % 2:
        fail(f"{rel}: unbalanced code fence")

    rows.append((name, len(desc), len(text), text.count("```") // 2))

# Cross-references must resolve to a skill that exists.
for path in sorted(SKILLS.rglob("SKILL.md")):
    text = path.read_text(encoding="utf-8")
    for ref in sorted(set(re.findall(r"`(android-[a-z0-9-]+)`", text))):
        if ref not in names:
            fail(f"{path.relative_to(ROOT)}: reference to unknown skill '{ref}'")

# Manifest versions must agree or installs ship mismatched metadata.
manifests = {
    ".claude-plugin/marketplace.json": ("metadata", "version"),
    "plugins/android-agent-kit/.claude-plugin/plugin.json": ("version",),
    "plugins/android-agent-kit/.codex-plugin/plugin.json": ("version",),
}
versions: dict[str, str] = {}
for rel, keys in manifests.items():
    p = ROOT / rel
    if not p.exists():
        fail(f"{rel}: missing manifest")
        continue
    node = json.loads(p.read_text(encoding="utf-8"))
    for k in keys:
        node = node[k]
    versions[rel] = node
if len(set(versions.values())) > 1:
    fail(f"plugin versions disagree: {versions}")

print(f"{'skill':26} {'desc':>5} {'chars':>7} {'blocks':>7}")
for name, dlen, clen, blocks in rows:
    print(f"{name:26} {dlen:>5} {clen:>7} {blocks:>7}")
print(f"\n{len(rows)} skills, version {next(iter(versions.values()), '?')}")

if problems:
    print(f"\n{len(problems)} PROBLEM(S):")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)
print("All skills valid.")
