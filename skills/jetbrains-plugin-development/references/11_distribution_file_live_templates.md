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

On the pinned 2026.2.2 source, both registrations above are public, dynamic EPs in
[LangExtensionPoints.xml](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/platform-resources/src/META-INF/LangExtensionPoints.xml).
The word `internal` in `internalFileTemplate` names a template category; it is not an API
status annotation. Conversely, the platform's `DefaultLiveTemplateEP` bean is Kotlin
`internal`: contribute declarative XML through the supported EP, never instantiate,
subclass, cast to, or import its implementation bean. Recheck the EP contract on the
minimum supported IDE version.
