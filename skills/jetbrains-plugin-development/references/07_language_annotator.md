# Annotator

## `Annotator` — semantic analysis

```java
public class MyAnnotator implements Annotator {
  @Override public void annotate(@NotNull PsiElement el, @NotNull AnnotationHolder holder) {
    if (!(el instanceof MyId)) return;
    if (((MyId) el).getReference().resolve() == null) {
      holder.newAnnotation(HighlightSeverity.ERROR, "Unresolved reference")
        .range(el.getTextRange())
        .highlightType(ProblemHighlightType.LIKE_UNKNOWN_SYMBOL)
        .withFix(new MyCreateQuickFix(el.getText()))
        .create();
    }
  }
}
```

```xml
<annotator language="MyLang" implementationClass="com.example.mylang.MyAnnotator"/>
```

`AnnotationHolder` is a builder — call `.create()` at the end or nothing happens. For
"color only, no message" annotations, use `holder.newSilentAnnotation(HighlightSeverity.INFORMATION)`.

Annotator vs Inspection (see `06_code_insight_inspections_intentions_quick_fixes.md`): default to Annotator unless
you need suppression, options, or batch participation.

Annotator rules:
- Stateless. The instance is shared across files and threads.
- Read-only. Modifications go through Quick Fixes / Intentions.
- Cheap. Filter early (`if (!(el is X)) return`).
- Cache resolution if it must repeat (`CachedValue` keyed on `PsiModificationTracker.MODIFICATION_COUNT`).
