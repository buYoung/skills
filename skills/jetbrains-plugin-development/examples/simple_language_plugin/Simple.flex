// Pairs with references/07_language_lexer_jflex.md.
// JFlex source. The IntelliJ Platform Gradle Plugin runs JFlex with --charat to
// produce com.example.simplelang.SimpleLexer (which implements FlexLexer); we
// then wrap it in FlexAdapter via SimpleLexerAdapter.kt.
package com.example.simplelang;

import com.intellij.lexer.FlexLexer;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.TokenType;
import com.example.simplelang.psi.SimpleTypes;

%%

%class SimpleLexer
%implements FlexLexer
%unicode
%function advance
%type IElementType
%eof{ return; %eof}

CRLF=\R
WHITE_SPACE=[\ \n\t\f]
ID=[A-Za-z_][A-Za-z_0-9]*
COMMENT="#"[^\r\n]*

%%

{COMMENT}              { return SimpleTypes.COMMENT; }
{ID}                   { return SimpleTypes.ID; }
"="                    { return SimpleTypes.EQ; }
({WHITE_SPACE}|{CRLF})+ { return TokenType.WHITE_SPACE; }
[^]                    { return TokenType.BAD_CHARACTER; }
