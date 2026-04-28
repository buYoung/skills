# Language Injection

## Language Injection

Inject another language inside string literals (regex inside Java strings, SQL inside
Kotlin string templates, etc.). Implement `MultiHostInjector`:

```java
public class MyInjector implements MultiHostInjector {
  @Override public @NotNull List<? extends Class<? extends PsiElement>> elementsToInjectIn() {
    return Collections.singletonList(PsiLiteralExpression.class);
  }
  @Override public void getLanguagesToInject(@NotNull MultiHostRegistrar reg, @NotNull PsiElement host) {
    PsiLiteralExpression lit = (PsiLiteralExpression) host;
    if (looksLikeRegex(lit)) {
      reg.startInjecting(RegExpLanguage.INSTANCE)
         .addPlace(null, null, (PsiLanguageInjectionHost) host,
                   TextRange.from(1, lit.getTextLength() - 2))
         .doneInjecting();
    }
  }
}
```

```xml
<multiHostInjector implementation="com.example.MyInjector"/>
```

The injected fragment becomes a real PSI tree underneath, so completion and inspection of
the inner language work normally.
