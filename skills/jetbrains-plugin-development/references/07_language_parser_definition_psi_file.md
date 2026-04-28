# Parser Definition and PSI File

## `ParserDefinition` — the registration glue

```java
public final class MyParserDefinition implements ParserDefinition {
  public static final TokenSet WHITE_SPACES = TokenSet.create(TokenType.WHITE_SPACE);
  public static final TokenSet COMMENTS     = TokenSet.create(MyTypes.COMMENT);
  public static final IFileElementType FILE = new IFileElementType(MyLanguage.INSTANCE);

  @Override public @NotNull Lexer createLexer(Project p)  { return new MyLexerAdapter(); }
  @Override public @NotNull PsiParser createParser(Project p) { return new MyParser(); }
  @Override public @NotNull IFileElementType getFileNodeType() { return FILE; }
  @Override public @NotNull TokenSet getCommentTokens()    { return COMMENTS; }
  @Override public @NotNull TokenSet getStringLiteralElements() { return TokenSet.EMPTY; }

  @Override public @NotNull PsiElement createElement(ASTNode node) {
    return MyTypes.Factory.createElement(node);
  }

  @Override public @NotNull PsiFile createFile(@NotNull FileViewProvider vp) {
    return new MyFile(vp);
  }
}
```

```xml
<lang.parserDefinition language="MyLang"
                       implementationClass="com.example.mylang.MyParserDefinition"/>
```

The root `PsiFile`:

```java
public class MyFile extends PsiFileBase {
  public MyFile(@NotNull FileViewProvider vp) { super(vp, MyLanguage.INSTANCE); }
  @Override public @NotNull FileType getFileType() { return MyFileType.INSTANCE; }
}
```

At this point, `runIde` opens `.mylang` files as your language — you can navigate the PSI
tree but no colors, no completion, no references.
