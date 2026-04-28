# Inspections, Intentions, and Quick Fixes

## Contents

- `LocalInspectionTool` — inspections
  - Annotator vs Inspection
- `IntentionAction` — Alt+Enter improvements
- Quick fixes (`LocalQuickFix`) — attached to inspection problems


## `LocalInspectionTool` — inspections

```java
public class MyInspection extends LocalInspectionTool {
  @Override public @NotNull PsiElementVisitor buildVisitor(@NotNull ProblemsHolder holder,
                                                           boolean isOnTheFly) {
    return new JavaElementVisitor() {
      @Override public void visitLiteralExpression(@NotNull PsiLiteralExpression expr) {
        if (looksWrong(expr)) {
          holder.registerProblem(expr, "Looks wrong",
            ProblemHighlightType.LIKE_UNKNOWN_SYMBOL,
            new MyQuickFix());
        }
      }
    };
  }
}
```

```xml
<localInspection language="JAVA"
                 shortName="LooksWrong"
                 displayName="Looks wrong literal"
                 groupPath="My Plugin"
                 groupName="General"
                 enabledByDefault="true"
                 level="WARNING"
                 implementationClass="com.example.MyInspection"/>
```

Key attributes:
- `shortName` — used by `@SuppressWarnings("LooksWrong")` and persisted profile keys. Must
  be stable.
- `level` — `WARNING`, `WEAK WARNING`, `ERROR`, `INFO`, etc.
- `groupPath`/`groupName` — placement in `Settings | Editor | Inspections`.

For UAST inspections, use `AbstractBaseUastLocalInspectionTool` and `language="UAST"` (see
`05_file_model_uast.md`).

Per-inspection user options:

```kotlin
override fun getOptionsPane(): OptPane = pane(
  checkbox("ignoreGenerated", "Ignore generated code")
)
```

### Annotator vs Inspection

| Aspect | `Annotator` | `LocalInspectionTool` |
|---|---|---|
| Suppression (`@SuppressWarnings`) | Limited | Fully supported |
| Settings UI | None | Yes |
| `Inspect Code` batch run | Excluded | Included |
| Frequency | Every edit | Incremental + batch |

Default to `Annotator` for live errors; switch to `Inspection` when you need suppression,
options, or batch participation.

## `IntentionAction` — Alt+Enter improvements

```kotlin
class MyIntention : IntentionAction {
  override fun getText(): String = "Convert to lambda"
  override fun getFamilyName(): String = "My Plugin"
  override fun isAvailable(p: Project, e: Editor?, f: PsiFile?): Boolean = /* cheap */ true
  override fun invoke(p: Project, e: Editor?, f: PsiFile?) { /* mutate PSI */ }
  override fun startInWriteAction(): Boolean = true
}
```

```xml
<intentionAction>
  <language>JAVA</language>
  <className>com.example.MyIntention</className>
  <category>My Plugin</category>
</intentionAction>
```

`isAvailable` is called for every visible intention every Alt+Enter — make it cheap.
If the implementation needs a modal dialog before mutating, return `startInWriteAction = false`
and wrap mutations yourself in `WriteCommandAction`. Otherwise the platform opens the write
action for you.

## Quick fixes (`LocalQuickFix`) — attached to inspection problems

```java
class MyQuickFix implements LocalQuickFix {
  @Override public @NotNull String getName()       { return "Replace with foo"; }
  @Override public @NotNull String getFamilyName() { return getName(); }

  @Override public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor d) {
    // already inside a Write Action
    PsiElement target = d.getPsiElement();
    target.replace(/* … */);
  }
}
```

Pass it to `holder.registerProblem(element, message, fix1, fix2, ...)`. The fix runs inside
a write action by default; for slow analysis prep, do it before applying or use
`IntentionAction` with `startInWriteAction = false`.
