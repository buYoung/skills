// Pairs with references/07_language_grammar_kit_bnf.md — the elementTypeClass and
// tokenTypeClass named in Simple.bnf. The generated SimpleTypes creates its constants
// through these constructors.
package com.example.simplelang.psi

import com.example.simplelang.SimpleLanguage
import com.intellij.psi.tree.IElementType

class SimpleElementType(debugName: String) : IElementType(debugName, SimpleLanguage)

class SimpleTokenType(debugName: String) : IElementType(debugName, SimpleLanguage) {
  override fun toString(): String = "SimpleTokenType." + super.toString()
}
