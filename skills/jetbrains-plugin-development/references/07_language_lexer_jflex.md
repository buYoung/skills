# JFlex Lexer

## Lexer with JFlex

The platform recommends JFlex for lexers. Output is a `FlexLexer` that you wrap with
`FlexAdapter` to produce the platform's `Lexer`.
With the IntelliJ Platform Gradle Plugin 2.18.1 setup in this skill, apply
`org.jetbrains.intellij.platform.grammarkit` to obtain the `generateLexer` task. The same
plugin also provides Grammar-Kit parser generation; do not add a separate `jflex()`
dependency helper or apply the standalone `org.jetbrains.grammarkit` plugin alongside it.
For an older build, check the generator plugin supported by that Gradle plugin version.

`MyLang.flex`:

```
package com.example.mylang;
import com.intellij.lexer.FlexLexer;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.TokenType;
import com.example.mylang.psi.MyTypes;

%%
%class MyLexer
%implements FlexLexer
%unicode
%function advance
%type IElementType
%eof{ return; %eof}

CRLF=\R
WS=[\ \n\t\f]
ID=[A-Za-z_][A-Za-z_0-9]*
COMMENT="#"[^\r\n]*

%%
{COMMENT}        { return MyTypes.COMMENT; }
{ID}             { return MyTypes.ID; }
"="              { return MyTypes.EQ; }
{WS}+ | {CRLF}+  { return TokenType.WHITE_SPACE; }
[^]              { return TokenType.BAD_CHARACTER; }
```

Key points:

- Always `%unicode`.
- Return `TokenType.WHITE_SPACE` for whitespace and `TokenType.BAD_CHARACTER` for unknowns —
  they participate in incremental highlighting and error display.
- The Gradle plugin runs JFlex with `--charat`, which is required for the platform's
  CharSequence-based lexer interface.

Adapter:

```java
public class MyLexerAdapter extends FlexAdapter {
  public MyLexerAdapter() { super(new MyLexer(null)); }
}
```

A new `MyLexerAdapter()` per call site — lexers are stateful and not reusable.

`FlexLexer`, `FlexAdapter`, `Lexer`, `IElementType`, and `TokenType` are the public lexer
surface used by this example in the `2026.2.2` source baseline. Do not cast to unsupported
platform lexer implementations or use reflection to reach their internals. Plugin-owned
generated lexer types remain usable through their normal generated contract. Check any newer lexer helper for `@ApiStatus.Internal` or
`@IntellijInternalApi` before putting it in plugin code.

The generation and API guidance was checked against the
[`idea/2026.2.2` source snapshot](https://github.com/JetBrains/intellij-community/tree/1c7e601c0423e544917046c23763b15d0282e2a3),
the [Grammar-Kit Gradle plugin documentation](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-plugins.html),
and the [official lexer guide](https://plugins.jetbrains.com/docs/intellij/implementing-parser-and-psi.html).
