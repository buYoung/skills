# Execution Diagnostics

## Common mistakes

- Long `RunProfileState.execute` running on the EDT and freezing the IDE during launch.
  Move the actual exec setup off the EDT.
- Forgetting `ProcessTerminatedListener.attach(processHandler)` so the console doesn't
  print exit code.
- Using a global `OkHttpClient` field on a service. Wrap construction in `cs.launch { }` or
  lazy init so plugin unload can release it. Better: build per-call.
- DOM file description `isMyFile` based on root tag without considering namespaces — picks
  up unrelated XML.
- `ErrorReportSubmitter` synchronously calling out to a server on the EDT. Submit in a
  background thread.
- Using `HttpRequests` in EDT contexts. Always run on background threads (`Dispatchers.IO`
  / `runBlockingCancellable`).

## Related references

- `10_execution_process_console_terminal.md` — `ConsoleView` setup.
- `06_code_insight_editor_markup_lifecycle.md` — console filters in detail.
- `02_runtime_services.md` — `ProcessAdapter` is just a listener pattern.
- `09_project_basics.md` — `ExternalSystemProjectAware`/`Tracker` integrate with the project
  model when imports change structure.
