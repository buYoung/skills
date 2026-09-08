# Search Everywhere API

Read this when a plugin contributes results or tabs to Search Everywhere, or migrates old
Search Everywhere integrations for Remote Development.

## API boundary for 2026.2.2

The stable external-plugin contract remains
[`SearchEverywhereContributor`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/lang-api/src/com/intellij/ide/actions/searcheverywhere/SearchEverywhereContributor.java)
through the `com.intellij.searchEverywhereContributor` EP declared in
[`LangExtensionPoints.xml`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/platform-resources/src/META-INF/LangExtensionPoints.xml).

IntelliJ Community `idea/2026.2.2` also exposes `SeItemsProvider` and
`SeItemsProviderFactory` from the public `intellij.platform.searchEverywhere` module, but both
types are `@ApiStatus.Experimental`. The source is fixed at commit
`1c7e601c0423e544917046c23763b15d0282e2a3`; see the
[`SeItemsProvider` declaration](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/searchEverywhere/shared/src/SeItemsProvider.kt),
[`SeItemsProviderFactory` declaration](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/searchEverywhere/shared/src/SeItemsProviderFactory.kt),
and [public module/EP metadata](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/searchEverywhere/shared/resources/intellij.platform.searchEverywhere.xml).

`SeTab` and `SeTabFactory` are also annotated experimental, but their
[`intellij.platform.searchEverywhere.frontend` module descriptor](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/searchEverywhere/frontend/resources/intellij.platform.searchEverywhere.frontend.xml)
has `visibility="internal"`. They are not supported external-plugin APIs and must not be used.

## Choosing the API

The Search Everywhere architecture is being redesigned for Remote Development. Newer IDE
branches use serializable result data so backend logic and frontend presentation can be
separated.

Use `SearchEverywhereContributor` for the stable public path. When Remote Development support
requires serializable result providers and the minimum supported IDE is 2026.2.2, the public
but experimental `SeItemsProvider` and `SeItemsProviderFactory` are available. Record that
minimum version and experimental compatibility risk. `SeLegacyItemPresentationProvider` is
also experimental and should be used only as a migration bridge from an existing legacy
contributor.

## Migration guidance

Existing `SearchEverywhereContributor` implementations continue to provide the stable local
integration. For a 2026.2.2 Remote Development migration, introduce the experimental provider
path only after confirming the module dependency and serialization contract on every target
IDE. Do not copy or cast to frontend implementation types to add a custom tab.

Keep returned items serializable and keep UI components out of backend result objects. Use
stable identifiers and presentation data instead of passing PSI, Swing, or service instances.

## Diagnostics checklist

1. Check the target IDE branch and module visibility before choosing old or new Search
   Everywhere APIs.
2. For Remote Development, verify items serialize without project-local object references.
3. Keep expensive search work cancellable and off UI paths.
4. Confirm result ranking and grouping remain stable when results arrive incrementally.
5. If migrating, preserve the stable contributor path for IDE versions that do not expose the
   public experimental provider module.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/api-notable-list-2025.html
