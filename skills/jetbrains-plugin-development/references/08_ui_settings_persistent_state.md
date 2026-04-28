# Persistent State

## Contents

- Persistent state
  - Modern Kotlin pattern — `SimplePersistentStateComponent` + `BaseState`
  - Immutable variant — `SerializablePersistentStateComponent` (2022.2+)
  - Java pattern — raw `PersistentStateComponent<T>`
  - `@State` and `@Storage`
  - Lifecycle of state I/O
- Secrets — `PasswordSafe`


## Persistent state

The platform's persistence mechanism is `PersistentStateComponent`. State is stored as XML
in the IDE config directory (Application services) or in `.idea/` (Project services).

### Modern Kotlin pattern — `SimplePersistentStateComponent` + `BaseState`

```kotlin
@Service
@State(
  name = "MyPluginSettings",
  storages = [Storage("my-plugin-settings.xml")],
  category = SettingsCategory.PLUGINS
)
class MyPluginSettings : SimplePersistentStateComponent<MyPluginSettings.State>(State()) {
  class State : BaseState() {
    var userId by string("default")    // String?
    var enabled by property(true)      // Boolean
    var maxRetries by property(3)      // Int
    var tags by list<String>()
    var configMap by map<String, String>()
  }

  companion object {
    fun getInstance(): MyPluginSettings =
      ApplicationManager.getApplication().getService(MyPluginSettings::class.java)
  }
}
```

Reading and writing:

```kotlin
val s = MyPluginSettings.getInstance()
s.state.userId = "new"
val enabled = s.state.enabled
```

Why `BaseState` delegates? They flip an internal `modified` flag on assignment so the
platform knows when to write to disk. Plain `var` properties skip this and silently fail to
save.

Available delegates:

| Delegate | Type |
|---|---|
| `string()` / `string("default")` | `String?` / non-null `String` |
| `property(default)` | primitives, enums |
| `list<T>()` / `set<T>()` / `map<K, V>()` | mutable collections |

### Immutable variant — `SerializablePersistentStateComponent` (2022.2+)

```kotlin
@Service
@State(name = "S", storages = [Storage("s.xml")])
class MyImmutableSettings : SerializablePersistentStateComponent<MyImmutableSettings.State>(State()) {
  data class State(
    @JvmField val userId: String = "",
    @JvmField val enabled: Boolean = true,
  )

  var userId: String
    get() = state.userId
    set(v) { updateState { it.copy(userId = v) } }
}
```

`@JvmField` is required so the platform's reflection serializer sees the fields directly.
`updateState { … }` is atomic.

### Java pattern — raw `PersistentStateComponent<T>`

```java
@Service
@State(name = "MySettings", storages = @Storage("my-settings.xml"))
public final class MySettings implements PersistentStateComponent<MySettings.State> {
  public static final class State {
    public String userId = "";
    public boolean enabled = true;
  }
  private State myState = new State();

  @Override public State getState() { return myState; }
  @Override public void loadState(@NotNull State state) { myState = state; }

  public static MySettings getInstance() {
    return ApplicationManager.getApplication().getService(MySettings.class);
  }
}
```

### `@State` and `@Storage`

`@State` attributes:

- `name` — XML root tag. Must be unique; usually FQN-style.
- `storages` — array of `@Storage`. The first is primary.
- `reloadable` — auto-reload when the file changes externally (default `true`).
- `category` — `SettingsCategory` for the Settings Sync plugin. Default `OTHER` is **not
  synced**; pick `UI`/`CODE`/`KEYMAP`/`TOOLS`/`SYSTEM`/`PLUGINS` if the value should sync
  across machines.

`@Storage` attributes:

- `value` — file name.
- `roamingType` — `DEFAULT`, `DISABLED`, `PER_OS`. Light Application services **must** use
  `DISABLED` for roaming since they are auto-registered.
- `deprecated` — for migrations from old file names.

Default file paths:

| Service level | Path |
|---|---|
| Application | `<IDE config>/options/<storage>.xml` |
| Project | `<project>/.idea/<storage>.xml` |

For per-user (non-VCS) state, store under workspace:

```kotlin
@Storage(StoragePathMacros.WORKSPACE_FILE)
```

That writes to `.idea/workspace.xml`, typically `.gitignore`d.

### Lifecycle of state I/O

1. On first `getService(...)`, the platform constructs the component and calls `loadState`
   with whatever is on disk (or nothing if first run).
2. `getState` is consulted on flush; the platform writes to disk.
3. Modifications mark the component dirty; the platform flushes on idle and IDE close.

Pre-load tasks: implement `noStateLoaded()` to handle the "no XML yet" case (e.g., copy
defaults), or `initializeComponent()` for one-time setup after load. These are part of the
`PersistentStateComponent` contract, not `Disposable`.

## Secrets — `PasswordSafe`

```kotlin
val attributes = CredentialAttributes(generateServiceName("MyPlugin", "github.com:apiToken"))
val cred = Credentials(/* user = */ null, /* password = */ token)

PasswordSafe.instance.set(attributes, cred)                       // store
val stored = PasswordSafe.instance.get(attributes)?.getPasswordAsString() // read
PasswordSafe.instance.set(attributes, null)                       // remove
```

`PasswordSafe` chooses an OS-appropriate keychain (macOS Keychain, Windows DPAPI, KWallet).
Never store credentials in `PersistentStateComponent` — the file is plaintext.
