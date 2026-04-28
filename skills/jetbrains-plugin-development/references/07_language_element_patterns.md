# Element Patterns

## Element Patterns — the matcher DSL

`PlatformPatterns`, `StandardPatterns`, `PsiJavaPatterns`. Compose with `.with(...)`,
`.withSuperParent(...)`, `.withFirstChild(...)`, `.afterLeaf(...)`,
`.afterSibling(...)`, etc. Patterns are usually the cleanest way to gate completion and
reference contributors precisely.

```java
PsiElementPattern.Capture<PsiLiteralExpression> p =
  PlatformPatterns.psiElement(PsiLiteralExpression.class)
    .withParent(PsiNameValuePair.class)
    .with(new PatternCondition<>("isMineKey") {
      @Override public boolean accepts(@NotNull PsiLiteralExpression t, ProcessingContext ctx) {
        return ((String) t.getValue()).startsWith("simple:");
      }
    });
```
