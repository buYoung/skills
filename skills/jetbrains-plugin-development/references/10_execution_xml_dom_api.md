# XML DOM API

## XML DOM API — typed XML models

When your plugin works with structured XML config files (Spring beans, custom DSL configs),
the **DOM API** maps elements to typed Java/Kotlin interfaces with validation, completion,
and references for free.

### Defining a DOM

```java
@Stubbed
public interface MyConfig extends DomElement {
  @Attribute("name") @Required GenericAttributeValue<String> getName();
  @Attribute("ref")   GenericAttributeValue<MyTarget> getRef();
  List<MyEntry> getEntries();
  MyEntry addEntry();
}

public interface MyEntry extends DomElement {
  @Attribute("key") @Required GenericAttributeValue<String> getKey();
  GenericDomValue<String> getValue();
}
```

### `DomFileDescription`

```java
public class MyDomFileDescription extends DomFileDescription<MyConfig> {
  public MyDomFileDescription() { super(MyConfig.class, "config"); }
  @Override public boolean isMyFile(@NotNull XmlFile file, @Nullable Module module) {
    return /* extension or root tag heuristic */ true;
  }
}
```

```xml
<dom.fileDescription implementation="com.example.MyDomFileDescription"/>
```

### Reading

```kotlin
val dm = DomManager.getDomManager(project)
val handler = dm.getFileElement(xmlFile, MyConfig::class.java) ?: return
val config: MyConfig = handler.rootElement
config.name.value   // String?
config.entries.forEach { e -> e.key.value }
```

### Modifying (Write Action)

```kotlin
WriteCommandAction.runWriteCommandAction(project) {
  val newEntry = config.addEntry()
  newEntry.key.value = "k"
  newEntry.value.value = "v"
}
```

### Type-safe references via `Converter`

```java
public class MyTargetConverter extends ResolvingConverter<MyTarget> { /* ... */ }
```

Hook into a `GenericAttributeValue` so resolution and completion work:

```java
@Convert(MyTargetConverter.class)
GenericAttributeValue<MyTarget> getRef();
```

### Inspections

`BasicDomElementsInspection<T>` is a base class for DOM-specific inspections. Register as a
`<localInspection>` plus the DOM hookup.

### Extending DOM dynamically

`DomExtender<MyConfig>` lets you contribute extra elements/attributes based on context
(e.g., a Spring schema extension). Register with `<dom.extender>`.
