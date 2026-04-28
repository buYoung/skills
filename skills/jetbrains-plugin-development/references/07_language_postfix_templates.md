# Postfix Templates

Read this when a plugin adds `.if`, `.var`, `.notnull`, or similar postfix completion
expansions for an existing or custom language.

## Registration and shape

Register `PostfixTemplateProvider` with
`com.intellij.codeInsight.template.postfixTemplateProvider`. The provider supplies one or
more `PostfixTemplate` implementations for the current language. During code completion,
the IDE asks providers for enabled templates and adds applicable ones to the completion list.

Simple templates usually decide whether an expression is applicable and then expand text in
the editor. More advanced templates can expose editable fields and use selector logic. Prefer
postfix templates when the user writes an expression first and then transforms or wraps it.
Use `06_code_insight_surround_with.md` when the user explicitly selects a code fragment and invokes
Surround With.

## Description resources

Each template needs user-facing description resources under
`postfixTemplates/<TemplateClassSimpleName>/`. The directory name must match the simple class
name. Provide a `description.html` and before/after template files for the target language
extension. These resources drive the settings preview and help users understand the expansion.

In multi-module plugins, make resource paths unique after packaging. Duplicate resource names
can be overwritten when modules are combined into one distribution artifact.

## Diagnostics checklist

1. Confirm the provider is registered through `postfixTemplateProvider`, not through normal
   `completion.contributor`.
2. Confirm the template is enabled in `Settings | Editor | General | Postfix Completion`.
3. Confirm applicability checks are local and cheap; do not perform broad resolution on each
   completion invocation.
4. Confirm description resources are packaged and their directory matches the template class
   simple name.
5. If a language-specific template is missing, verify the language dependency and language ID
   in `plugin.xml`.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/postfix-templates.html
- https://plugins.jetbrains.com/docs/intellij/postfix-completion.html
