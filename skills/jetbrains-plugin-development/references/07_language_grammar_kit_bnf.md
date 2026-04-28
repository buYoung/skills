# Grammar-Kit BNF

## Parser via Grammar-Kit BNF

Grammar-Kit generates the parser, the element/token type holders, and PSI interfaces from
a BNF file. Hand-rolled parsers are possible but only worth the effort for unusual grammars.

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
