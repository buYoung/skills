// Pairs with references/07_language_annotator.md.
// Annotator is stateless and shared across files/threads. Filter early; do not do
// expensive resolution without caching (see CachedValue in 05_file_model_psi_basics.md).
package com.example.simplelang

import com.example.simplelang.psi.SimpleProperty
import com.intellij.lang.annotation.AnnotationHolder
import com.intellij.lang.annotation.Annotator
import com.intellij.lang.annotation.HighlightSeverity
import com.intellij.psi.PsiElement

class SimpleAnnotator : Annotator {
  override fun annotate(element: PsiElement, holder: AnnotationHolder) {
    if (element !is SimpleProperty) return
    val name = element.name ?: return
    if (name.isBlank()) {
      holder.newAnnotation(HighlightSeverity.ERROR, "Property name must not be blank")
        .range(element.textRange)
        .create()
    }
  }
}
