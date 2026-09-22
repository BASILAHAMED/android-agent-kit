# Contributing

## What belongs here

A skill earns its place by changing agent behavior. Before opening a PR, answer:
**what does the agent do differently because this text exists?** If the answer is
"nothing, but it's good to know", it belongs in a blog post.

## Skill standards

Every `SKILL.md` must have:

```yaml
---
name: android-thing            # lowercase, hyphens, matches the directory name
description: One line under 60 characters, ends with a period.
version: 1.0.0
license: MIT
---
```

Body sections, in this order (omit what doesn't apply):

```
# Title
2-3 sentence intro: what it covers, what it explicitly does not.
## When to Use        - triggers, plus "Don't use for:" counter-triggers
## Procedure          - numbered, each step with a checkable completion criterion
## Pitfalls           - numbered, the failures that actually happen
## Verification       - how the agent proves it worked
```

## Writing rules

1. **Every rule carries its fix.** "Touch targets must be 48dp" is half a rule.
   `Modifier.minimumInteractiveComponentSize()` is the other half.
2. **Name the symptom, not just the cause.** Agents pattern-match on what they observe:
   "state resets while typing" finds the bug faster than "missing remember".
3. **No version numbers in prose.** They rot. Teach the agent to query
   `maven-metadata.xml` instead — see `android-dependencies`.
4. **Cut anything that doesn't change behavior.** "Be careful" and "follow best
   practices" are no-ops. Replace with a checkable criterion or delete.
5. **Commands must be copy-pasteable** and correct on Windows, macOS, and Linux.
   Where they differ (`gradlew` vs `gradlew.bat`), say so explicitly.
6. **One skill, one concern.** If a skill needs two unrelated "When to Use" clusters,
   it's two skills.

## Verify before opening a PR

Claims in a skill must be tested against a real device or build, not recalled:

```bash
adb devices -l
adb exec-out uiautomator dump /dev/tty | head -20
./gradlew.bat assembleDebug --console=plain     # or ./gradlew on macOS/Linux
```

Then run the validator, which checks frontmatter, field presence, the 60-character
description budget, directory/name agreement, required sections, balanced code fences,
cross-skill references, and manifest version sync:

```bash
python validate.py
```

It exits non-zero and lists every problem. CI runs the same command.

Keep versions in sync across `.claude-plugin/marketplace.json`,
`plugins/android-agent-kit/.claude-plugin/plugin.json`, and
`plugins/android-agent-kit/.codex-plugin/plugin.json`.

## Reporting a bad rule

Open an issue with the project setup, what the skill told the agent to do, and what
actually happened. A rule that is wrong on real hardware is a bug, not a preference.
