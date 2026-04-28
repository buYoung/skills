# JFlex Lexer

## Lexer with JFlex

The platform recommends JFlex for lexers. Output is a `FlexLexer` that you wrap with
`FlexAdapter` to produce the platform's `Lexer`.

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
