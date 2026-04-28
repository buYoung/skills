// Pairs with references/07_language_file_type.md — file-name binding.
// fieldName="INSTANCE" in plugin.xml requires this to be a singleton object
// (or a Kotlin object exposes the static INSTANCE field by convention via @JvmField on a
// companion property if you prefer a class). Keeping it as `object` is simplest.
package com.example.simplelang

import com.intellij.openapi.fileTypes.LanguageFileType
import javax.swing.Icon

object SimpleFileType : LanguageFileType(SimpleLanguage) {
  override fun getName(): String = "Simple File"
  override fun getDescription(): String = "Simple language file"
  override fun getDefaultExtension(): String = "simple"
  override fun getIcon(): Icon? = null  // replace with a real icon resource for production
}
