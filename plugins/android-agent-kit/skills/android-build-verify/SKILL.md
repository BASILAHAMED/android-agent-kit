---
name: android-build-verify
description: Build, install, and prove an Android change actually runs.
version: 1.0.0
license: MIT
---

# Build and verify

Closes the loop between "code written" and "code works". A change is unverified until
Gradle exits 0, and a UI change is unverified until the app runs on a device without
crashing. This skill is the discipline plus the failure-triage playbook.

## When to Use

- Finishing any Android code change, before reporting it complete
- A Gradle build fails and the output is thousands of lines
- The app builds but crashes, hangs, or shows a blank screen
- Setting up verification in an unfamiliar project

## Use the right wrapper for the platform

| Host | Command |
|---|---|
| Windows | `./gradlew.bat` (the extensionless `gradlew` is a shell script; `cmd` cannot run it) |
| macOS / Linux | `./gradlew` |

Using the wrong one is the most common cross-platform Android agent failure. Check once:

```bash
ls gradlew gradlew.bat
```

Never invoke a system-wide `gradle` — the wrapper pins the version the project expects.

## Procedure

1. **Compile.** The narrowest task that proves the change:

   ```bash
   ./gradlew.bat assembleDebug --console=plain
   ```

   Completion: `BUILD SUCCESSFUL`. Anything else means step 2, not a progress report.

2. **Read failures from the bottom.** Gradle prints the summary last. The useful lines
   are `e: file:///...` (Kotlin), `error:` (Java/AGP), and `Execution failed for task`.

   ```bash
   ./gradlew.bat assembleDebug --console=plain 2>&1 | grep -E "^e: |error:|Execution failed for task|Caused by:" | head -30
   ```

   Completion: every distinct error has a file and line number. Fix the **first** error
   first — later ones are frequently cascade noise from it.

3. **Install on a device.**

   ```bash
   ./gradlew.bat installDebug --console=plain
   ```

   `INSTALL_FAILED_UPDATE_INCOMPATIBLE` means a different signing key is installed —
   `adb uninstall <applicationId>` first. `INSTALL_FAILED_INSUFFICIENT_STORAGE` and
   `no devices/emulators found` are environment problems, not code problems.

4. **Run it and watch.** Building proves compilation, not correctness:

   ```bash
   adb logcat -c
   adb shell am force-stop <applicationId>
   adb shell monkey -p <applicationId> -c android.intent.category.LAUNCHER 1
   sleep 4
   adb logcat -d "*:E" | grep -E "FATAL EXCEPTION|AndroidRuntime|ANR in" | head -20
   ```

   Completion: **zero** fatal lines, and the app is genuinely in the foreground:

   ```bash
   adb shell dumpsys window | grep -E "mCurrentFocus|mFocusedApp"
   ```

   A crash at startup often leaves the launcher focused — if the focused package is not
   yours, the app died regardless of what the build said.

5. **Report the evidence, not the intent.** State the task that passed and the runtime
   check result. "Should work now" without step 4 output is not a report.

## Reading a stack trace

```
FATAL EXCEPTION: main
Process: com.example.app, PID: 12345
java.lang.NullPointerException: ... 
    at com.example.app.HomeScreen.render(HomeScreen.kt:42)   <- first line in YOUR package
    at androidx.compose.runtime.…                             <- framework noise
Caused by: java.lang.IllegalStateException: …                 <- the actual root cause
```

Read the **first frame inside your own package** for the location and the **last
`Caused by:`** for the reason. The top exception type is often a wrapper.

| Symptom | Usual cause |
|---|---|
| `ClassNotFoundException: …Hilt_…` | Hilt annotation processor not running — KSP plugin missing |
| `IllegalStateException: No compose compiler` | Compose plugin not applied for Kotlin 2.x |
| `Unresolved reference` for an AndroidX symbol that exists | Dependency in the wrong module's `build.gradle` |
| Blank white screen, no crash | Composable throwing inside a `remember`, or a `LaunchedEffect` that never completes |
| `ANR in …` | Blocking I/O on `Dispatchers.Main` |

## Making failures cheaper

```bash
./gradlew.bat assembleDebug --console=plain --offline   # skip dependency resolution when iterating
./gradlew.bat :app:compileDebugKotlin --console=plain   # compile only, skip packaging
./gradlew.bat clean assembleDebug --console=plain       # only after dependency/plugin changes
```

`--stacktrace` belongs on configuration failures (a broken `build.gradle.kts`), not
compile errors, where it buries the useful lines.

## Pitfalls

1. **`clean` on every run.** It discards the build cache and turns a 20-second
   incremental build into minutes. Use it only when Gradle configuration changed.
2. **Trusting `BUILD SUCCESSFUL` for UI work.** It proves the code compiled, nothing more.
3. **Piping a full log into context.** Redirect to a file and grep it:
   `./gradlew.bat assembleDebug > build.log 2>&1` then grep — the raw log is mostly noise.
4. **`installDebug` with several devices attached.** Gradle fails; set
   `ANDROID_SERIAL=<serial>` or disconnect the others.
5. **Reading logcat without clearing first.** Old crashes from previous runs read as new ones.

## Verification

- Correct wrapper for the host OS
- `BUILD SUCCESSFUL` observed, not assumed
- For UI changes: app installed, launched, foreground confirmed, logcat clean
- Reported result cites the actual command output
