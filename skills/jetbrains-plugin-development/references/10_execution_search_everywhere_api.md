# Search Everywhere API

Read this when a plugin contributes results or tabs to Search Everywhere, or migrates old
Search Everywhere integrations for Remote Development.

## Modern API direction

The Search Everywhere architecture is being redesigned for Remote Development. Newer IDE
branches use serializable result data so backend logic and frontend presentation can be
separated.

Use `SeItemsProvider` and `SeItemsProviderFactory` for result sources on branches that expose
the new API. Use `SeTab` and `SeTabFactory` for frontend-only tabs. Use
`SeLegacyItemPresentationProvider` only as a migration bridge from older
`SearchEverywhereContributor` integrations.

## Migration guidance

Legacy `SearchEverywhereContributor` implementations can continue to work in local
monolithic IDEs through adapters, but they are not the long-term shape for remote-ready
plugins. For new code that targets 2025-era IDEs and Remote Development, start with the new
API when available.

Keep returned items serializable and keep UI components out of backend result objects. Use
stable identifiers and presentation data instead of passing PSI, Swing, or service instances.

## Diagnostics checklist

1. Check the target IDE branch before choosing old or new Search Everywhere APIs.
2. For Remote Development, verify items serialize without project-local object references.
3. Keep expensive search work cancellable and off UI paths.
4. Confirm result ranking and grouping remain stable when results arrive incrementally.
5. If migrating, keep old contributor code only behind explicit branch compatibility needs.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/api-notable-list-2025.html
