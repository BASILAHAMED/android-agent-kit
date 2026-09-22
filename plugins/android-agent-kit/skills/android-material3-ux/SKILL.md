---
name: android-material3-ux
description: Apply Material 3 tokens, color, type, and adaptive layout.
version: 1.0.0
license: MIT
---

# Material 3 design and UX

Design-level decisions: colour roles, typography, shape, spacing, motion, and adaptive
layout. Compose mechanics live in `android-compose-ui`; auditing a built screen lives in
`android-ui-audit`.

## When to Use

- Theming an app or building a design system
- Implementing a Figma design in Compose
- Choosing navigation for phones, tablets, and foldables
- Deciding a colour, elevation, corner radius, or motion duration

## Never hardcode what a token defines

```kotlin
// wrong: invisible in dark theme, ignores dynamic color
Text("Hi", color = Color(0xFF1A1A1A))
Surface(color = Color.White) { … }

// right
Text("Hi", color = MaterialTheme.colorScheme.onSurface)
Surface(color = MaterialTheme.colorScheme.surface) { … }
```

A literal colour is a dark-theme bug that ships looking fine.

### Colour roles

| Role | Use for | Text on it |
|---|---|---|
| `primary` | Main CTA, active states | `onPrimary` |
| `primaryContainer` | Emphasised container, chips | `onPrimaryContainer` |
| `secondary` / `tertiary` | Supporting accents | `onSecondary` / `onTertiary` |
| `surface` | Sheets, cards, app background | `onSurface` |
| `surfaceContainerLow…Highest` | Elevation tiers **(M3 uses tone, not shadow)** | `onSurface` |
| `surfaceVariant` | Subtle differentiation | `onSurfaceVariant` |
| `error` / `errorContainer` | Destructive, validation | `onError` / `onErrorContainer` |
| `outline` / `outlineVariant` | Borders, dividers | — |

Every `X` has a matching `onX` guaranteeing contrast. Pairing `primary` with a
hand-picked text colour breaks that guarantee.

**Depth in M3 comes from tonal surface colour, not shadow.** A raised card is
`surfaceContainerHigh`, not `Modifier.shadow(8.dp)`.

### Dynamic colour needs an API guard

```kotlin
val colorScheme = when {
    Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
        if (darkTheme) dynamicDarkColorScheme(ctx) else dynamicLightColorScheme(ctx)
    darkTheme -> DarkColorScheme
    else -> LightColorScheme
}
```

API 31+ only. Always define static fallback schemes — they are what most users see if
`minSdk` is below 31.

## Typography: role, not size

`displayLarge…Small`, `headlineLarge…Small`, `titleLarge…Small`, `bodyLarge…Small`,
`labelLarge…Small`. Use `MaterialTheme.typography.bodyMedium`, never `fontSize = 14.sp`.
Body text is `bodyLarge` (16sp) or `bodyMedium` (14sp); `bodySmall` (12sp) is the floor.
Roboto is the correct M3 default — generic "avoid Roboto" advice does not apply here.

## Spacing and shape

Spacing is an **8dp grid** (4dp for tight pairs): 4, 8, 12, 16, 24, 32, 48. 16dp is the
standard screen margin.

Shape scale: `extraSmall` 4dp, `small` 8dp, `medium` 12dp, `large` 16dp,
`extraLarge` 28dp. Use `MaterialTheme.shapes.medium`, not `RoundedCornerShape(12.dp)`.

## Adaptive layout — required, not optional

Phones, foldables, tablets, and desktop windows all run the same APK. Branch on window
size class, never on a hardcoded device check:

| Width class | Range | Navigation |
|---|---|---|
| Compact | < 600dp | Bottom navigation bar |
| Medium | 600–839dp | Navigation rail |
| Expanded | ≥ 840dp | Permanent drawer + list-detail |

```kotlin
val widthClass = calculateWindowSizeClass(activity).widthSizeClass
when (widthClass) {
    WindowWidthSizeClass.Compact -> BottomBarScaffold()
    else -> RailScaffold()
}
```

Foldables add postures beyond size: detect a `FoldingFeature` via `WindowInfoTracker`
and **never place interactive content across the hinge**. Half-opened horizontal
(tabletop) = content top, controls bottom. Half-opened vertical (book) = list left,
detail right.

## Motion

| Duration | Range | Use |
|---|---|---|
| `short1–4` | 50–200ms | Ripples, selection, switches |
| `medium1–4` | 250–400ms | Screen transitions, expansion |
| `long1–4` | 450–600ms | Container transforms |

Pair short with `FastOutSlowIn`, medium/long with the emphasized easings. Animations must
be interruptible and must never block input. Respect reduced-motion: read
`Settings.Global.ANIMATOR_DURATION_SCALE`; at `0f` skip animation rather than shortening it.

## Implementing a design faithfully

Transcription, not adaptation. Every difference from the design is a defect, including
improvements.

- Copy is character-exact: `GET STARTED` is not `Get started`; keep the em dash and the
  trailing period; keep `Step 01 of 03` padded.
- Match a colour by **value**, then sanity-check the role name — never the reverse.
- A token the theme genuinely lacks gets **added**, never substituted with the nearest
  existing one. Substituting silently redraws the design and hides the gap.

## Pitfalls

1. **Hardcoded colours and sizes.** Breaks dark theme, dynamic colour, and font scaling.
2. **`Modifier.shadow` for depth.** Use a `surfaceContainer*` tone.
3. **Assuming a phone.** A fixed-width layout is unusable on a tablet or unfolded device.
4. **Custom `onX` colours.** Loses the contrast guarantee.
5. **Testing at one font scale.** Users run up to 200%; `Text` with a fixed `height` clips.

## Verification

- No colour, corner radius, or text size literals in UI code
- Dynamic colour guarded by an API check with static fallbacks
- Layout branches on window size class
- Checked at 200% font scale and in dark theme
- Audited with `android-ui-audit`
