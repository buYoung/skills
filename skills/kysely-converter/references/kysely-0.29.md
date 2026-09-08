# Kysely 0.29 Reference

## Review baseline and scope

- Series: **0.29.x**.
- Initially reviewed version: **0.29.5**.
- Current documentation review baseline: **0.29.5**, checked **2026-09-08**.
- Evidence: official release notes, published package metadata, and official API/SQL documentation. This is a documentation review, not a claim that all examples were type-checked or executed.
- Official API documentation is a moving reference. Use the target installation's declarations or tagged source when an exact signature differs; the baseline is not an assertion that every live documentation page is frozen at 0.29.5.

Read this with the relevant topic reference. It covers query authoring and diagnosis; migration operations and unrelated internal API changes are outside scope.

## Contents

- [Runtime and tooling](#runtime-and-tooling)
- [Query-facing changes](#query-facing-changes)
- [Execution options](#execution-options)
- [Patch-specific evidence](#patch-specific-evidence)
- [Topic routing and maintenance](#topic-routing-and-maintenance)

## Runtime and tooling

The [0.29.5 package manifest](https://raw.githubusercontent.com/kysely-org/kysely/v0.29.5/package.json) declares Node.js >=22.0.0, ESM packaging, and rejection declarations for TypeScript <5.4. Check the application's actual runtime and module-loading mode; CommonJS callers need supported `require(esm)` behavior or dynamic import. Node's minimum engine range alone does not establish that every module-loading path works.

The [0.29.0 release](https://github.com/kysely-org/kysely/releases/tag/v0.29.0) moved the build target to ES2023 and removed the CommonJS distribution. Inspect other runtimes and driver compatibility separately rather than applying the Node engine declaration to them.

## Query-facing changes

These changes entered in 0.29.0 unless a patch is stated below. The [0.29.0 release notes](https://github.com/kysely-org/kysely/releases/tag/v0.29.0) are the introduction/removal evidence.

| Area | Change and action |
| --- | --- |
| Raw values | Removed `sql.value` / `sql.literal`; use `sql.val` / `sql.lit`. |
| Execution | `db.executeQuery` takes options as its second argument, replacing deprecated `queryId`. |
| Low-level results | Removed `QueryResult.numUpdatedOrDeletedRows`; use `numAffectedRows`. This does not rename `UpdateResult.numUpdatedRows` or `DeleteResult.numDeletedRows`. |
| Schema scope | Removed `ExpressionBuilder.withSchema`; establish scope through `db.withSchema(...)` before query construction. |
| CASE references | Added `whenRef`, `thenRef`, and `elseRef`; existing `eb.ref(...)` expression forms remain useful. |
| Table type helpers | Added `$pickTables`, `$omitTables`, `$extendTables`; `withTables` is deprecated in favor of `$extendTables`. |
| CTEs | Added `with(name, query)` alongside callback construction. |
| Narrowing | `$narrowType` supports nested objects/discriminated unions. |
| Update inputs | `Updateable` accepts explicit undefined with `exactOptionalPropertyTypes`. |
| Plugins | Added `SafeNullComparisonPlugin` and `ParseJSONResultsPlugin.shouldParse`. |

Use [Kysely API documentation](https://kysely-org.github.io/kysely-apidoc/classes/Kysely.html) for schema/table helper scope. These type helpers do not alter physical tables. `$narrowType` does not filter rows or validate runtime data; justify narrowing from query semantics or runtime evidence. [SafeNullComparisonPlugin](https://kysely-org.github.io/kysely-apidoc/classes/SafeNullComparisonPlugin.html) changes how null comparisons compile, so inspect existing plugins before translating SQL; explicit IS NULL remains clear without adding a plugin. [ParseJSONResultsPlugin](https://kysely-org.github.io/kysely-apidoc/classes/ParseJSONResultsPlugin.html) configuration can affect returned JSON values, so preserve it when changing queries.

## Execution options

In this series, query execution accepts [AbortableQueryOptions](https://kysely-org.github.io/kysely-apidoc/interfaces/AbortableQueryOptions.html), including `signal` and `inflightQueryAbortStrategy`. Query builders accept options in execution methods; raw queries take them after `db`; `db.executeQuery(compiledQuery, options)` takes them second. Consult the selected method's signature rather than passing the old query ID.

Cancellation does not always mean the server stopped work. The default strategy ignores the in-flight result; database-side cancellation or session termination depends on the dialect and control-connection configuration. Keep the supplied options with the execution site when refactoring. Do not introduce a timeout or stronger cancellation strategy just to adapt a query. A timeout signal also needs runtime support if the requested code uses it.

See [building versus execution](https://kysely.dev/docs/recipes/splitting-query-building-and-execution). Compilation produces SQL and parameters without demonstrating that cancellation, transactions, or result decoding work against a real server.

## Patch-specific evidence

| Release | Query-relevant evidence |
| --- | --- |
| [0.29.1](https://github.com/kysely-org/kysely/releases/tag/v0.29.1) | Fixed chaining of plugin result transformations. |
| [0.29.2](https://github.com/kysely-org/kysely/releases/tag/v0.29.2) | Fixed branded types in `$narrowType`. |
| [0.29.3](https://github.com/kysely-org/kysely/releases/tag/v0.29.3) | Release fix concerns migration exclusivity; no query-authoring change is recorded here. |
| [0.29.4](https://github.com/kysely-org/kysely/releases/tag/v0.29.4) | Fixed PostgreSQL control-client password forwarding and SQLite DELETE RETURNING placement relative to ORDER BY/LIMIT. Server support remains a separate condition. |
| [0.29.5](https://github.com/kysely-org/kysely/releases/tag/v0.29.5) | Fixed infinite type-check recursion and missing `beforeThrow` calls during in-flight abort handling. |

Do not assume an earlier 0.29 patch contains a later fix. These notes do not authorize changing the user's installed version.

## Topic routing and maintenance

- [SELECT](select.md): query shape, aliases, CTEs, conditional selection and result inference.
- [INSERT](insert.md): common type contract, values, conflict handling and result metadata.
- [UPDATE](update.md) and [DELETE](delete.md): predicates, assignments, dialect limitations and returned rows.
- [Operators](operators.md): BETWEEN methods, binding and raw SQL boundaries.
- [Window functions](window_function.md): OVER, frame semantics and server restrictions.

If the project version is unknown, announce the 0.29.5 assumption as instructed in [SKILL.md](../SKILL.md#2-establish-project-context-and-version). If requested and resolved versions conflict, ask which to target. For another version, consult official evidence for that version instead of treating this file as universal compatibility guidance.

For a later patch in this series, update the current baseline/date and patch differences after review, retaining the initial baseline. Add later minor series as separate files and register them in SKILL.md. Do not backfill historical version documents.
