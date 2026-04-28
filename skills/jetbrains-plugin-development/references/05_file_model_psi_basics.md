# PSI Basics

## Contents

- PSI — `PsiElement` and friends
  - Getting PSI from anywhere
  - Walking and querying
  - Modifying PSI
  - Whitespace and formatting


## PSI — `PsiElement` and friends

PSI is the parsed structure of a file in a known language. Each language plugin defines its
own PSI hierarchy:

- Java: `PsiJavaFile`, `PsiClass`, `PsiMethod`, `PsiStatement`, …
- Kotlin: `KtFile`, `KtClass`, `KtFunction`, …
- XML: `XmlFile`, `XmlTag`, `XmlAttribute`, …
- Custom languages: defined by the plugin's `ParserDefinition` (see `07_language_pipeline.md`).

### Getting PSI from anywhere

```kotlin
// VirtualFile → PsiFile (Read Action)
val psiFile = PsiManager.getInstance(project).findFile(virtualFile)

// Document → PsiFile
val psiFile = PsiDocumentManager.getInstance(project).getPsiFile(document)

// PsiFile → VirtualFile / Document
val vf = psiFile.virtualFile
val doc = PsiDocumentManager.getInstance(project).getDocument(psiFile)

// At an offset
val element: PsiElement? = psiFile.findElementAt(offset)
```

All PSI access requires a Read Action.

### Walking and querying

```kotlin
element.parent
element.children
element.firstChild / element.lastChild
element.nextSibling / element.prevSibling
element.containingFile
element.project
element.text                      // backing text — expensive; prefer textMatches
element.textRange
element.textOffset
element.isValid

// Recursive visitor
element.accept(object : PsiRecursiveElementVisitor() {
  override fun visitElement(e: PsiElement) {
    // ...
    super.visitElement(e)
  }
})

// Type-targeted lookups via PsiTreeUtil
val method   = PsiTreeUtil.getParentOfType(element, PsiMethod::class.java)
val calls    = PsiTreeUtil.findChildrenOfType(element, PsiMethodCallExpression::class.java)
val firstLit = PsiTreeUtil.findChildOfType(element, PsiLiteralExpression::class.java)
```

Performance pitfalls:

- `element.text` allocates and copies; use `element.textMatches(literal)` /
  `element.textContains(c)` for comparisons.
- Repeatedly calling `element.containingFile` / `element.project` walks parents each time —
  hoist them into a local.
- For tight visitors, use the language-specific recursive visitor (`JavaRecursiveElementWalkingVisitor`,
  `KtTreeVisitorVoid`, etc.) which prunes irrelevant nodes.

### Modifying PSI

PSI mutation requires `WriteCommandAction`:

```kotlin
WriteCommandAction.runWriteCommandAction(project, "Rename", null, {
  (element as PsiNamedElement).setName("newName")
})
// Or:
writeCommandAction(project, "Rename") { (element as PsiNamedElement).setName("newName") }
```

Creating new elements goes through a factory (language-specific) or `PsiFileFactory`:

```java
// Java
PsiElementFactory factory = JavaPsiFacade.getElementFactory(project);
PsiMethod method = factory.createMethodFromText("public void foo() {}", null);
existingClass.add(method);
```

```kotlin
// Language-neutral
val tempFile = PsiFileFactory.getInstance(project)
  .createFileFromText("temp.java", JavaLanguage.INSTANCE, "class A { void foo() {} }")
val newMethod = (tempFile.firstChild as PsiClass).methods[0]

writeCommandAction(project, "Add Method") { targetClass.add(newMethod) }
```

Mutation operations:

| Op | Effect |
|---|---|
| `element.add(child)` | append child (returns the actually inserted node, possibly a copy) |
| `element.addBefore(child, anchor)` | insert before anchor |
| `element.addAfter(child, anchor)` | insert after anchor |
| `element.delete()` | remove |
| `element.replace(new)` | replace with new |

The returned node from `add`/`replace` is the **real** node now in the tree — always do
follow-up operations on the returned reference, not the one you passed in.

### Whitespace and formatting

Do not insert whitespace nodes manually; format afterwards:

```kotlin
CodeStyleManager.getInstance(project).reformat(element)
```

For Java, also shorten references after inserting fully qualified names:

```java
JavaCodeStyleManager.getInstance(project).shortenClassReferences(element);
```
