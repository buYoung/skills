// Pairs with references/07_language_parser_definition_psi_file.md — the root PsiFile.
package com.example.simplelang

import com.intellij.extapi.psi.PsiFileBase
import com.intellij.openapi.fileTypes.FileType
import com.intellij.psi.FileViewProvider

class SimpleFile(viewProvider: FileViewProvider)
  : PsiFileBase(viewProvider, SimpleLanguage) {

  override fun getFileType(): FileType = SimpleFileType
  override fun toString(): String = "Simple File"
}
