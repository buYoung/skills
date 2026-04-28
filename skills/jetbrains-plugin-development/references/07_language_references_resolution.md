# References and Resolution

## References — `PsiReference` + `PsiReferenceContributor`

References are the link between identifier text and definition. They power Go to
Declaration, Find Usages, Rename.

A reference for an identifier element:

```java
public class MyReference extends PsiReferenceBase<MyId> {
  public MyReference(@NotNull MyId element, @NotNull TextRange range) { super(element, range); }
  @Override public @Nullable PsiElement resolve() {
    return MyResolver.findDeclaration(getElement().getProject(), getElement().getText());
  }
  @Override public Object @NotNull [] getVariants() {
    return MyResolver.allDeclarations(getElement().getProject()).toArray();
  }
}
```

Contribute references via `PsiReferenceContributor` for elements you don't own (e.g.,
injecting references into Java string literals matching `simple:foo`):

```java
public class MyReferenceContributor extends PsiReferenceContributor {
  @Override public void registerReferenceProviders(@NotNull PsiReferenceRegistrar reg) {
    reg.registerReferenceProvider(
      PlatformPatterns.psiElement(PsiLiteralExpression.class),
      new PsiReferenceProvider() {
        @Override public PsiReference @NotNull [] getReferencesByElement(@NotNull PsiElement el,
                                                                          @NotNull ProcessingContext ctx) {
          PsiLiteralExpression lit = (PsiLiteralExpression) el;
          Object v = lit.getValue();
          if (!(v instanceof String s) || !s.startsWith("simple:")) return PsiReference.EMPTY_ARRAY;
          TextRange range = new TextRange("simple:".length() + 1, s.length() + 1);
          return new PsiReference[] { new MyReference(lit, range) };
        }
      }
    );
  }
}
```

```xml
<psi.referenceContributor language="JAVA"
                          implementation="com.example.mylang.MyReferenceContributor"/>
```

For your **own** language, the BNF mixin commonly returns references via `getReferences`
on the PSI element itself.

### Multi-resolve

If a reference can resolve to several elements (overloads, multiple definitions), implement
`PsiPolyVariantReferenceBase` and override `multiResolve`. Annotator and Find Usages handle
both forms.

### Search support

For complete search scope, `<elementDescriptionProvider>`, `<usageType>` , and a
`FindUsagesProvider` may be needed. The simplest path:

```xml
<lang.findUsagesProvider language="MyLang"
                         implementationClass="com.example.mylang.MyFindUsagesProvider"/>
```

`FindUsagesProvider` defines what counts as a word, a search target, and a usage type.
