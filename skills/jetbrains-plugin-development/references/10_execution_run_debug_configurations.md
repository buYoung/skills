# Run and Debug Configurations

## Contents

- Run / Debug configurations
  - `ConfigurationType` and `ConfigurationFactory`
  - `RunConfiguration` skeleton
  - `RunProfileState` and `ProcessHandler`
  - `Executor` / `ProgramRunner`
  - `RunLineMarkerContributor` — gutter run icons
  - `BeforeRunTaskProvider` — pre-run steps
  - `ExecutionListener` — observe run lifecycle


Read this when you are integrating with run/debug, controlling external processes, building
a custom Run/Debug configuration, integrating an external build system (Gradle/Maven-style),
defining a typed XML configuration model, or hooking into IDE infrastructure (error
reporting, lifecycle, environment).

## Run / Debug configurations

### `ConfigurationType` and `ConfigurationFactory`

```java
public class MyConfigurationType implements ConfigurationType {
  public static final String ID = "com.example.myRunner";
  @Override public @NotNull String getId()                    { return ID; }
  @Override public @NotNull String getDisplayName()           { return "My Runner"; }
  @Override public String getConfigurationTypeDescription()   { return "Runs MyLang programs"; }
  @Override public Icon getIcon()                             { return MyIcons.Run; }
  @Override public ConfigurationFactory[] getConfigurationFactories() {
    return new ConfigurationFactory[] { new MyConfigurationFactory(this) };
  }
}

public class MyConfigurationFactory extends ConfigurationFactory {
  public MyConfigurationFactory(ConfigurationType type) { super(type); }
  @Override public @NotNull RunConfiguration createTemplateConfiguration(@NotNull Project project) {
    return new MyRunConfiguration(project, this, "My Run");
  }
  @Override public @NotNull String getId() { return MyConfigurationType.ID + ".factory"; }
}
```

### `RunConfiguration` skeleton

```java
public class MyRunConfiguration extends RunConfigurationBase<MyRunOptions> {
  public MyRunConfiguration(Project p, ConfigurationFactory f, String name) { super(p, f, name); }
  @Override public @NotNull MyRunOptions getOptions() { return (MyRunOptions) super.getOptions(); }
  @Override public @NotNull SettingsEditor<? extends RunConfiguration> getConfigurationEditor() {
    return new MyRunSettingsEditor();
  }
  @Override public @Nullable RunProfileState getState(@NotNull Executor executor,
                                                       @NotNull ExecutionEnvironment env) {
    return new MyRunProfileState(env, getOptions());
  }
}
```

`RunConfigurationBase<TOptions extends RunConfigurationOptions>` gives you property
delegates for typed options:

```kotlin
class MyRunOptions : RunConfigurationOptions() {
  var script by string("")
  var args   by list<String>()
}
```

Register:

```xml
<configurationType implementation="com.example.MyConfigurationType"/>
```

### `RunProfileState` and `ProcessHandler`

```java
public class MyRunProfileState implements RunProfileState {
  private final ExecutionEnvironment env;
  private final MyRunOptions opts;
  public MyRunProfileState(ExecutionEnvironment env, MyRunOptions opts) { this.env = env; this.opts = opts; }

  @Override public @Nullable ExecutionResult execute(@NotNull Executor executor, @NotNull ProgramRunner<?> runner)
      throws ExecutionException {
    GeneralCommandLine cmd = new GeneralCommandLine("python", opts.getScript()).withParameters(opts.getArgs());
    ProcessHandler ph = new KillableColoredProcessHandler(cmd);
    ProcessTerminatedListener.attach(ph);
    ConsoleView console = TextConsoleBuilderFactory.getInstance().createBuilder(env.getProject()).getConsole();
    console.attachToProcess(ph);
    return new DefaultExecutionResult(console, ph);
  }
}
```

`ProcessHandler` choices:

| Class | When |
|---|---|
| `OSProcessHandler` | Plain process; collects stdout/stderr. |
| `KillableColoredProcessHandler` | Process supports kill + ANSI-colored output. |
| `BaseProcessHandler` | Custom transports (gRPC, sockets). |
| `ColoredProcessHandler` | ANSI passthrough only. |

Listening:

```kotlin
processHandler.addProcessListener(object : ProcessAdapter() {
  override fun onTextAvailable(event: ProcessEvent, outputType: Key<*>) { /* ... */ }
  override fun processTerminated(event: ProcessEvent) { /* exit code event.exitCode */ }
})
```

### `Executor` / `ProgramRunner`

`Executor` describes "what kind of run" (`Run`, `Debug`, `Coverage`, …). Built-ins:
`DefaultRunExecutor.getRunExecutorInstance()`, `DefaultDebugExecutor.getDebugExecutorInstance()`.

`ProgramRunner` orchestrates the lifecycle (setup → execute → cleanup). For a vanilla
run/debug, the platform's default runners cover most cases. Implement a custom runner only
when you need to interpose (e.g., for remote execution).

### `RunLineMarkerContributor` — gutter run icons

```kotlin
class MyRunMarker : RunLineMarkerContributor() {
  override fun getInfo(element: PsiElement): Info? {
    if (element !is MyMainFunction) return null
    val actions = ExecutorAction.getActions(0)
    return Info(AllIcons.RunConfigurations.TestState.Run, actions, { "Run ${element.name}" })
  }
}
```

```xml
<runLineMarkerContributor language="MyLang"
                          implementationClass="com.example.MyRunMarker"/>
```

### `BeforeRunTaskProvider` — pre-run steps

Add a step that runs before every Run/Debug of a compatible configuration (build, generate
sources, etc.).

```xml
<stepsBeforeRunProvider implementation="com.example.MyBeforeRun"/>
```

### `ExecutionListener` — observe run lifecycle

Application-level message bus topic for execution events. Subscribe via declarative listener
or `MessageBusConnection`.
