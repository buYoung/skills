# Line Markers

Read this when a plugin adds gutter icons for navigation, run actions, implementations,
related files, or similar line-level editor affordances.

## `LineMarkerProvider` — gutter icons

```java
public class MyLineMarkerProvider extends RelatedItemLineMarkerProvider {
  @Override
  protected void collectNavigationMarkers(@NotNull PsiElement element,
                                          @NotNull Collection<? super RelatedItemLineMarkerInfo<?>> result) {
    // ALWAYS check leaf — see "must be leaf" rule below.
    if (!isInterestingLeaf(element)) return;
    // ...build a NavigationGutterIconBuilder and add to result.
  }
}
```

```xml
<codeInsight.lineMarkerProvider language="JAVA"
                                implementationClass="com.example.MyLineMarkerProvider"/>
```

### "Must be leaf" rule

Markers must be returned only on **leaf PSI elements** — tokens — not on composite nodes
like `PsiMethod`. Returning on a composite causes the marker to flicker as the user scrolls
and parts of the parent enter/leave the visible window. Find the relevant ancestor with
`PsiTreeUtil.getParentOfType` from the leaf. The platform's "fast" pass also relies on this
contract.

### Slow vs fast markers

`LineMarkerProvider.getLineMarkerInfo` runs in the *fast* daemon pass and must be cheap.
For markers that need resolution (e.g., "open recipe" icons that consult an index), use
`SlowLineMarkerProvider` or do the slow work in `collectNavigationMarkers` of
`RelatedItemLineMarkerProvider`, which the platform schedules in a slower pass.

### Make it `DumbAware` if it doesn't need indexes

Implement `DumbAware` so the marker survives Dumb Mode if the analysis is index-free.
