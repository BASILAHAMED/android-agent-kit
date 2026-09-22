---
name: android-architecture
description: "Structure Android apps: layers, UiState, repositories, DI."
version: 1.0.0
license: MIT
---

# Android architecture

How an app is layered, how state reaches the UI, and where errors are handled. Composable
mechanics live in `android-compose-ui`.

## When to Use

- Starting an app, feature, or module
- Adding a screen that loads or saves data
- Untangling logic that has accumulated in an Activity or composable
- Reviewing structure or module boundaries

## Layers

```
UI (Compose)  →  ViewModel  →  Repository  →  DataSource (remote / local)
```

Rules that keep this honest:

- Dependencies point **inward only**. A repository never imports a ViewModel.
- The **domain/model layer has zero Android imports** — no `Context`, no `Uri`, no `Log`.
  This is what makes it unit-testable and KMP-portable.
- The repository is the single source of truth for its data and owns the caching decision.
- `:feature:*` modules never depend on each other; shared code moves to `:core:*`.

## One immutable UiState per screen

```kotlin
data class ProfileUiState(
    val isLoading: Boolean = false,
    val user: UserUi? = null,
    val errorMessage: String? = null,
)

class ProfileViewModel(private val repo: UserRepository) : ViewModel() {
    private val _state = MutableStateFlow(ProfileUiState())
    val state: StateFlow<ProfileUiState> = _state.asStateFlow()

    private val _events = Channel<ProfileEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    fun load(id: String) {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, errorMessage = null) }
            when (val result = repo.user(id)) {
                is Result.Success -> _state.update { it.copy(isLoading = false, user = result.data.toUi()) }
                is Result.Failure -> _state.update { it.copy(isLoading = false, errorMessage = result.error.message()) }
            }
        }
    }
}
```

Two separate streams, deliberately:

- **State** is what the screen looks like. It is replayed on every config change.
- **Events** are fire-once imperatives — navigate, snackbar, share sheet. Putting these
  in state makes them replay on rotation, which is how a snackbar reappears forever.

Expose `StateFlow`, never `MutableStateFlow`. The UI must not be able to write state.

## Errors: map at the repository boundary

Platform exceptions must not leak past the repository. Map them to a domain type so the
ViewModel never touches `IOException` or `HttpException`.

```kotlin
sealed interface Result<out T> {
    data class Success<T>(val data: T) : Result<T>
    data class Failure(val error: DomainError) : Result<Nothing>
}

sealed interface DomainError {
    data object Network : DomainError
    data object Unauthorized : DomainError
    data class Unknown(val cause: String) : DomainError
}
```

`UiState` models loading, success, **and** error explicitly. A screen with no error
branch will show a blank page the first time the network fails.

## Dependency injection

Hilt is the default; Koin when the project already uses it. The point is that a ViewModel
receives its dependencies rather than constructing them — a ViewModel that news up a
Retrofit instance cannot be tested.

```kotlin
@HiltViewModel
class ProfileViewModel @Inject constructor(private val repo: UserRepository) : ViewModel()
```

Bind interfaces, not implementations, so tests can substitute a fake. Hilt requires KSP;
if generated `Hilt_*` classes are missing at runtime, the processor is not wired up.

## Threading

`viewModelScope` is main-dispatched. The **repository** owns its dispatcher — callers
should never need `withContext(Dispatchers.IO)` at the call site:

```kotlin
class UserRepositoryImpl(
    private val api: UserApi,
    private val io: CoroutineDispatcher = Dispatchers.IO,
) : UserRepository {
    override suspend fun user(id: String): Result<User> = withContext(io) { … }
}
```

Injecting the dispatcher lets tests swap in a test dispatcher. Room and Retrofit `suspend`
functions are already main-safe — wrapping them again is harmless noise, but blocking I/O
on the main thread is an ANR.

## Structure by feature, not by type

```
feature/profile/  ProfileScreen.kt  ProfileViewModel.kt  ProfileUiState.kt
core/data/        UserRepository.kt
core/model/       User.kt          <- no Android imports
```

Not `ui/`, `viewmodels/`, `models/` — type-based packages force every change to touch
four directories and make modularisation impossible later.

## Pitfalls

1. **Business logic in a composable or Activity.** Untestable; lost on config change.
2. **Exposing `MutableStateFlow`.** The UI can corrupt state from anywhere.
3. **Events in state.** Replays on rotation.
4. **`Context` in a ViewModel.** Leaks the Activity. Use `@ApplicationContext` or move
   the dependency behind a repository.
5. **Repository returning `Response<T>` or throwing HTTP exceptions.** Retrofit types
   leaking upward means the transport is now the domain model.
6. **One giant `AppViewModel`.** Scope one ViewModel per screen.

## Verification

- `core/model` compiles with no Android imports
- UiState covers loading, success, and error
- ViewModel exposes read-only `StateFlow`; one-off events on a separate channel
- Dependencies injected, dispatchers injectable
- Compiled via `android-build-verify`
