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

UAST is **read-only**. To mutate, fetch `sourcePsi` and switch to language-specific PSI:

```kotlin
val ktFunction = uMethod.sourcePsi as? KtFunction
writeCommandAction(project, "Rename") { ktFunction?.setName("newName") }
```

For UAST inspections, register with `language="UAST"` and extend `AbstractBaseUastLocalInspectionTool`:

```kotlin
class MyUastInspection : AbstractBaseUastLocalInspectionTool(UCallExpression::class.java) {
  override fun checkMethod(method: UMethod, manager: InspectionManager, isOnTheFly: Boolean) =
    arrayOf<ProblemDescriptor>()  // implement
}
```

```xml
<localInspection language="UAST"
                 implementationClass="com.example.MyUastInspection"
                 displayName="My UAST inspection" groupName="My Plugin"/>
```

For visitors, use `UastHintedVisitorAdapter.create(file, visitor, arrayOf(<types you care about>), directOnly = true)`
to skip irrelevant conversions.

Language coverage: Java and Kotlin are fully supported; Scala is beta; Groovy supports
declarations only.
