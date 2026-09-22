---
name: android-dependencies
description: Resolve Android dependency versions without guessing.
version: 1.0.0
license: MIT
---

# Dependencies and versions

Model training data goes stale; Maven metadata does not. Never state a version number
from memory — resolve it, then pin it.

## When to Use

- Adding a dependency or starting a project
- Upgrading AGP, Kotlin, or Compose
- A build fails with a version or compatibility error
- Auditing whether a project's pins are current

## Resolve the real latest version

Every Maven artifact publishes machine-readable metadata. Fetch it:

```bash
# Google Maven (AndroidX, AGP, Compose, Room, Hilt runtime artifacts)
curl -s https://dl.google.com/dl/android/maven2/androidx/compose/compose-bom/maven-metadata.xml | grep -o '<version>[^<]*' | tail -5

# Maven Central (Kotlin, KSP, Retrofit, OkHttp, Ktor, Coil, Hilt Gradle plugin)
curl -s https://repo1.maven.org/maven2/org/jetbrains/kotlin/kotlin-gradle-plugin/maven-metadata.xml | grep -o '<version>[^<]*' | tail -5
```

The coordinate maps directly to the path: `androidx.compose:compose-bom` →
`androidx/compose/compose-bom`. **Which repository matters** — `com.google.dagger:hilt-android`
is on Maven Central, not Google Maven; querying the wrong host returns 404 and looks like
the artifact does not exist.

Filter prereleases yourself: the last `<version>` entry is frequently an `alpha`, `beta`,
`rc`, or `-RC` build. Take the newest entry with none of those markers unless the user
asked for bleeding edge.

## Compatibility is a chain, not a list

These must agree; upgrading one alone breaks the build:

| Pair | Constraint |
|---|---|
| Kotlin ↔ KSP | KSP version is `<kotlin>-<ksp>`, e.g. `2.1.0-1.0.29`. A mismatch fails at configuration. |
| Kotlin ↔ Compose compiler | From Kotlin 2.0, apply `org.jetbrains.kotlin.plugin.compose`; the version tracks Kotlin. |
| AGP ↔ Gradle | Each AGP has a minimum Gradle version. |
| AGP ↔ JDK | AGP 8.x needs JDK 17+; AGP 9.x needs JDK 21+. |
| compileSdk ↔ AndroidX | Recent AndroidX releases require a recent `compileSdk`; the error is "dependency requires compileSdk 35 or later". |

Upgrade in order — **JDK → Gradle → AGP → Kotlin → KSP → libraries** — verifying a build
at each step. Bumping everything at once produces errors that cannot be attributed.

## Use the BOM for Compose

```kotlin
implementation(platform("androidx.compose:compose-bom:<version>"))
implementation("androidx.compose.ui:ui")               // no version
implementation("androidx.compose.material3:material3") // no version
```

The BOM resolves a mutually-tested set. Pinning an individual Compose artifact's version
alongside the BOM overrides it and reintroduces the incompatibility it prevents.

## Version catalogs

Modern projects centralise versions in `gradle/libs.versions.toml`:

```toml
[versions]
kotlin = "2.1.0"
composeBom = "2025.01.00"

[libraries]
compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "composeBom" }

[plugins]
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
```

```kotlin
implementation(platform(libs.compose.bom))
```

Dots in the TOML alias become dots in the accessor (`compose-bom` → `libs.compose.bom`).
In a catalog project, a hardcoded coordinate in a module is an inconsistency — always
check whether `gradle/libs.versions.toml` exists before adding a dependency.

## Diagnosing version failures

```bash
./gradlew.bat app:dependencies --configuration debugRuntimeClasspath   # full tree
./gradlew.bat app:dependencyInsight --dependency okhttp --configuration debugRuntimeClasspath
```

| Error | Cause |
|---|---|
| `Duplicate class … found in modules` | Two libraries bundling the same classes — exclude one transitively |
| `requires compileSdk 35 or later` | Library newer than the project's compileSdk |
| `ksp … is too new for kotlin …` | KSP/Kotlin pair mismatch |
| `Unsupported class file major version` | JDK too new or too old for this AGP |
| `Could not find …` | Wrong repository, or artifact renamed between major versions |

## Pitfalls

1. **Stating a version from memory.** Confidently wrong numbers waste a whole build cycle.
2. **Taking the last metadata entry blindly.** It is usually a prerelease.
3. **Assuming Google Maven hosts everything AndroidX-adjacent.** Hilt's Gradle plugin,
   Kotlin, KSP, Retrofit, OkHttp, and Coil are on Maven Central.
4. **Pinning Compose artifacts next to the BOM.** Defeats the BOM.
5. **Upgrading AGP without checking the JDK.** Fails with an opaque class-file error.
6. **Adding a duplicate dependency already provided transitively.** Check the tree first.

## Verification

- Every version resolved from Maven metadata during this task, not recalled
- Prereleases filtered unless explicitly requested
- Kotlin/KSP and AGP/Gradle/JDK pairs checked against each other
- Catalog used if `gradle/libs.versions.toml` exists
- Build passes via `android-build-verify` after the change
