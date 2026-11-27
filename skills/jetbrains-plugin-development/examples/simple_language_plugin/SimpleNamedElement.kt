// Pairs with references/07_language_grammar_kit_bnf.md — the `implements` interface of the
// `property` rule in Simple.bnf. The generated SimpleProperty interface extends it.
package com.example.simplelang.psi

import com.intellij.psi.PsiNameIdentifierOwner

interface SimpleNamedElement : PsiNameIdentifierOwner
