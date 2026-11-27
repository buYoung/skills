// Pairs with references/07_language_grammar_kit_bnf.md — the `mixin` of the `property` rule
// in Simple.bnf. The generated SimplePropertyImpl extends this class, so rename support lives
// here and survives regeneration.
package com.example.simplelang.psi.impl

import com.example.simplelang.SimpleFileType
import com.example.simplelang.psi.SimpleNamedElement
import com.example.simplelang.psi.SimpleProperty
import com.example.simplelang.psi.SimpleTypes
import com.intellij.extapi.psi.ASTWrapperPsiElement
import com.intellij.lang.ASTNode
import com.intellij.psi.PsiElement
import com.intellij.psi.PsiFileFactory
import com.intellij.psi.util.PsiTreeUtil
import com.intellij.util.IncorrectOperationException

abstract class SimpleNamedElementImpl(node: ASTNode) : ASTWrapperPsiElement(node), SimpleNamedElement {
  // The first ID of `property ::= ID EQ ID?` is the property name.
  override fun getNameIdentifier(): PsiElement? = node.findChildByType(SimpleTypes.ID)?.psi

  override fun getName(): String? = nameIdentifier?.text

  override fun setName(name: String): PsiElement {
    val oldId = node.findChildByType(SimpleTypes.ID)
      ?: throw IncorrectOperationException("Property has no name")
    val dummy = PsiFileFactory.getInstance(project).createFileFromText("dummy.simple", SimpleFileType, "$name=")
    val newId = PsiTreeUtil.findChildOfType(dummy, SimpleProperty::class.java)
      ?.node?.findChildByType(SimpleTypes.ID)
      ?: throw IncorrectOperationException("Invalid property name: $name")
    node.replaceChild(oldId, newId)
    return this
  }
}
