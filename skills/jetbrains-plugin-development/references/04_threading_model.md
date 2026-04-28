# Threading, background work, and coroutines

The single most important file in this skill. Read it whenever the task touches a thread, a
read or write of platform model state (PSI, VFS, Document, project model), a background
operation, an executor, a coroutine, or any pre-2024.1 code that needs to migrate to
coroutines.

## The threading model in one page

Two thread categories the platform recognizes:

- **EDT** (Event Dispatch Thread). Single Swing UI thread. Anything that touches a Swing
  component, a popup, a tool window, or focus must run here. Blocking the EDT freezes the IDE.
- **BGT** (Background Thread). Anything that is not the EDT. Many threads exist (executor
  pools, coroutine dispatchers).

Two locks the platform uses:

- **Read Lock.** Held during a Read Action. Required to read PSI, VFS, Document, project
  model, and most platform-managed state.
- **Write Lock.** Held during a Write Action. Required to **modify** that state. Exclusive:
  while held, all reads block. **Must be acquired on the EDT** (or via the suspending
  `writeAction`/`backgroundWriteAction`/`writeCommandAction`).

Combining gives the cell-table:

| Operation | Required lock | Allowed thread |
|---|---|---|
| Read PSI/VFS/Document/project model | Read Lock | Any (EDT or BGT) |
| Write same | Write Lock | EDT-bound (or coroutine helpers below) |

A few additional concepts:

- **Read locks are reentrant** and shared: many threads can hold one simultaneously.
- **Write locks are exclusive.** They wait for all readers to finish before proceeding.
- **Write Intent Lock** (2023.3+) is auto-held on the EDT. You rarely manage it directly,
  but it's the reason an EDT thread can begin a Write Action.
- **Dumb Mode** is a separate axis (indexes are unavailable). See `05_file_model_psi_basics.md`.
- **`ProcessCanceledException`** (PCE) is the platform's cancellation signal. Read Actions,
  many platform calls (`PsiFile.getText()`, `PsiReference.resolve()`), and progress checks
  all may throw it. **Never catch-all and swallow it.**
