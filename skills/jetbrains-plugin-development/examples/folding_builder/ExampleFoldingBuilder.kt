// Pairs with references/06_code_insight_folding.md.
// Folding builders are stateless extensions. Re-walk the current PSI on each call
// instead of caching PsiElement or ASTNode instances on fields.
package com.example.folding

import com.intellij.lang.ASTNode
import com.intellij.lang.folding.FoldingBuilderEx
import com.intellij.lang.folding.FoldingDescriptor
import com.intellij.openapi.editor.Document
import com.intellij.openapi.project.DumbAware
import com.intellij.psi.PsiComment
import com.intellij.psi.PsiElement

class ExampleFoldingBuilder : FoldingBuilderEx(), DumbAware {
  override fun buildFoldRegions(
    root: PsiElement,
    document: Document,
    quick: Boolean,
  ): Array<FoldingDescriptor> {
    val descriptors = mutableListOf<FoldingDescriptor>()
    collectFoldRegions(root, document, descriptors)
    return descriptors.toTypedArray()
  }

  override fun getPlaceholderText(node: ASTNode): String = "/*...*/"

  override fun isCollapsedByDefault(node: ASTNode): Boolean = false

  private fun collectFoldRegions(
    element: PsiElement,
    document: Document,
    descriptors: MutableList<FoldingDescriptor>,
  ) {
    if (element is PsiComment && element.textContains('\n')) {
      val range = element.textRange
      if (!range.isEmpty && range.endOffset <= document.textLength) {
        descriptors += FoldingDescriptor(element, range)
      }
    }

    var child = element.firstChild
    while (child != null) {
      collectFoldRegions(child, document, descriptors)
      child = child.nextSibling
    }
  }
}
