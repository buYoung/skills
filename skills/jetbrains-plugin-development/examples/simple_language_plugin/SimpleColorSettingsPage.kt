// Pairs with references/07_language_syntax_highlighting.md — exposes the highlighter keys
// in Settings | Editor | Color Scheme so users can theme them.
package com.example.simplelang

import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.openapi.fileTypes.SyntaxHighlighter
import com.intellij.openapi.options.colors.AttributesDescriptor
import com.intellij.openapi.options.colors.ColorDescriptor
import com.intellij.openapi.options.colors.ColorSettingsPage
import javax.swing.Icon

class SimpleColorSettingsPage : ColorSettingsPage {
  override fun getDisplayName(): String = "Simple"
  override fun getIcon(): Icon? = null
  override fun getHighlighter(): SyntaxHighlighter = SimpleSyntaxHighlighter()

  override fun getDemoText(): String = """
    # a comment
    name = value
  """.trimIndent()

  override fun getAdditionalHighlightingTagToDescriptorMap(): Map<String, TextAttributesKey>? = null

  override fun getAttributeDescriptors(): Array<AttributesDescriptor> = arrayOf(
    AttributesDescriptor("Identifier", SimpleHighlighterKeys.ID),
    AttributesDescriptor("Equals sign", SimpleHighlighterKeys.EQ),
    AttributesDescriptor("Comment",    SimpleHighlighterKeys.COMMENT),
    AttributesDescriptor("Bad character", SimpleHighlighterKeys.BAD),
  )

  override fun getColorDescriptors(): Array<ColorDescriptor> = ColorDescriptor.EMPTY_ARRAY
}
