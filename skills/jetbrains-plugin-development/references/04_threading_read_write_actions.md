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

// Write — EDT only
WriteAction.run<Throwable> {
  document.insertString(offset, "text")
}
val r = WriteAction.compute<String, Throwable> { /* ... */ }
```

Read locks are reentrant, so nested `ReadAction.compute { ... }` calls are essentially free.

### EDT and read locks

Code running on the EDT does **not** automatically hold a read lock. Wrap reads in
`ReadAction.compute { ... }` even on the EDT, unless you know for certain you're already
inside a read context (for example, an `Annotator.annotate` call provides a read lock).

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

In 2024.1+ coroutine code, the equivalent is `readAction { … }` (suspending).

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

Hopping work to the EDT:

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

### Threading annotations (compile-time signal)

Plugin DevKit byte-code instrumentation adds runtime assertions for these:

| Annotation | Asserts |
|---|---|
| `@RequiresReadLock` | `ThreadingAssertions.assertReadAccess()` |
| `@RequiresWriteLock` | `ThreadingAssertions.assertWriteAccess()` |
| `@RequiresEdt` | `ThreadingAssertions.assertEventDispatchThread()` |
| `@RequiresBackgroundThread` | `ThreadingAssertions.assertBackgroundThread()` |
| `@RequiresReadLockAbsence` (`@Experimental`) | `assertNoReadAccess()` |
| `@RequiresBlockingContext` (`@Experimental`) | inspection-based |

Use these on every public method whose threading is not obvious. They are documentation and
runtime safety net at the same time.
