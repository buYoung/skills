# Syntax Highlighting

## Syntax highlighting (lexer-based)

Two layers in the editor: **lexer-based syntax highlighting** (fast, token-only) and
**semantic Annotator** (PSI-based, slower). They compose.

```java
public class MySyntaxHighlighter extends SyntaxHighlighterBase {
  public static final TextAttributesKey EQ =
    createTextAttributesKey("MYLANG_EQ", DefaultLanguageHighlighterColors.OPERATION_SIGN);
  public static final TextAttributesKey ID =
    createTextAttributesKey("MYLANG_ID", DefaultLanguageHighlighterColors.IDENTIFIER);
  public static final TextAttributesKey COMMENT =
    createTextAttributesKey("MYLANG_COMMENT", DefaultLanguageHighlighterColors.LINE_COMMENT);
  public static final TextAttributesKey BAD_CHAR =
    createTextAttributesKey("MYLANG_BAD_CHARACTER", HighlighterColors.BAD_CHARACTER);

  private static final TextAttributesKey[] EQ_KEYS = {EQ}, ID_KEYS = {ID},
    COMMENT_KEYS = {COMMENT}, BAD_CHAR_KEYS = {BAD_CHAR}, NONE = TextAttributesKey.EMPTY_ARRAY;

  @Override public @NotNull Lexer getHighlightingLexer() { return new MyLexerAdapter(); }
  @Override public TextAttributesKey @NotNull [] getTokenHighlights(IElementType t) {
    if (t == MyTypes.EQ)             return EQ_KEYS;
    if (t == MyTypes.ID)             return ID_KEYS;
    if (t == MyTypes.COMMENT)        return COMMENT_KEYS;
    if (t == TokenType.BAD_CHARACTER) return BAD_CHAR_KEYS;
    return NONE;
  }
}
```

Always provide a fallback key (`DefaultLanguageHighlighterColors.*` /
`HighlighterColors.*`). Hard-coded RGB doesn't follow user theme changes.

Register via factory:

```xml
<lang.syntaxHighlighterFactory language="MyLang"
                               implementationClass="com.example.mylang.MySyntaxHighlighterFactory"/>
```

Expose categories to the user via `ColorSettingsPage`:

```xml
<colorSettingsPage implementation="com.example.mylang.MyColorSettingsPage"/>
```

Inside the page, build an `AttributesDescriptor[]` from your keys and provide demo text.
