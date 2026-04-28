// Pairs with references/07_language_syntax_highlighting.md — lexer-based syntax highlighting.
// Always provide a fallback key from DefaultLanguageHighlighterColors / HighlighterColors
// so users' theme overrides flow through.
package com.example.simplelang

import com.example.simplelang.psi.SimpleTypes
import com.intellij.lexer.Lexer
import com.intellij.openapi.editor.DefaultLanguageHighlighterColors
import com.intellij.openapi.editor.HighlighterColors
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.openapi.editor.colors.TextAttributesKey.createTextAttributesKey
import com.intellij.openapi.fileTypes.SyntaxHighlighter
import com.intellij.openapi.fileTypes.SyntaxHighlighterBase
import com.intellij.openapi.fileTypes.SyntaxHighlighterFactory
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.psi.TokenType
import com.intellij.psi.tree.IElementType

object SimpleHighlighterKeys {
  val EQ      = createTextAttributesKey("SIMPLE_EQ",      DefaultLanguageHighlighterColors.OPERATION_SIGN)
  val ID      = createTextAttributesKey("SIMPLE_ID",      DefaultLanguageHighlighterColors.IDENTIFIER)
  val COMMENT = createTextAttributesKey("SIMPLE_COMMENT", DefaultLanguageHighlighterColors.LINE_COMMENT)
  val BAD     = createTextAttributesKey("SIMPLE_BAD",     HighlighterColors.BAD_CHARACTER)
}

class SimpleSyntaxHighlighter : SyntaxHighlighterBase() {
  override fun getHighlightingLexer(): Lexer = SimpleLexerAdapter()

  override fun getTokenHighlights(tokenType: IElementType): Array<TextAttributesKey> = when (tokenType) {
    SimpleTypes.EQ              -> arrayOf(SimpleHighlighterKeys.EQ)
    SimpleTypes.ID              -> arrayOf(SimpleHighlighterKeys.ID)
    SimpleTypes.COMMENT         -> arrayOf(SimpleHighlighterKeys.COMMENT)
    TokenType.BAD_CHARACTER     -> arrayOf(SimpleHighlighterKeys.BAD)
    else                        -> TextAttributesKey.EMPTY_ARRAY
  }
}

class SimpleSyntaxHighlighterFactory : SyntaxHighlighterFactory() {
  override fun getSyntaxHighlighter(project: Project?, virtualFile: VirtualFile?): SyntaxHighlighter =
    SimpleSyntaxHighlighter()
}
