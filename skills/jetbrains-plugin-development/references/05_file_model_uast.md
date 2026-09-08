# UAST

## UAST — Unified AST for JVM languages

When you want one inspection / one line marker / one analysis to cover Java, Kotlin, Groovy,
and Scala simultaneously, use **UAST** instead of language-specific PSI.

```kotlin
val uMethod = psiMethod.toUElement(UMethod::class.java)
val params  = uMethod?.uastParameters
val body    = uMethod?.uastBody
```

Key UAST types: `UElement`, `UFile`, `UClass`, `UMethod`, `UField`, `UParameter`,
`UCallExpression`, `UIfExpression`, `UBinaryExpression`.

Two PSI bridges on every `UElement`:

| Property | Meaning | Use for |
|---|---|---|
| `sourcePsi` | Real underlying language PSI | Mutation, text ranges, Annotator targets |
| `javaPsi` | Java-shaped synthetic PSI | Java-API analysis (types, resolve) |

`UElement.psi` is deprecated.

UAST is **read-only**. To mutate, fetch `sourcePsi` and switch to language-specific PSI
only when the feature truly needs a language-specific operation:

```kotlin
val sourcePsi = uMethod.sourcePsi
// Use a documented public PSI API for the specific language only after declaring
// that language plugin as a dependency; UAST itself remains read-only.
```

For UAST inspections, register with `language="UAST"` and extend the public
`AbstractBaseUastLocalInspectionTool`. Its no-argument constructor visits the standard
declaration types; pass only public `UElement` classes as hints when narrowing the visitor:

```kotlin
class MyUastInspection : AbstractBaseUastLocalInspectionTool(UMethod::class.java) {
  override fun checkMethod(method: UMethod, manager: InspectionManager, isOnTheFly: Boolean) =
    arrayOf<ProblemDescriptor>()  // implement
}
```

```xml
<localInspection language="UAST"
                 implementationClass="com.example.MyUastInspection"
                 displayName="My UAST inspection" groupName="My Plugin"/>
```

For visitors, use the public
`UastHintedVisitorAdapter.create(language, visitor, arrayOf(<types you care about>), directOnly = true)`
signature to skip irrelevant conversions. The first argument is a `Language`, not a `PsiFile`.

Language coverage: Java and Kotlin are fully supported; Scala is beta; Groovy supports
declarations only.

UAST itself and the inspection/visitor APIs above are public external APIs in the
2026.2.2 source baseline. The `UastCodeGenerationPlugin` and related UAST extension points
are marked experimental and are not recommended for external plugins; do not use them as a
mutation shortcut. Add the bundled Java plugin dependency (`com.intellij.java`) and verify
that each language plugin you intend to analyze is present in the target product. Do not
cast to UAST implementation classes or use reflection to bypass the abstraction.

Kotlin support has a separate compatibility boundary: starting with IntelliJ IDEA 2025.1,
K2 is enabled by default and the Analysis API is the supported route for Kotlin-specific
semantic analysis. Keep UAST code language-neutral where possible, and if Kotlin-specific
behavior is required, declare the Kotlin plugin dependency and verify the modes actually
available on the IDE versions you advertise. K1 was removed in 2026.2; only older branches
that still ship K1 can participate in a K1/K2 compatibility matrix. See the
[2026 Kotlin API changes](https://plugins.jetbrains.com/docs/intellij/api-changes-list-2026.html#kotlin-plugin-2026-2).
The API status statements above were checked against
the [`idea/2026.2.2` source snapshot](https://github.com/JetBrains/intellij-community/tree/1c7e601c0423e544917046c23763b15d0282e2a3)
including the protected extension constructors and public `checkMethod` callback in
[`AbstractBaseUastLocalInspectionTool`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/java/java-analysis-api/src/com/intellij/codeInspection/AbstractBaseUastLocalInspectionTool.java),
the public `create(Language, ...)` method in
[`UastHintedVisitorAdapter`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/java/java-analysis-api/src/com/intellij/uast/UastHintedVisitorAdapter.kt),
and the [official UAST guide](https://plugins.jetbrains.com/docs/intellij/uast.html).
