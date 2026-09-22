---
name: android-dev
description: Baseline for all Android and Kotlin development work.
version: 1.0.0
license: MIT
---

# Android development baseline

Load this for **any** Android or Kotlin work: the house defaults below apply without
re-derivation, and the routing table points at the focused skill for the task.

## When to Use

- Any mention of Android, Kotlin, Jetpack, Compose, Gradle, AndroidManifest, ViewModel,
  Activity, Fragment, adb, logcat, APK, Play Store, KMP, or an `applicationId`
- Any work inside a directory containing `settings.gradle[.kts]` and an `app/` module
- Casual triggers: "fix this crash", "add a screen", "why is my build failing"

**Don't use for:** Flutter, React Native, or Compose Multiplatform targeting desktop/web
only — those have different toolchains and this skill's defaults will mislead.

## The rule that matters most

**Never report Android work as done without a build that passed.** Kotlin that reads
correctly and compiles are different claims. Every change ends with a real
`assembleDebug` at minimum, and UI changes end with the app running on a device.
See `android-build-verify` — that skill exists because this is the dominant failure mode.

## House defaults

Apply these unless the project already does something else, in which case match the project.

| Concern | Default |
|---|---|
| Language | Kotlin. New Java files only when extending existing Java. |
| UI | Compose. XML Views only in codebases that are already XML. |
| Async | Coroutines + Flow. No `LiveData`, no RxJava in new code. |
| DI | Hilt + KSP. Koin when the project already uses it. |
| JSON | `kotlinx.serialization`. |
| Network | Retrofit + OkHttp (Android), Ktor (KMP shared). |
| Local | Room; DataStore for preferences. Never `SharedPreferences` in new code. |
| Images | Coil 3. |
| Annotation processing | KSP. `kapt` is legacy — migrating off it is usually the single biggest build-speed win. |

## Routing

| Task | Load |
|---|---|
| Composable state, recomposition, modifiers, side effects, lists | `android-compose-ui` |
| Colors, type, shape, spacing, adaptive layout, motion, M3 tokens | `android-material3-ux` |
| Layers, UiState modelling, repositories, DI wiring, error types | `android-architecture` |
| Building, installing, Gradle failures, crash triage | `android-build-verify` |
| Driving a device/emulator, reading the screen, reproducing a bug | `android-device-loop` |
| Reviewing a live screen for accessibility and M3 compliance | `android-ui-audit` |
| Unit, Compose, and instrumented tests | `android-testing` |
| Choosing or upgrading dependency versions | `android-dependencies` |

## Establish the API floor before writing code

`minSdk` silently decides which APIs are legal. Read it first — never assume a modern floor:

```bash
grep -rn "minSdk" app/build.gradle.kts app/build.gradle
```

| Feature | Requires |
|---|---|
| Dynamic color (Material You) | API 31 |
| Per-app language preferences | API 33 |
| Notification runtime permission | API 33 — **must be requested**, silently dropped below |
| Predictive back | API 33 opt-in, default 34 |
| System-controlled contrast levels | API 34 |

Below API 31, `dynamicLightColorScheme()` does not exist — a theme that calls it
unguarded fails to compile against a lower `compileSdk` and misleads reviewers into
thinking dynamic color works. Gate it:

```kotlin
val scheme = when {
    Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
        if (dark) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
    dark -> DarkColorScheme
    else -> LightColorScheme
}
```

## Orient before editing an unfamiliar project

```bash
# module layout and applicationId
grep -rn "applicationId\|namespace\|compileSdk\|targetSdk" app/build.gradle.kts app/build.gradle
# is this Compose or Views?
grep -rn "buildFeatures" -A3 app/build.gradle.kts app/build.gradle
# version catalog present?
ls gradle/libs.versions.toml
```

Compose is active only when `buildFeatures { compose = true }` is set **and** the
Compose compiler plugin is applied. From Kotlin 2.0 the plugin is
`org.jetbrains.kotlin.plugin.compose` — the old `composeOptions.kotlinCompilerExtensionVersion`
block is obsolete and its presence alongside Kotlin 2.x is a misconfiguration worth fixing.

## Pitfalls

1. **Assuming a fresh toolchain.** An `compileSdk 34` / AGP 8.5 project cannot use
   Compose BOM releases that require compileSdk 35+. Check before recommending upgrades.
2. **Writing `LiveData` because a tutorial did.** `StateFlow` + `collectAsStateWithLifecycle()`
   is the current pattern; mixing both in one project creates two sources of truth.
3. **Editing `build.gradle` when the project uses `build.gradle.kts`.** Both can exist in
   different modules; always confirm the extension of the file you are about to change.
4. **Adding a dependency without checking `gradle/libs.versions.toml`.** In a catalog
   project, a hardcoded coordinate is an inconsistency reviewers reject.

## Verification

- `minSdk` read and any gated API guarded
- Project confirmed Compose or Views before UI code was written
- Change compiled via `android-build-verify`, not assumed
