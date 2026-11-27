# File and Live Templates

## File templates and live templates

### File templates — "New File" templates

```xml
<extensions defaultExtensionNs="com.intellij">
  <internalFileTemplate name="My Template Name"/>
</extensions>
```

Template body lives in `src/main/resources/fileTemplates/internal/My Template Name.ft`
(naming is significant — it must match `name`, with `.ft` extension). Variables use Velocity
syntax (`${NAME}`, `#if(...)`).

### Live templates

```xml
<defaultLiveTemplates file="liveTemplates/myPlugin"/>
```

The XML at `src/main/resources/liveTemplates/myPlugin.xml` defines templates. Each template
specifies `name`, `value`, `description`, applicable contexts, and variables.

## Public registration boundary

On the pinned 2026.3 source, both registrations above are public, dynamic EPs in
[intellij.platform.lang.impl.xml](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-impl/resources/intellij.platform.lang.impl.xml).
The word `internal` in `internalFileTemplate` names a template category; it is not an API
status annotation. Conversely, the platform's `DefaultLiveTemplateEP` bean is Kotlin
`internal`: contribute declarative XML through the supported EP, never instantiate,
subclass, cast to, or import its implementation bean. Recheck the EP contract on the
minimum supported IDE version.
