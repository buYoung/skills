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
