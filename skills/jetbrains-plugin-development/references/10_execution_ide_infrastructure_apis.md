# IDE Infrastructure APIs

## IDE infrastructure APIs

Common platform helpers that do not belong to a narrower API area.

### Error reporting — `ErrorReportSubmitter`

When a plugin throws, the IDE shows a "Report to Author" dialog. Override the destination
by implementing `ErrorReportSubmitter` and declaring it in `plugin.xml`:

```xml
<errorHandler implementation="com.example.MyErrorReportSubmitter"/>
```

```kotlin
class MyErrorReportSubmitter : ErrorReportSubmitter() {
  override fun getReportActionText(): String = "Report to MyPlugin"
  override fun submit(events: Array<IdeaLoggingEvent>, additionalInfo: String?,
                      parentComponent: Component, consumer: Consumer<in SubmittedReportInfo>): Boolean {
    // collect events, send to your tracker
    consumer.consume(SubmittedReportInfo(SubmissionStatus.NEW_ISSUE))
    return true
  }
}
```

### `AppLifecycleListener`

Topic for IDE lifecycle events (`appStarted`, `appWillBeClosed`). Use a declarative listener
to react.

### `RunOnceUtil`

```kotlin
RunOnceUtil.runOnceForApp("my-key", Runnable { /* runs at most once on this user's IDE */ })
RunOnceUtil.runOnceForProject(project, "my-key", Runnable { /* once per project */ })
```

Useful for one-time migrations or onboarding messages.
The suspending top-level `runOnceForProject` overload is `@ApiStatus.Internal` in
`idea/2026.3`; use the public `RunOnceUtil` methods shown above. The source is fixed at
[`RunOnceUtil.kt`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/ide-core/src/com/intellij/ide/util/RunOnceUtil.kt).

### `ApplicationInfo` / `SystemInfo` / `PathManager`

```kotlin
ApplicationInfo.getInstance().fullVersion       // "2024.1.4"
ApplicationInfo.getInstance().build             // BuildNumber("241.…")

SystemInfo.isMac
SystemInfo.isWindows
SystemInfo.OS_VERSION

PathManager.getConfigPath()      // user IDE config directory
PathManager.getPluginsPath()     // user-installed plugins
PathManager.getSystemPath()      // caches
PathManager.getLogPath()         // idea.log directory
```

### `BrowserLauncher`

```kotlin
BrowserLauncher.instance.browse(URI("https://example.com"))
BrowserLauncher.instance.open("https://example.com/page")
```

### `HttpConnectionUtils`, `HttpRequests`

Use the platform's HTTP helpers when you need a simple HTTP call without bringing your own
client:

```kotlin
HttpRequests.request("https://example.com/api").readString(/* progress = */ null)
```

For anything beyond trivial, use `Dispatchers.IO` plus a full client — the platform's API is
convenient but not full-featured. From 2026.3 the IDE no longer bundles OkHttp, so a plugin
that loads `okhttp3` classes must ship the library itself or it fails with
`NoClassDefFoundError`. The 2026.3 notes suggest `java.net.http.HttpClient` instead;
`com.intellij.util.net.PlatformHttpClient` returns a JDK client that follows the IDE proxy,
certificate, and user agent settings, but it is `@ApiStatus.Experimental` at the 2026.3
baseline, so record that risk or build the JDK client yourself.

### `PowerSaveMode`

Reflects the IDE's power-save preference. Honor it to suppress non-essential background
work:

```kotlin
if (!PowerSaveMode.isEnabled()) cs.launch { /* heavy work */ }
```

### `WebHelpProvider`

Map `helpId`s used by `Configurable` and other UI to documentation URLs:

```kotlin
class MyHelpProvider : WebHelpProvider() {
  override fun getHelpPageUrl(helpTopicId: String): String? =
    if (helpTopicId.startsWith("com.example.")) "https://docs.example.com/${helpTopicId}" else null
}
```

```xml
<webHelpProvider implementation="com.example.MyHelpProvider"/>
```
