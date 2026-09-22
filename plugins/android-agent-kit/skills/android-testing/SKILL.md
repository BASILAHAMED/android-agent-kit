---
name: android-testing
description: Write Android unit, Compose, and instrumented tests.
version: 1.0.0
license: MIT
---

# Android testing

Which test to write, where it runs, and how to keep it from flaking.

## When to Use

- Adding tests for a ViewModel, repository, or screen
- A test passes locally and fails on CI, or fails intermittently
- Deciding between a unit test and an instrumented test

## Pick the cheapest test that proves the behaviour

| Target | Location | Runs on | Speed |
|---|---|---|---|
| ViewModel, repository, pure Kotlin | `src/test/` | JVM | milliseconds |
| Composable UI | `src/androidTest/` | Device/emulator | seconds |
| Room DAO, navigation, permissions | `src/androidTest/` | Device/emulator | seconds |
| Robolectric (Android APIs on JVM) | `src/test/` | JVM | fast, some fidelity loss |

```bash
./gradlew.bat testDebugUnitTest          # JVM, no device needed
./gradlew.bat connectedDebugAndroidTest  # requires an attached device
```

Most logic belongs in JVM tests. An instrumented test for something that could be a unit
test costs a device and roughly a thousand times the runtime.

## Coroutines and Flow

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class ProfileViewModelTest {
    private val dispatcher = StandardTestDispatcher()

    @Before fun setUp() = Dispatchers.setMain(dispatcher)
    @After  fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `load emits success`() = runTest {
        val vm = ProfileViewModel(FakeUserRepository())
        vm.load("1")
        advanceUntilIdle()
        assertEquals("Ada", vm.state.value.user?.name)
    }
}
```

`Dispatchers.setMain` is mandatory — `viewModelScope` uses `Dispatchers.Main`, which does
not exist on the JVM, and its absence throws before any assertion runs.

`StandardTestDispatcher` queues work until you advance it, so you can assert intermediate
states (loading). `UnconfinedTestDispatcher` runs eagerly — convenient, but it hides
ordering bugs. Prefer `StandardTestDispatcher` with `advanceUntilIdle()`.

Collecting a `StateFlow` that never completes hangs the test. Use Turbine, or read
`.value` after advancing.

## Compose UI tests

```kotlin
@get:Rule val rule = createComposeRule()

@Test
fun submitDisabledUntilValid() {
    rule.setContent { LoginScreen(state = LoginUiState(), onSubmit = {}) }

    rule.onNodeWithText("Submit").assertIsNotEnabled()
    rule.onNodeWithText("Email").performTextInput("a@b.com")
    rule.onNodeWithText("Submit").assertIsEnabled()
}
```

Test the **stateless** composable with state passed in and callbacks captured — that is
why `android-architecture` hoists state. `createComposeRule()` needs no Activity;
`createAndroidComposeRule<T>()` is only for testing real Activity behaviour.

Find nodes by semantics, never by position:

```kotlin
rule.onNodeWithText("Save")
rule.onNodeWithContentDescription("Close dialog")
rule.onNodeWithTag("user_list")            // Modifier.testTag("user_list")
```

If a node cannot be found by text or content description, that is usually an
accessibility defect, not a test problem — see `android-ui-audit`.

## Synchronisation, not sleeping

Compose tests auto-sync with the composition. `Thread.sleep` is the main source of
flakiness. When something genuinely needs waiting:

```kotlin
rule.waitUntil(timeoutMillis = 5_000) {
    rule.onAllNodesWithText("Loaded").fetchSemanticsNodes().isNotEmpty()
}
```

Infinite animations block auto-sync forever — the test times out with no useful message.
Disable them under test or use `rule.mainClock.autoAdvance = false`.

## Fakes over mocks

```kotlin
class FakeUserRepository(private val users: Map<String, User> = emptyMap()) : UserRepository {
    override suspend fun user(id: String): Result<User> =
        users[id]?.let { Result.Success(it) } ?: Result.Failure(DomainError.Unknown("missing"))
}
```

A hand-written fake is readable, refactor-safe, and does not break when a signature
changes in a way mocks silently tolerate. Reserve mocking frameworks for verifying
interactions you genuinely cannot observe through state.

## Naming and structure

```kotlin
@Test fun `load sets error state when network fails`() { … }
```

Arrange, act, assert — one behaviour per test. A test name that does not say what breaks
when it fails is a test nobody will maintain.

## Pitfalls

1. **Missing `Dispatchers.setMain`.** Every ViewModel test fails with a main-dispatcher error.
2. **`runBlocking` instead of `runTest`.** Loses virtual time; delays become real waits.
3. **Instrumented tests for pure logic.** Slow, needs hardware, no extra confidence.
4. **Asserting on a ViewModel's internal `MutableStateFlow`.** Test the public `StateFlow`.
5. **`Thread.sleep` in Compose tests.** Flaky by construction.
6. **Shared mutable state between tests.** Order-dependent passes; recreate fakes in `@Before`.

## Verification

- Tests run at the cheapest level that proves the behaviour
- `Dispatchers.setMain` set and reset for every ViewModel test
- Compose nodes found by semantics, not position
- No `Thread.sleep`
- Suite passes twice in a row (a single pass does not disprove flakiness)
