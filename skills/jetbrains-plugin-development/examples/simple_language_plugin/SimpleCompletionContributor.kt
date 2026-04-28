// Pairs with references/07_language_completion.md.
// PsiElementPattern gates when this fires — here, only on identifier tokens
// inside a Simple file.
package com.example.simplelang

import com.example.simplelang.psi.SimpleTypes
import com.intellij.codeInsight.completion.CompletionContributor
import com.intellij.codeInsight.completion.CompletionParameters
import com.intellij.codeInsight.completion.CompletionProvider
import com.intellij.codeInsight.completion.CompletionResultSet
import com.intellij.codeInsight.completion.CompletionType
import com.intellij.codeInsight.lookup.LookupElementBuilder
import com.intellij.patterns.PlatformPatterns
import com.intellij.util.ProcessingContext

class SimpleCompletionContributor : CompletionContributor() {
  init {
    extend(
      CompletionType.BASIC,
      PlatformPatterns.psiElement(SimpleTypes.ID).withLanguage(SimpleLanguage),
      object : CompletionProvider<CompletionParameters>() {
        override fun addCompletions(
          parameters: CompletionParameters,
          context: ProcessingContext,
          result: CompletionResultSet,
        ) {
          listOf("name", "value", "version").forEach {
            result.addElement(LookupElementBuilder.create(it))
          }
        }
      }
    )
  }
}
