# Parameter Info and Navigation

## `ParameterInfoHandler` — `(` parameter hints

```java
public class MyParamInfo implements ParameterInfoHandler<PsiMethodCallExpression, PsiMethod> {
  @Override public PsiMethodCallExpression findElementForParameterInfo(@NotNull CreateParameterInfoContext c) {
    return findCallAtCursor(c.getFile(), c.getOffset());
  }
  @Override public void showParameterInfo(@NotNull PsiMethodCallExpression call,
                                          @NotNull CreateParameterInfoContext c) {
    PsiMethod m = call.resolveMethod();
    if (m != null) c.setItemsToShow(new Object[]{ m });
    c.showHint(call, call.getTextRange().getStartOffset(), this);
  }
  // updateUI(...) renders the hint, highlighting the active parameter
  @Override public boolean supportsOverloadSwitching() { return true; }
}
```

EP: `<codeInsight.parameterInfo language="..." implementationClass="..."/>`.

## Smaller navigation surfaces

These APIs add structure, breadcrumbs, choose-by-name lookup, and spellchecking support:

- **Use `ChooseByNameContributorEx`** (not the old `ChooseByNameContributor`); it streams
  results via `Processor` instead of returning a full array.
- **Spellchecking** plugs in a `Tokenizer<T>` per `PsiElement` type. Use
  `TEXT_TOKENIZER` for parts that should be checked, `EMPTY_TOKENIZER` to opt out.

Use `06_code_insight_surround_with.md` for selection-based `Surrounder` implementations.
