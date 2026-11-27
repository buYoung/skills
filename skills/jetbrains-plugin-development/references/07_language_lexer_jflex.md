# JFlex Lexer

## Lexer with JFlex

The platform recommends JFlex for lexers. Output is a `FlexLexer` that you wrap with
`FlexAdapter` to produce the platform's `Lexer`.
With the IntelliJ Platform Gradle Plugin 2.20.1 setup in this skill, apply
`org.jetbrains.intellij.platform.grammarkit` to obtain the `generateLexer` task. The same
plugin also provides Grammar-Kit parser generation and supplies the JFlex version; add the
`jflex(...)` dependency helper only to override that version. Do not apply the standalone
`org.jetbrains.grammarkit` plugin alongside it. Point `generateLexer` at the `.flex` file and
add its output to the source set as shown in `01_core_gradle_project.md`.
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
%eof{ return;
%eof}

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
- Start every directive on its own line, including the closing `%eof}`. JFlex requires
  each directive at the beginning of a line; `%eof{ return; %eof}` on one line fails with
  "Unexpected end of file in macros" ([JFlex manual](https://jflex.de/manual.html)).
- Return `TokenType.WHITE_SPACE` for whitespace and `TokenType.BAD_CHARACTER` for unknowns —
  they participate in incremental highlighting and error display.
- The Gradle plugin runs JetBrains' JFlex build (1.10.17 by default in 2.20.1, "tweaked for
  IntelliJ platform"), whose generated lexer reads a `CharSequence` buffer as the platform's
  `FlexLexer` interface requires. `generateLexer` passes only `-d`, an optional `--skel`, and
  the source file; this JFlex has no `--charat` option.

Adapter:

```java
public class MyLexerAdapter extends FlexAdapter {
  public MyLexerAdapter() { super(new MyLexer(null)); }
}
```

A new `MyLexerAdapter()` per call site — lexers are stateful and not reusable.

`FlexLexer`, `FlexAdapter`, `Lexer`, `IElementType`, and `TokenType` are the public lexer
surface used by this example in the `2026.3` source baseline. Do not cast to unsupported
platform lexer implementations or use reflection to reach their internals. Plugin-owned
generated lexer types remain usable through their normal generated contract. Check any newer lexer helper for `@ApiStatus.Internal` or
`@IntellijInternalApi` before putting it in plugin code.

The generation and API guidance was checked against the
[`idea/2026.3` source snapshot](https://github.com/JetBrains/intellij-community/tree/c91871ae2864649d952825cff72569e3db0e7ac6),
the [Grammar-Kit Gradle plugin documentation](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-plugins.html),
and the [official lexer guide](https://plugins.jetbrains.com/docs/intellij/implementing-parser-and-psi.html).
