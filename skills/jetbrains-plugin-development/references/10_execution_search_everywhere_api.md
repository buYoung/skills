# Search Everywhere API

Read this when a plugin contributes results or tabs to Search Everywhere, or migrates old
Search Everywhere integrations for Remote Development.

## API boundary for 2026.3

In 2026.3 the old Search Everywhere API in `com.intellij.ide.actions.searcheverywhere` is
deprecated in favor of `com.intellij.platform.searchEverywhere`. The new API was introduced
in 2025.3 (on by default only in Remote Development) and has been enabled by default since
2026.2. The official
[2026.3 notable changes](https://plugins.jetbrains.com/docs/intellij/api-notable-list-2026.html)
schedule the old API to be disabled by default through a registry key in 2027.1 and removed
in 2027.2. At `idea/2026.3` (commit `c91871ae2864649d952825cff72569e3db0e7ac6`),
[`SearchEverywhereContributor`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-api/src/com/intellij/ide/actions/searcheverywhere/SearchEverywhereContributor.java)
carries `@Deprecated`; its `com.intellij.searchEverywhereContributor` EP is still declared in
[`intellij.platform.lang.xml`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-api/resources/intellij.platform.lang.xml).

The replacements `SeItemsProvider` and `SeItemsProviderFactory` (registered in
`com.intellij.searchEverywhere.itemsProviderFactory`) come from the public
`intellij.platform.searchEverywhere` module, but both types are `@ApiStatus.Experimental`;
see the
[`SeItemsProvider` declaration](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/searchEverywhere/shared/src/SeItemsProvider.kt),
[`SeItemsProviderFactory` declaration](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/searchEverywhere/shared/src/SeItemsProviderFactory.kt),
and [public module/EP metadata](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/searchEverywhere/shared/resources/intellij.platform.searchEverywhere.xml).

The notable-changes page maps custom tabs to `SeTabFactory` and the
`com.intellij.searchEverywhere.tabFactory` EP. At the 2026.3 tag, however, `SeTabFactory` and
that EP live in the
[`intellij.platform.searchEverywhere.frontend` module descriptor](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/searchEverywhere/frontend/resources/intellij.platform.searchEverywhere.frontend.xml),
which still declares `visibility="internal"`. Under the public API boundary of this skill, do
not use them until a target IDE exposes that module publicly; report the custom-tab gap
instead.

## Choosing the API

The Search Everywhere architecture is being redesigned for Remote Development. Newer IDE
branches use serializable result data so backend logic and frontend presentation can be
separated.

For new result sources whose minimum supported IDE is 2026.2 or later, implement
`SeItemsProvider` through `SeItemsProviderFactory` and record the experimental compatibility
risk. On older branches keep `SearchEverywhereContributor`; it still works through 2026.3,
but it is deprecated there and scheduled for removal.
`SeLegacyItemPresentationProvider` is also experimental and should be used only as a
migration bridge from an existing legacy contributor.

## Migration guidance

Plugins that support branches before 2026.2 keep their `SearchEverywhereContributor`
implementation for those branches. For 2026.2+ targets, migrate to the provider path after
confirming the module dependency and serialization contract on every target IDE, and plan
for the old API's removal in 2027.2. Do not copy or cast to frontend implementation types to
add a custom tab.

Keep returned items serializable and keep UI components out of backend result objects. Use
stable identifiers and presentation data instead of passing PSI, Swing, or service instances.

## Diagnostics checklist

1. Check the target IDE branch and module visibility before choosing old or new Search
   Everywhere APIs.
2. For Remote Development, verify items serialize without project-local object references.
3. Keep expensive search work cancellable and off UI paths.
4. Confirm result ranking and grouping remain stable when results arrive incrementally.
5. If migrating, keep the contributor path for IDE versions that do not enable the provider
   API by default.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/api-notable-list-2025.html
- https://plugins.jetbrains.com/docs/intellij/api-notable-list-2026.html
