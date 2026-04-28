// Pairs with references/07_language_inline_completion.md.
// InlineCompletionProvider is the gray in-editor suggestion surface, not the
// popup completion surface covered by CompletionContributor.
package com.example.inlinecompletion

import com.intellij.codeInsight.inline.completion.InlineCompletionEvent
import com.intellij.codeInsight.inline.completion.InlineCompletionProvider
import com.intellij.codeInsight.inline.completion.InlineCompletionProviderID
import com.intellij.codeInsight.inline.completion.InlineCompletionRequest
import com.intellij.codeInsight.inline.completion.elements.InlineCompletionGrayTextElement
import com.intellij.codeInsight.inline.completion.suggestion.InlineCompletionSingleSuggestion
import com.intellij.codeInsight.inline.completion.suggestion.InlineCompletionSuggestion

class ExampleInlineCompletionProvider : InlineCompletionProvider {
  override val id = InlineCompletionProviderID("com.example.inlinecompletion.ExampleInlineCompletionProvider")

  override fun isEnabled(event: InlineCompletionEvent): Boolean {
    return event is InlineCompletionEvent.DocumentChange ||
      event is InlineCompletionEvent.DirectCall ||
      event is InlineCompletionEvent.ManualCall
  }

  override suspend fun getSuggestion(request: InlineCompletionRequest): InlineCompletionSuggestion {
    val suggestionText = buildSuggestionText(request)
    if (suggestionText.isEmpty()) {
      return InlineCompletionSuggestion.Empty
    }

    return InlineCompletionSingleSuggestion.build {
      emit(InlineCompletionGrayTextElement(suggestionText))
    }
  }

  private fun buildSuggestionText(request: InlineCompletionRequest): String {
    val offset = request.endOffset
    val document = request.document
    if (offset < 0 || offset > document.textLength) {
      return ""
    }

    val lineNumber = document.getLineNumber(offset)
    val lineEndOffset = document.getLineEndOffset(lineNumber)
    val restOfLine = document.charsSequence.subSequence(offset, lineEndOffset).toString()
    if (restOfLine.isNotBlank()) {
      return ""
    }

    return " // inline suggestion"
  }
}
