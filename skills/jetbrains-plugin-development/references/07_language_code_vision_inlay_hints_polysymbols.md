# Code Vision, Inlay Hints, and Polysymbols

### Code Vision and Inlay Hints

Choose the extension point by the kind of hint and the minimum IDE version, as described in
the official [Inlay Hints guide](https://plugins.jetbrains.com/docs/intellij/inlay-hints.html):

| Hint | Implement | Register in |
|---|---|---|
| Parameter-name hints (plain strings before arguments) | `InlayParameterHintsProvider` | `com.intellij.codeInsight.parameterNameHints` |
| Inline hints, 2023.1+ (recommended) | declarative `com.intellij.codeInsight.hints.declarative.InlayHintsProvider` | `com.intellij.codeInsight.declarativeInlayProvider` |
| Block hints above an element, PSI-dependent | `DaemonBoundCodeVisionProvider` | `com.intellij.codeInsight.daemonBoundCodeVisionProvider` |
| Block hints above an element, PSI-independent | `CodeVisionProvider` | `com.intellij.codeInsight.codeVisionProvider` |
| Custom inline or block presentation (legacy) | `com.intellij.codeInsight.hints.InlayHintsProvider` | `com.intellij.codeInsight.inlayProvider` |

There is no `DeclarativeInlayHintsProvider` class and no `<inlayHintsProvider>` or
`<codeVision.provider>` EP; the declarative and legacy interfaces are both named
`InlayHintsProvider` and differ only by package.

Declarative provider registration:

```xml
<extensions defaultExtensionNs="com.intellij">
  <codeInsight.declarativeInlayProvider
      language="MyLang"
      implementationClass="com.example.mylang.MyInlayHintsProvider"
      isEnabledByDefault="true"
      group="TYPES_GROUP"
      providerId="mylang.types"
      bundle="messages.MyLangBundle"
      nameKey="inlay.provider.mylang.types.name"/>
</extensions>
```

`implementationClass`, `language`, `isEnabledByDefault`, `group` (an `InlayGroup` constant),
`providerId`, and `nameKey` are required by the bean; `bundle` and `descriptionKey` are
optional. The provider implements `createCollector(file, editor)` and returns `null` when the
file has nothing to show. The Settings preview text lives in
`inlayProviders/<providerId>/preview.<ext>` in plugin resources.

Code Vision registration takes only the implementation; the provider's `id`, `name`, and
`groupId` come from the class. Add a `com.intellij.config.codeVisionGroupSettingProvider`
entry whose `groupId` matches, so the group appears in Settings:

```xml
<extensions defaultExtensionNs="com.intellij">
  <codeInsight.daemonBoundCodeVisionProvider
      implementation="com.example.mylang.MyUsagesCodeVisionProvider"/>
  <config.codeVisionGroupSettingProvider
      implementation="com.example.mylang.MyUsagesCodeVisionSettingsProvider"/>
</extensions>
```

`CodeVisionProvider` is `@ApiStatus.Experimental`, and the SDK guide marks the whole Code
Vision API experimental. The legacy `codeInsight.inlayProvider` EP is listed as experimental
in the extension point list. Record the minimum IDE version and that instability before
using either; prefer the declarative provider for inline hints.

The EP names, bean attributes, and API status above were checked at IntelliJ Community
`idea/2026.3` (commit `c91871ae2864649d952825cff72569e3db0e7ac6`):
[`intellij.platform.lang.xml`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-api/resources/intellij.platform.lang.xml),
[`intellij.platform.lang.impl.xml`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-impl/resources/intellij.platform.lang.impl.xml),
[declarative `InlayHintsProviderExtensionBean`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-api/src/com/intellij/codeInsight/hints/declarative/InlayHintsProviderExtensionBean.kt),
[declarative `InlayHintsProvider`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-api/src/com/intellij/codeInsight/hints/declarative/InlayHintsProvider.kt),
[`CodeVisionProvider`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-impl/src/com/intellij/codeInsight/codeVision/CodeVisionProvider.kt),
[`DaemonBoundCodeVisionProvider`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-impl/src/com/intellij/codeInsight/hints/codeVision/DaemonBoundCodeVisionProvider.kt),
and the [extension point list](https://plugins.jetbrains.com/docs/intellij/intellij-platform-extension-point-list.html).
The declarative interface already exists on the `231` branch, matching the SDK guide's
2023.1 boundary.

### Polysymbols

A unified symbol model used across plugins (Vue, Angular, Astro, etc.). Useful when you
want to interoperate with web-style polyglot files. Verify the API against the target IDE
branch before implementation.
