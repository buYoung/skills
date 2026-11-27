# Threading, background work, and coroutines

The single most important file in this skill. Read it whenever the task touches a thread, a read or write of platform model state (PSI, VFS, Document, project model), a background operation, an executor, a coroutine, or any pre-2024.1 code that needs to migrate to coroutines.

## The threading model in one page

Two thread categories the platform recognizes:

- **EDT** (Event Dispatch Thread). Single Swing UI thread. Anything that touches a Swing component, a popup, a tool window, or focus must run here. Blocking the EDT freezes the IDE.
- **BGT** (Background Thread). Anything that is not the EDT. Many threads exist (executor pools, coroutine dispatchers).

Three locks the platform uses:

- **Read Lock.** Held during a Read Action. Required to read PSI, VFS, Document, project model, and most platform-managed state.
- **Write Intent Lock.** Allows reads and can be upgraded atomically to the Write Lock. `Dispatchers.EDT` and `Application.invokeLater()` provide it; pure UI dispatchers do not.
- **Write Lock.** Held during a Write Action. Required to **modify** that state. Exclusive: while held, all reads block.

Combining gives the cell-table:

| Operation | Required lock | Allowed thread |
|---|---|---|
| Read PSI/VFS/Document/project model | Read Lock | Any (EDT or BGT) |
| Write same | Write Lock | Depends on the target version and chosen API; see below |

A few additional concepts:

- **Read locks are reentrant** and shared: many threads can hold one simultaneously.
- **Write locks are exclusive.** They wait for all readers to finish before proceeding.
- **2024.1-era compatibility:** writes are EDT-bound. Preserve an existing EDT write with `withContext(Dispatchers.EDT)` plus classic `WriteAction`; use `WriteCommandAction` for undoable PSI/Document changes.
- **2025.1:** `Dispatchers.Main` and raw Swing callbacks no longer imply Write Intent, and stable `edtWriteAction` makes an EDT write explicit. Use `Dispatchers.EDT` for EDT model access, or an explicit read/write action.
- **2025.3+:** `Dispatchers.UI` is the public pure-UI dispatcher. It runs on EDT without Write Intent; in 2026.3, starting a read or write action inside it is reported as an error, so keep PSI/VFS/Document access out of it.
- **2026.2+:** suspending `writeAction` delegates to `backgroundWriteAction` and acquires the Write Lock from `Dispatchers.Default`. Use `edtWriteAction` when EDT execution is part of the old behavior or the called API requires EDT. Do not infer thread affinity merely from holding the Write Lock.
- **Dumb Mode** is a separate axis (indexes are unavailable). See `05_file_model_indexing_stubs.md`.
- **`ProcessCanceledException`** (PCE) is the platform's cancellation signal. Read Actions, many platform calls (`PsiFile.getText()`, `PsiReference.resolve()`), and progress checks all may throw it. **Never catch-all and swallow it.**

## Fixed-source evidence

The 2026.2+ statements above are verified against IntelliJ Community tag `idea/2026.3`, commit `c91871ae2864649d952825cff72569e3db0e7ac6`:

- [`Application.java`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/core-api/src/com/intellij/openapi/application/Application.java)
- [`coroutines.kt`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/core-api/src/com/intellij/openapi/application/coroutines.kt)

The recommended entry points in this reference are public and are not annotated `@ApiStatus.Internal` or `@IntellijInternalApi` at that commit. Internal source is useful only for understanding behavior; never call or cast to its implementations.
