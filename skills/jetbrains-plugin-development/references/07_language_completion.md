# Completion

## Completion — `CompletionContributor`

```java
public class MyCompletionContributor extends CompletionContributor {
  public MyCompletionContributor() {
    extend(CompletionType.BASIC,
           PlatformPatterns.psiElement(MyTypes.ID),
           new CompletionProvider<>() {
             @Override
             protected void addCompletions(@NotNull CompletionParameters params,
                                           @NotNull ProcessingContext ctx,
                                           @NotNull CompletionResultSet result) {
               for (String name : myKnownNames(params.getOriginalFile())) {
                 result.addElement(LookupElementBuilder.create(name).withIcon(MyIcons.SYMBOL));
               }
             }
           });
  }
}
```

```xml
<completion.contributor language="MyLang"
                        implementationClass="com.example.mylang.MyCompletionContributor"/>
```

`PsiElementPattern`s drive when a contributor fires. Common builders live in `StandardPatterns`, `PsiJavaPatterns`, `PlatformPatterns`. Build patterns by:

```java
PlatformPatterns.psiElement(MyTypes.ID)
  .withParent(MyProperty.class)
  .afterLeaf(PlatformPatterns.psiElement(MyTypes.EQ));
```

`CompletionType.BASIC` is the standard `Ctrl+Space`. `SMART` is type-matching completion, invoked by the `SmartTypeCompletion` action (`Ctrl+Shift+Space` in the default keymap). `CLASS_NAME` is deprecated; use `BASIC` instead.

Tweak the result set. `withPrefixMatcher` and `withRelevanceSorter` return a new `CompletionResultSet`, so chain them and keep the result; `restartCompletionOnPrefixChange` returns `void`, and `runRemainingContributors(params, passResult)` returns the collected results:

```java
CompletionResultSet adjusted = result.withPrefixMatcher(prefix)  // override prefix
                                     .withRelevanceSorter(sorter);
adjusted.restartCompletionOnPrefixChange(StandardPatterns.string().endsWith("."));
adjusted.runRemainingContributors(params, true); // run later contributors, pass results through
```

The three-argument `runRemainingContributors(params, consumer, stop)` is deprecated.
