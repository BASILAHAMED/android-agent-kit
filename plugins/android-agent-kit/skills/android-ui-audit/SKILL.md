---
name: android-ui-audit
description: Audit a live Android screen for accessibility and M3.
version: 1.0.0
license: MIT
---

# UI/UX audit

Score a screen against Material 3 and Android accessibility requirements using the
accessibility tree. Deterministic and vision-free: the same screen scores the same every
run, and each finding names the fix.

## When to Use

- Reviewing a screen before shipping it
- An accessibility complaint or Play Store pre-launch report finding
- Confirming a redesign did not regress usability

**Don't use for:** colour contrast of rendered pixels and visual polish — the tree has
no colour data. Read theme values from source, or capture a screenshot for visual review.

## Procedure

1. Put the target screen in the foreground and let animations settle.
2. Capture the tree and the device metrics:

   ```bash
   adb shell wm size && adb shell wm density
   adb exec-out uiautomator dump /dev/tty
   ```

3. Convert every measurement to dp before judging it: `dp = px / (density / 160)`.
4. Walk the rules below in order. Completion: every interactive node has been checked
   against touch-target and label rules — not a sample.
5. Report findings with severity, the element's label, and the concrete fix.

## Rules

### Touch targets — error below 48dp

Every `clickable`, `checkable`, or `long-clickable` node must be at least **48×48dp**
(WCAG 2.5.5, M3 minimum). Measure `bounds`, convert to dp.

Exempt: `scrollable` containers, and nodes whose class is a container
(`ScrollView`, `RecyclerView`, `ComposeView`, `WebView`).

```kotlin
// Compose: the visual size stays small, the touch area grows
IconButton(onClick = …, modifier = Modifier.minimumInteractiveComponentSize())
// or explicitly
Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp)
```

A 24dp icon with no expanded touch area is the single most common real violation.

### Labels — error when missing

Any interactive node with no `text` **and** no `content-desc` is invisible to
TalkBack, Voice Access, and Switch Access.

```kotlin
Icon(Icons.Default.Close, contentDescription = "Close dialog")
Icon(Icons.Default.Star, contentDescription = null)   // correct ONLY if decorative
```

`contentDescription = null` is a deliberate statement that the element is decorative and
adjacent text conveys the meaning. On a functional control it is a bug.

### System insets — warning

Interactive elements within ~24dp of the bottom edge collide with gesture navigation;
elements at the very top sit under the status bar.

```kotlin
Modifier.navigationBarsPadding()
Modifier.statusBarsPadding()
// or let Scaffold consume WindowInsets.safeDrawing
```

Edge-to-edge is the default from API 35 — content that ignores insets is clipped or
untappable on modern devices.

### Overlapping hit rects — warning

Two sibling interactive nodes whose `bounds` intersect by more than ~25% of the smaller
one make taps ambiguous. Nesting (child inside parent) is normal and not a finding.

### Text size — warning below 12sp

Body text below 12sp fails legibility guidance. Prefer a typography role over a literal:
`MaterialTheme.typography.bodySmall` is 12sp; `labelSmall` is 11sp and is for labels, not prose.

### Duplicate labels — info

Several interactive elements sharing one label ("Edit", "Edit", "Edit") leave voice
control unable to disambiguate. Qualify them: "Edit name", "Edit email".

### Physical-direction naming — info

A `resource-id` or modifier using `left`/`right` rather than `start`/`end` will not
mirror in RTL locales. Use `paddingStart`/`paddingEnd` and `Arrangement.Start`.

## Scoring

Start at 100 and subtract: **error −8**, **warning −3**, **info −1**. Below 70 the screen
needs work before shipping; a single unlabelled control or sub-48dp target is enough to
justify blocking regardless of the total.

## Report format

```
[ERROR] touch-target  'Close'        36×22dp, below the 48dp minimum
        fix: Modifier.minimumInteractiveComponentSize()
[WARN ] edge          'Submit'       sits inside the bottom gesture inset
        fix: Modifier.navigationBarsPadding()
```

## Pitfalls

1. **Judging px as dp.** On a 480dpi phone a compliant 48dp button is 144px. Not
   converting produces false errors on every element.
2. **Flagging nested overlap.** A clickable row containing a clickable icon is correct.
3. **Auditing mid-animation.** Bounds are in flight; wait for the screen to settle.
4. **Claiming contrast compliance from the tree.** It carries no colour. Say so rather
   than guessing.
5. **Auditing one screen and declaring the app accessible.** Dialogs, empty states, and
   error states are where violations concentrate.

## Verification

- Device density read and every bound converted to dp
- Every interactive node checked, not a sample
- Each finding carries severity, element label, and an actionable fix
- Contrast explicitly marked as out of scope unless checked from theme source
