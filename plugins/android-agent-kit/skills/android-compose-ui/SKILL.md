---
name: android-compose-ui
description: "Compose UI: state, recomposition, effects, and lists."
version: 1.0.0
license: MIT
---

# Jetpack Compose UI

Covers the parts of Compose that compile fine and behave wrongly: state that does not
survive, effects that fire twice, lists that rebuild every frame. Material 3 theming and
design tokens live in `android-material3-ux`.

## When to Use

- Writing or reviewing any `@Composable`
- UI that flickers, loses state on rotation, or stutters while scrolling
- Converting XML layouts to Compose

## State: pick the right holder

```kotlin
var text by remember { mutableStateOf("") }               // survives recomposition
var text by rememberSaveable { mutableStateOf("") }       // + process death & rotation
val uiState by viewModel.state.collectAsStateWithLifecycle()  // from a ViewModel
```

| Need | Use |
|---|---|
| Transient UI state (expanded, focused) | `remember` |
| State a user would be angry to lose (form input, scroll position) | `rememberSaveable` |
| Business state, survives config change | `ViewModel` + `StateFlow` |
| Derived from other state | `remember { derivedStateOf { … } }` |

`collectAsStateWithLifecycle()` — not `collectAsState()` — is correct on Android: it
stops collecting when the app backgrounds. `collectAsState()` keeps the flow hot behind
the lock screen and drains battery.

**A `mutableStateOf` without `remember` resets on every recomposition.** It compiles,
and the symptom is a field that clears itself as the user types.

## Hoist state, keep composables stateless

```kotlin
// Reusable and testable: no internal state, caller owns everything
@Composable
fun SearchBar(query: String, onQueryChange: (String) -> Unit, modifier: Modifier = Modifier) { … }
```

Rules: state goes to the lowest common ancestor of everything reading it; a composable
takes `Modifier` as its **first optional parameter** and applies it to its outermost
element; a content composable never touches a ViewModel directly — pass state and
callbacks so previews and tests work.

## Side effects — the right one, or a bug

| Situation | Use |
|---|---|
| Run on first composition / when a key changes | `LaunchedEffect(key)` |
| Clean up when leaving composition | `DisposableEffect(key) { onDispose { … } }` |
| Call a suspend function from a callback (not composition) | `rememberCoroutineScope()` |
| Read latest value inside a long-lived effect | `rememberUpdatedState` |
| Push state out to non-Compose code | `SideEffect` |

`LaunchedEffect(Unit)` runs once per composition entry. `LaunchedEffect(someChangingValue)`
cancels and restarts every time that value changes — the usual cause of a network call
firing repeatedly. **Never call a ViewModel one-shot event from the composable body**;
it runs on every recomposition.

One-off events (navigate, snackbar) must not live in `UiState` — a config change replays
them. Use a `Channel(Channel.BUFFERED).receiveAsFlow()` consumed in a `LaunchedEffect`.

## Lists

```kotlin
LazyColumn {
    items(items = users, key = { it.id }) { user -> UserRow(user) }
}
```

`key` is not optional in practice: without it, inserting at the top re-creates every row,
losing scroll position and animation state. Never wrap `LazyColumn` in a
`verticalScroll` — it throws at runtime with an infinite-height-constraint error.

## Recomposition cost

Compose skips a composable when all parameters are **stable**. Unstable parameters
defeat skipping and cause frame drops:

- `List<T>` is unstable — use `ImmutableList` (kotlinx-collections-immutable) or `@Immutable`
- A `data class` with a `var` is unstable
- A lambda capturing an unstable value is unstable

```kotlin
@Immutable
data class UserUi(val id: String, val name: String)
```

Defer state reads to the narrowest scope. `Modifier.offset { IntOffset(x, 0) }` (lambda)
re-runs only layout; `Modifier.offset(x.dp)` (value) re-runs composition.

Diagnose before optimising — enable strong skipping and check with the compiler metrics
rather than guessing which composable is hot.

## Common runtime failures

| Symptom | Cause |
|---|---|
| Blank screen, no crash | Exception inside `remember`, or a `LaunchedEffect` that never returns |
| State resets while typing | `mutableStateOf` without `remember` |
| Network call fires repeatedly | Suspend call in the composable body, or an unstable `LaunchedEffect` key |
| Scroll jumps when data updates | Missing `key` in `items()` |
| Crash: "infinite height constraints" | `LazyColumn` inside `verticalScroll` |
| Snackbar reappears after rotation | One-off event modelled as state |

## Pitfalls

1. **Reading state too high.** A `Text` reading a rapidly changing value forces its whole
   parent to recompose; push the read down into the smallest composable.
2. **`Modifier` parameter not first or not forwarded.** Callers silently lose the ability
   to size and position your component.
3. **`collectAsState()` on Android.** Use the lifecycle-aware variant.
4. **Previews that need a ViewModel.** If it cannot be previewed, the state is not hoisted.

## Verification

- Every `mutableStateOf` wrapped in `remember` or `rememberSaveable`
- Effects keyed deliberately; no suspend calls in composable bodies
- `key` supplied for every dynamic `items()`
- Content composables preview without a ViewModel
- Compiled via `android-build-verify`
