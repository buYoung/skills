# Language and File Type

## `Language` singleton and `FileType`

Every language has a single `Language` instance:

```java
public final class MyLanguage extends Language {
  public static final MyLanguage INSTANCE = new MyLanguage();
  private MyLanguage() { super("MyLang"); }     // "MyLang" is the case-sensitive Language ID
}
```

A `LanguageFileType` ties file names/extensions to the language:

```java
public final class MyFileType extends LanguageFileType {
  public static final MyFileType INSTANCE = new MyFileType();
  private MyFileType() { super(MyLanguage.INSTANCE); }
  @Override public @NotNull String getName()             { return "MyLang File"; }
  @Override public @NotNull String getDescription()      { return "MyLang language file"; }
  @Override public @NotNull String getDefaultExtension() { return "mylang"; }
  @Override public Icon getIcon()                        { return MyIcons.FILE; }
}
```

Register both:

```xml
<extensions defaultExtensionNs="com.intellij">
  <fileType name="MyLang File"
            implementationClass="com.example.mylang.MyFileType"
            fieldName="INSTANCE"
            language="MyLang"
            extensions="mylang"/>
</extensions>
```

`fieldName="INSTANCE"` is mandatory — the platform reads the static `INSTANCE`, never
`new`s your file type. `extensions=` accepts a comma-separated list. `language=` must
exactly match `MyLanguage.getID()` (case-sensitive).
