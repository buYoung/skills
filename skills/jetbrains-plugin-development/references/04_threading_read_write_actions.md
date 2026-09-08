# Read and Write Actions

## Classic Read / Write Action API

Pre-coroutine API. Still ubiquitous in legacy code; use suspending equivalents in new code.

```kotlin
// Read
val file = ReadAction.compute<PsiFile?, Throwable> {
  PsiManager.getInstance(project).findFile(virtualFile)
}
ReadAction.run<Throwable> {
  // void
}

// Write — preserve legacy EDT behavior by calling from EDT
WriteAction.run<Throwable> {
  document.insertString(offset, "text")
}
val r = WriteAction.compute<String, Throwable> { /* ... */ }
```

These blocking read entry points are deprecated for 2026.1+ because a background caller can
delay writes. For new Kotlin code use cancellable `readAction { ... }`; for Java use
`ReadAction.nonBlocking().submit(...)` or `.executeSynchronously()`. Keep
`ReadAction.computeBlocking` only as a last resort under modal progress.

### EDT and read locks

Do not use "runs on EDT" as proof of model access. The implicit Write Intent scope changed
across releases: since 2025.1 raw Swing callbacks and `Dispatchers.Main` do not provide it,
while `Application.invokeLater()` and `Dispatchers.EDT` do. Prefer an explicit read action
unless the extension-point contract already supplies read access (for example,
`Annotator.annotate`).

### Long reads — `ReadAction.nonBlocking`

A long read on the EDT freezes the IDE; a long read on a BGT blocks every Write that
arrives. The cooperative pattern:

```kotlin
ReadAction.nonBlocking<Result> { computeResult() }
  .inSmartMode(project)                  // wait until indexes are ready
  .expireWith(parentDisposable)
  .finishOnUiThread(ModalityState.defaultModalityState()) { result -> useOnEdt(result) }
  .submit(AppExecutorUtil.getAppExecutorService())
```

If a Write arrives while the read is in progress, the platform throws PCE inside the read,
runs the Write, and re-runs the read. Your block must therefore be **idempotent** — no
side effects that aren't safe to repeat.

In 2024.1+ coroutine code, the preferred equivalent is `readAction { … }` (suspending and
cancellable). The action may restart after a pending write, so keep it idempotent.

### Write Command Action — for modifying Document/PSI

```kotlin
WriteCommandAction.runWriteCommandAction(project, "My Edit", null /* groupId */, {
  document.replaceString(start, end, "new text")
})
```

`WriteCommandAction` = Write Action + `CommandProcessor`. Use it for any change that should
participate in undo, including all PSI and Document edits. See `05_file_model_psi_basics.md` for
the Document/PSI rules around modifications.

### `invokeLater` and `ModalityState`

Hopping model work to the EDT with Write Intent:

```kotlin
ApplicationManager.getApplication().invokeLater({
  WriteAction.run<Throwable> { /* ... */ }
}, ModalityState.defaultModalityState())
```

`ModalityState`:

- `defaultModalityState()` — the modality at the time of submission.
- `nonModal()` — only when no modal dialog is up.
- `any()` — whatever, even mid-modal.
- A specific dialog's `ModalityState` — to schedule onto that dialog's modality.

Picking the wrong modality state is a common cause of "my code runs in the wrong order
when a dialog is open."

For pure Swing work on 2025.3+, prefer `withContext(Dispatchers.UI)`. It runs on EDT without
Write Intent and forbids starting read/write actions. Use `Dispatchers.EDT` when legacy model
access on EDT is intentional.

### Threading annotations (compile-time signal)

Plugin DevKit byte-code instrumentation adds runtime assertions for these:

| Annotation | Asserts |
|---|---|
| `@RequiresReadLock` | `ThreadingAssertions.assertReadAccess()` |
| `@RequiresWriteLock` | `ThreadingAssertions.assertWriteAccess()` |
| `@RequiresEdt` | `ThreadingAssertions.assertEventDispatchThread()` |
| `@RequiresBackgroundThread` | `ThreadingAssertions.assertBackgroundThread()` |
| `@RequiresReadLockAbsence` (`@Experimental`) | `assertNoReadAccess()` |
| `@RequiresBlockingContext` (`@Experimental`) | inspection/runtime contract |

Use these on every public method whose threading is not obvious. They are documentation and
runtime safety net at the same time.

Both experimental annotations above are external public API in 2026.2.2, but their stability
is not guaranteed. Confirm them in every supported IDE version and prefer stable annotations
when they express the same contract. Evidence:

- [`RequiresReadLockAbsence.java`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/util/concurrency/annotations/RequiresReadLockAbsence.java)
- [`RequiresBlockingContext.kt`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/core-api/src/com/intellij/util/concurrency/annotations/RequiresBlockingContext.kt)
