# Extensions and Extension Points

## API boundary for 2026.2.2

The examples in this reference use extension contracts intended for external plugins. Verify
platform EPs against their declared interface or bean class as well as the descriptor metadata;
an XML-visible EP is not automatically public. In the fixed `idea/2026.2.2` source,
[`ProjectExtensionPointName`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/extensions/src/com/intellij/openapi/extensions/ProjectExtensionPointName.kt)
explicitly says not to introduce project- or module-scoped EPs, and
[`AbstractExtensionPointBean`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/service-container/src/com/intellij/openapi/extensions/AbstractExtensionPointBean.java)
is deprecated. Do not use either for a new plugin contract.

## Contents

- Extensions and Extension Points
  - Anatomy of an `<extensions>` block
  - Two kinds of EPs
  - Implementation rules (these explain most "registered but not working" cases)
  - Ordering with `order`
  - Iterating an EP from code
  - Defining your own EP
  - Finding the right EP


## Extensions and Extension Points

Extensions are how a plugin contributes implementations. They are declared in `<extensions>`
blocks; the platform constructs them lazily on first use.

### Anatomy of an `<extensions>` block

```xml
<extensions defaultExtensionNs="com.intellij">
  <annotator language="JAVA"
             implementationClass="com.example.MyAnnotator"
             order="first"/>

  <toolWindow id="MyToolWindow"
              anchor="right"
              factoryClass="com.example.MyToolWindowFactory"/>

  <applicationConfigurable instance="com.example.MySettingsConfigurable"
                           id="com.example.settings"
                           displayName="My Plugin"/>
</extensions>
```

`defaultExtensionNs="com.intellij"` means the tag `<annotator>` resolves to the EP id
`com.intellij.annotator`. To extend a non-platform plugin's EP, change `defaultExtensionNs`
to that plugin's id, or use the fully qualified tag name.

### Two kinds of EPs

- **Interface EP** (`<annotator implementationClass="...">`): you provide a class implementing
  the EP's interface.
- **Bean EP** (`<fileType name="..." extensions="..." language="..." fieldName="INSTANCE"
  implementationClass="...">`): you provide data plus, optionally, an implementation class.
  Attributes map to the EP's bean class via `@Attribute("...")` and `@Tag("...")`.

A common confusion: `implementationClass` (Bean EP) versus `implementation` (Interface EP).
The XML attribute name differs by EP. The IDE's XML completion and validation will steer
you correctly — pay attention to red squiggles.

### Implementation rules (these explain most "registered but not working" cases)

The platform is strict about EP implementations. Violations are silent until they hit a
specific runtime path.

1. **Stateless.** One instance per EP container is shared across all calls and threads.
   Mutating instance fields will corrupt across projects, threads, or dynamic reloads.
   Move state into a service.
2. **No work in the constructor.** No I/O, no other-service lookup, no listener registration,
   no class loading of optional dependencies. The platform uses lazy EP iteration; constructor
   work runs on whichever thread happens to first iterate the EP.
3. **No `static` initializer blocks.** Same reason as (2), and unloadable plugins cannot have
   classes referenced from static state outliving the plugin.
4. **No `object` singletons in Kotlin** — `class` only. `object` keeps a static `INSTANCE`
   that survives plugin unload.
5. **Conditional opt-out via `ExtensionNotApplicableException.create()`** (constructor throws
   this if the extension shouldn't apply in the current environment). The legacy
   `ExtensionNotApplicableException.INSTANCE` is deprecated.
6. **`PluginAware`** — implement to receive the `PluginDescriptor` after construction. Lets
   the implementation know its plugin id, classloader, and version when needed.

Plugin DevKit's "Non-default constructors for service and extension class" inspection
catches most violations automatically.

### Ordering with `order`

```xml
<annotator language="JAVA" implementationClass="com.example.A" order="first"/>
<annotator language="JAVA" implementationClass="com.example.B"
           order="after com.example.A, before com.example.C"/>
```

Supported tokens: `first`, `last`, `before <id>`, `after <id>`, comma-combined.

### Iterating an EP from code

```kotlin
val ep = ExtensionPointName.create<MyPointInterface>("com.example.myplugin.myPoint")

ep.forEachExtensionSafe { it.doSomething() }   // exception in one extension does not
                                               // abort the rest
val first = ep.findFirstSafe { it.matches(criteria) }
val typed = ep.findExtension(MySpecificImpl::class.java)
```

Define new EPs at application scope. If an extension needs a `Project` or `Module`, pass it to
the extension method instead of creating a project- or module-scoped EP.

Avoid `ep.extensions` / `ep.extensionList` plus a manual `try/catch`. The `*Safe` variants
do the right thing.

### Defining your own EP

```xml
<extensionPoints>
  <extensionPoint name="myPoint"
                  interface="com.example.MyPointInterface"
                  dynamic="true"/>
  <extensionPoint name="myDataPoint"
                  beanClass="com.example.MyBeanClass"
                  dynamic="true"/>
</extensionPoints>
```

Set `dynamic="true"` unless you have a specific reason not to. A non-dynamic EP forces every
plugin that uses it to require a restart, which transitively forces yours to as well.

For Bean EPs, write a plain `final` bean with public fields annotated `@Attribute`, `@Tag`,
and `@RequiredElement` where mandatory:

```java
public final class MyBeanClass {
  @Attribute("name") @RequiredElement public String name;
  @Attribute("className")              public String className;
  @Tag("description")                  public String description;
}
```

### Finding the right EP

- Inside `plugin.xml` itself, `Ctrl+Space` inside `<extensions>` lists every EP available
  given the current `<depends>` set. This is the authoritative live list — only EPs from
  resolved dependencies appear, so a missing EP almost always means a missing `<depends>`.
- The IDE underlines unknown EP tags and unresolved attributes in `plugin.xml` immediately;
  treat that as the first stop when an EP "doesn't seem to exist".
- For EPs you define yourself, the `<extensionPoint>` declaration in your own descriptor is
  the single source of truth — keep its `name`, `interface`/`beanClass`, and `dynamic`
  attributes consistent with how implementations register.
