// Pairs with references/06_code_insight_formatter_commenter.md.
// Drives Ctrl+/ (line) and Ctrl+Shift+/ (block) for the language.
package com.example.simplelang

import com.intellij.lang.Commenter

class SimpleCommenter : Commenter {
  override fun getLineCommentPrefix(): String = "#"
  override fun getBlockCommentPrefix(): String? = null
  override fun getBlockCommentSuffix(): String? = null
  override fun getCommentedBlockCommentPrefix(): String? = null
  override fun getCommentedBlockCommentSuffix(): String? = null
}
