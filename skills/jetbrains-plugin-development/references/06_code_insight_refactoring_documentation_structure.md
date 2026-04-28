# Refactoring and Structure

Read this when a custom language participates in Rename, Safe Delete, Inline, structure
view, or related language structure features. Use `06_code_insight_documentation_target_api.md` for Quick
Documentation and hover documentation.

## Refactoring support

```java
public class MyRefactoringSupport extends RefactoringSupportProvider {
  @Override public boolean isMemberInplaceRenameAvailable(@NotNull PsiElement element,
                                                          @Nullable PsiElement context) {
    return element instanceof MyDeclaration;
  }
  @Override public boolean isSafeDeleteAvailable(@NotNull PsiElement element) {
    return element instanceof MyDeclaration;
  }
}
```

```xml
<lang.refactoringSupport language="MyLang"
                         implementationClass="com.example.MyRefactoringSupport"/>
```

Preconditions:
- **Rename** depends on `PsiNamedElement.setName(...)` actually mutating PSI and on
  `PsiReference.isReferenceTo(...)` being correct so all usages are rewritten.
- **Safe Delete** depends on Find Usages being accurate so the platform can decide when a
  delete would orphan references.
- **Inline** requires a separate `InlineActionHandler`.
