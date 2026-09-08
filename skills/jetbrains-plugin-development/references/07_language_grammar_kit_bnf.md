# Grammar-Kit BNF

## Parser via Grammar-Kit BNF

Grammar-Kit generates the parser, the element/token type holders, and PSI interfaces from
a BNF file. Hand-rolled parsers are possible but only worth the effort for unusual grammars.
For the IntelliJ Platform Gradle Plugin 2.18.1 setup in this skill, apply
`org.jetbrains.intellij.platform.grammarkit` in the `plugins` block (see
`01_core_gradle_project.md`); it supplies the `generateParser` and `generateLexer` tasks.
Do not treat generator dependencies as runtime plugin dependencies or also apply the
standalone `org.jetbrains.grammarkit` plugin in this setup. When maintaining an older 2.x
build, check its supported generator integration before migrating from the standalone plugin.

`MyLang.bnf` (excerpt):

```
{
  parserClass="com.example.mylang.parser.MyParser"
  parserUtilClass="com.example.mylang.parser.MyParserUtil"
  extends="com.intellij.extapi.psi.ASTWrapperPsiElement"

  psiClassPrefix="My"
  psiImplClassSuffix="Impl"
  psiPackage="com.example.mylang.psi"
  psiImplPackage="com.example.mylang.psi.impl"

  elementTypeHolderClass="com.example.mylang.psi.MyTypes"
  elementTypeClass="com.example.mylang.psi.MyElementType"
  tokenTypeClass="com.example.mylang.psi.MyTokenType"

  tokens = [
    ID      = 'regexp:[A-Za-z_][A-Za-z_0-9]*'
    EQ      = '='
    COMMENT = 'regexp:#.*'
  ]
}

myFile ::= item_*

private item_ ::= property | COMMENT | CRLF

property ::= ID EQ ID? {
  mixin="com.example.mylang.psi.impl.MyNamedElementImpl"
  implements="com.example.mylang.psi.MyNamedElement"
  methods=[ getName setName getNameIdentifier ]
}
```

What's generated:

- `MyParser.java` — the parser body, driving `PsiBuilder`.
- `MyTypes.java` — every token/element type as a constant + `Factory.createElement(ASTNode)`.
- `psi/My*.java` interfaces and `psi/impl/My*Impl.java` implementations.

Custom logic (e.g. `getName`/`setName` for rename support) goes in **`mixin` classes** that
the generated `*Impl` classes extend, **never** in the generated files themselves
(regenerated builds overwrite them).

Hand-written parser skeleton:

```java
public class MyParser implements PsiParser {
  @Override
  public @NotNull ASTNode parse(IElementType root, PsiBuilder builder) {
    PsiBuilder.Marker rootM = builder.mark();
    while (!builder.eof()) {
      if (builder.getTokenType() == MyTypes.ID) {
        PsiBuilder.Marker propM = builder.mark();
        builder.advanceLexer();
        if (builder.getTokenType() == MyTypes.EQ) builder.advanceLexer();
        if (builder.getTokenType() == MyTypes.ID) builder.advanceLexer();
        propM.done(MyTypes.PROPERTY);
      } else {
        builder.advanceLexer();
      }
    }
    rootM.done(root);
    return builder.getTreeBuilt();
  }
}
```

`PsiParser`, `PsiBuilder`, `ASTNode`, `IElementType`, and
`ASTWrapperPsiElement` used by this skeleton are public platform APIs in the `2026.2.2`
source baseline. Before using another parser helper, inspect its declaration and metadata;
`public` visibility alone does not permit `@ApiStatus.Internal`, `@IntellijInternalApi`, or
implementation-only platform parser classes. Keep plugin-owned custom logic in the mixins
that generated classes extend, as described above; generation does not authorize calls into
platform-internal parser implementations.

Grammar-Kit generation does not make Kotlin compiler or language-plugin internals public.
If a mixin adds Kotlin-specific behavior, declare the Kotlin plugin dependency and use only
its supported public API; otherwise keep the generated PSI language-local.

The API check was performed against the
[`idea/2026.2.2` source snapshot](https://github.com/JetBrains/intellij-community/tree/1c7e601c0423e544917046c23763b15d0282e2a3)
and the [official parser/PSI guide](https://plugins.jetbrains.com/docs/intellij/implementing-parser-and-psi.html).
