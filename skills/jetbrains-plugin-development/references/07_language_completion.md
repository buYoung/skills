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

`PsiElementPattern`s drive when a contributor fires. Common builders live in
`StandardPatterns`, `PsiJavaPatterns`, `PlatformPatterns`. Build patterns by:

```java
PlatformPatterns.psiElement(MyTypes.ID)
  .withParent(MyProperty.class)
  .afterLeaf(PlatformPatterns.psiElement(MyTypes.EQ));
```

`CompletionType.BASIC` is the standard `Ctrl+Space`. `SMART` is the older deprecated
"smart completion" path. `CLASS_NAME` is the class-name path.

Tweak the result set:

```java
result.withPrefixMatcher(prefix)              // override prefix
      .withRelevanceSorter(...)
      .restartCompletionOnPrefixChange(...)
      .runRemainingContributors(params, true) // explicitly chain
```
