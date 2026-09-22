<div align="center">

# Android Agent Kit

**Android & Jetpack Compose agent skills that make your AI coding tool verify its own work.**

![skills](https://img.shields.io/badge/skills-9-8b5cf6)
![license](https://img.shields.io/badge/license-MIT-2f9e6f)
![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-d97757)
![Codex](https://img.shields.io/badge/Codex-plugin-10a37f)
![Copilot CLI](https://img.shields.io/badge/Copilot_CLI-plugin-24292e)

</div>

Most Android agent skills teach an agent *what to write*. They still let it say "done"
over Kotlin that was never compiled and a screen that was never rendered. This pack adds
the half that is usually missing: **a closed loop** — build it, install it, run it, read
the screen back as text, audit it against Material 3, and only then report.

Skills load automatically from context: touching a `@Composable` pulls in
`android-compose-ui`, a Gradle failure pulls in `android-build-verify`.

## Contents

- [What makes this different](#what-makes-this-different)
- [Installation](#installation)
- [Skills](#skills)
- [The loop](#the-loop)
- [Requirements](#requirements)
- [Design principles](#design-principles)
- [Attribution](#attribution)
- [License](#license)

## What makes this different

| | Typical Android skill packs | Android Agent Kit |
|---|---|---|
| Knowledge (architecture, Compose, M3) | ✅ | ✅ |
| Says "run `./gradlew`" | ✅ | ✅ |
| **Distinguishes `gradlew` from `gradlew.bat`** | ❌ | ✅ |
| **Refuses to report done without a passing build** | ❌ | ✅ |
| **Reads the UI without a vision model** | ❌ | ✅ |
| **Executable accessibility/M3 audit rules with severities** | ❌ | ✅ |
| **Resolves dependency versions from Maven at run time** | ❌ | ✅ |

Three of the nine skills are *verification*, not knowledge. That ratio is deliberate —
it is what decides whether an agent ships working apps or plausible-looking Kotlin.

### Text-first, so it works on any model

Reading a screen via `uiautomator` returns exact labels, ids, bounds, and state.
A screenshot returns pixels a text model cannot read and a vision model must
re-interpret every turn. The accessibility tree is cheaper, deterministic, and
**works on models with no vision at all**.

```
FrameLayout desc='Video player' id=watch_player @1064,540 2128x1080
ViewGroup desc='Expand Mini Player' id=player_overlays [C] @1064,540 2128x1080
SeekBar desc='0 minutes 0 seconds of 3 minutes 49 seconds' @1122,863 2012x108
```

## Installation

### Claude Code

```
/plugin marketplace add BASILAHAMED/android-agent-kit
/plugin install android-agent-kit@android-agent-kit
```

### Codex CLI

```bash
codex plugin marketplace add BASILAHAMED/android-agent-kit
codex plugin add android-agent-kit@android-agent-kit
```

Start a new session, then confirm with `/skills`.

### Copilot CLI

```bash
copilot plugin install BASILAHAMED/android-agent-kit
```

### Any other agent

The skills are plain, self-contained markdown — no runtime, no dependencies.

```bash
git clone https://github.com/BASILAHAMED/android-agent-kit.git
cp -r android-agent-kit/plugins/android-agent-kit/skills/* ~/.hermes/skills/android/
# Cursor / Windsurf / generic:  .claude/skills/   OpenCode:  ~/.config/opencode/skill/
```

## Skills

| Skill | Use when |
|---|---|
| **android-dev** | Baseline for all Android work. House defaults, `minSdk` API gating, routing. |
| **android-build-verify** | Building, installing, triaging Gradle failures and crashes. |
| **android-device-loop** | Driving a device over adb and reading the screen as text. |
| **android-ui-audit** | Scoring a live screen for accessibility and M3 compliance. |
| **android-compose-ui** | Composable state, recomposition, effects, lists, stability. |
| **android-material3-ux** | Color roles, typography, shape, spacing, motion, adaptive layout. |
| **android-architecture** | Layers, UiState, repositories, error mapping, DI, threading. |
| **android-testing** | Unit, Compose, and instrumented tests that don't flake. |
| **android-dependencies** | Resolving and upgrading versions without guessing. |

## The loop

What "done" means in this pack:

```
 1  read minSdk               API floor decides which APIs are legal
 2  write                     Compose + architecture skills
 3  ./gradlew.bat assembleDebug      BUILD SUCCESSFUL, or fix and repeat
 4  ./gradlew.bat installDebug
 5  launch + adb logcat -d "*:E"     zero FATAL EXCEPTION, app in foreground
 6  uiautomator dump                 read the screen back as text
 7  audit                            48dp targets, labels, insets, contrast scope
 8  report                           cite the output, not the intention
```

Steps 3–7 are the reason this pack exists. An agent that stops at step 2 is guessing.

### Rules the pack enforces

- **`gradlew.bat` on Windows.** The extensionless `gradlew` is a shell script `cmd`
  cannot run — the most common cross-platform Android agent failure.
- **px → dp before judging any size.** On a 480dpi phone a compliant 48dp target is
  144px. Skipping the conversion produces confidently wrong accessibility verdicts.
- **Never state a version from memory.** Query `maven-metadata.xml`, then filter
  prereleases. Note that `com.google.dagger:hilt-android` is on Maven Central, *not*
  Google Maven — querying the wrong host returns 404 and looks like a missing artifact.
- **`BUILD SUCCESSFUL` is not a UI verification.** It proves compilation and nothing else.
- **Contrast is out of scope for tree-based audits.** The accessibility tree carries no
  colour. Say so rather than guessing.

## Requirements

| | |
|---|---|
| Android SDK | platform-tools (`adb`) + at least one platform |
| JDK | 17+ for AGP 8.x, 21+ for AGP 9.x |
| Device | Physical device or emulator with USB debugging authorized |
| Vision model | **Not required** |

Check the toolchain before starting:

```bash
adb devices -l                              # 'device' = ready; 'unauthorized' = accept the prompt
java -version                               # match to your AGP major
ls gradlew gradlew.bat                      # know which wrapper to call
```

## Design principles

1. **Verification over vocabulary.** A skill that cannot tell the agent how to prove it
   worked is documentation, not a skill.
2. **Text over pixels.** The accessibility tree is cheaper, deterministic, and
   model-agnostic.
3. **Resolve, don't recall.** Version numbers come from Maven, API gates from `minSdk`.
4. **Every rule carries its fix.** `minimumInteractiveComponentSize()`, not "make it bigger".
5. **Name the failure mode.** Each skill ends with the pitfalls that actually bite.

## Attribution

Prior art surveyed while building this. The knowledge skills stand on their shoulders;
the verification skills exist because none of them close the loop:

| Project | Contribution |
|---|---|
| [rcosteira79/android-skills](https://github.com/rcosteira79/android-skills) | Router + specialist structure; design-transcription fidelity |
| [chrisbanes/skills](https://github.com/chrisbanes/skills) | Procedure-with-completion-criteria style; Compose testing patterns |
| [hamen/material-3-skill](https://github.com/hamen/material-3-skill) | M3 token, color, and adaptive-layout guidance |
| [new-silvermoon/awesome-android-agent-skills](https://github.com/new-silvermoon/awesome-android-agent-skills) | Semantic (non-pixel) device navigation approach |
| [Meet-Miyani/compose-skill](https://github.com/Meet-Miyani/compose-skill) | KMP/CMP boundary coverage |

## License

MIT — see [LICENSE](LICENSE).
