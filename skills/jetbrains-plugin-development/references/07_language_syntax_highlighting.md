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

Expose categories to the user via `ColorSettingsPage`. The registering extension point
depends on the minimum IDE version. For `since-build` 263 (2026.3) or later, declare the
page in `com.intellij.colorSettings`; `displayName` (or `key` and `bundle`) must match
`getDisplayName()`, because the Settings tree is built from the declaration without loading
the class:

```xml
<colorSettings implementation="com.example.mylang.MyColorSettingsPage"
               displayName="MyLang"/>
```

Before 2026.3, use `com.intellij.colorSettingsPage`, which is deprecated since 2026.3 but
still works:

```xml
<colorSettingsPage implementation="com.example.mylang.MyColorSettingsPage"/>
```

A plugin that supports both ranges can register the page with both EPs: 2026.3+ uses the
`colorSettings` declaration and ignores `colorSettingsPage`, while earlier versions ignore the
unknown `colorSettings` entry but then cannot load or unload the plugin without a restart.
If dynamic reload on those versions matters, keep only `colorSettingsPage` until the
minimum reaches 2026.3. See
[Registering a Color Settings Page](https://plugins.jetbrains.com/docs/intellij/syntax-highlighting-and-error-highlighting.html#registering-a-color-settings-page).

Inside the page, build an `AttributesDescriptor[]` from your keys and provide demo text.
