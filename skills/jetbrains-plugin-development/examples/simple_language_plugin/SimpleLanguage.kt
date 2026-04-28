// Pairs with references/07_language_file_type.md — the Language singleton.
// The string passed to super(...) is the case-sensitive Language ID; every
// language="Simple" attribute in plugin.xml must match it exactly.
package com.example.simplelang

import com.intellij.lang.Language

object SimpleLanguage : Language("Simple")
