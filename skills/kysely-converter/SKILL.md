---
name: kysely-converter
description: Convert raw SQL into type-safe Kysely TypeScript, write Kysely queries from requirements without source SQL, modify or refactor existing Kysely code, and diagnose Kysely type errors. Use for SELECT, INSERT, UPDATE, DELETE, joins, CTEs, expressions, and window functions with version-aware SQL dialect handling. Excludes migration operations and work on other query builders.
---

# Kysely Query Workflow

Translate query intent into Kysely code using the project's schema types, dialect, and installed API. Source SQL is optional. Keep SQL semantics and the application's result contract visible throughout the task.

## 1. Classify the request

- **Convert SQL:** identify input parameters, clauses, and expected output columns before mapping methods.
- **Write a query:** derive tables, relationships, filtering, cardinality, ordering, and desired result shape from requirements; ask for missing schema or business rules that determine the query.
- **Modify or refactor:** identify the intended behavior change, or preserve behavior for a refactor. Read the existing builder, helpers, execution site, and result consumer.
- **Diagnose types:** obtain the exact error, failing expression, relevant table types, and expected result. Follow the diagnostic order below rather than guessing a replacement type.

## 2. Establish project context and version

Inspect the relevant project package manifest, installed Kysely package metadata when available, lockfile resolution, TypeScript version, database dialect/server version, driver, schema types, and nearby query code. A dependency range is not an exact installed version. Account for workspace-specific resolutions and plugins that transform queries or results.

Use the user's requested version together with installation and lock information. If they conflict, ask which version to target before choosing APIs. If no version can be confirmed, explicitly state **“Assuming Kysely 0.29.5”** and proceed with that baseline; do not present it as the installed version. Missing dialect, schema, or return requirements still need clarification when they affect correctness.

For 0.29.x, read [the version reference](references/kysely-0.29.md) before selecting APIs. For another version, verify relevant APIs against that version's official release notes and tagged source/declarations. Do not apply the 0.29 reference as proof of compatibility with older or later versions, or silently upgrade the project.

## 3. Select references

Read only the topics required by the request, alongside the applicable version reference.

| Need | Reference |
| --- | --- |
| Selection, aliases, joins, subqueries, CTEs, aggregation, pagination, conditional selection | [SELECT](references/select.md) |
| Schema read/write types, inserted values, conflict handling, insertion results | [INSERT](references/insert.md) |
| Assignments, update joins, affected rows, update results | [UPDATE](references/update.md) |
| Delete predicates, USING/JOIN, deletion results | [DELETE](references/delete.md) |
| Boolean grouping, NULL, BETWEEN, values versus references, raw predicates | [Operators](references/operators.md) |
| Ranking, value/aggregate windows, frames, top-N-per-group | [Window functions](references/window_function.md) |
| Runtime requirements, changed/removed APIs, patch differences | [Kysely 0.29](references/kysely-0.29.md) |

For type errors, start with the [shared type contract](references/insert.md#schema-and-value-types), then read SELECT for scope/result inference and the reference for the failing operation.

## 4. Convert, write, modify, or diagnose

### Preserve query meaning

For SQL conversion, map clauses without changing boolean parentheses, NULL/three-valued logic, join kind or predicate placement (`ON` versus `WHERE`), duplicate rows, grouping, ordering, pagination, selected columns, or aliases. Preserve `UNION` versus `UNION ALL` and `COUNT(*)` versus `COUNT(column)`. Do not add `DISTINCT`, filters, limits, or an arbitrary ordering to conceal uncertain semantics. Explain nondeterministic source pagination or representative-row selection.

For a new query, settle those same choices from the requirements. Prefer expression-builder callbacks for scoped references and dedicated methods for supported syntax. Bind data values; use a `sql` fragment when the target API cannot express the required syntax. Check database support separately from Kysely method availability.

When modifying code, follow the query through helpers to execution and result use. Retain the intended result shape (array, first row, optional row, or mutation metadata), transaction instance, plugins, and execution options unless the requested change requires otherwise. A builder-returning helper should remain a builder-returning helper when the request only changes its query.

### Diagnose type errors in order

1. **Schema types:** compare table/column names and read/insert/update types, including `Generated`, `ColumnType`, `Insertable`, and `Updateable`. Check driver-returned numeric, date, and JSON values separately.
2. **Reference scope:** check tables and aliases visible at the failing callback, correlated subqueries, CTE outputs, and outer-join nullability. Prefer callback-local `eb.fn` when function arguments need the current query scope.
3. **Expression types:** distinguish values from references; check scalar subquery cardinality, operators, CASE branches, aggregate nullability, and explicitly typed raw fragments.
4. **Result types:** check selected aliases, `$if` optional fields, `returning`, execution method, helper annotations, and the final consumer. For excessive type instantiation, consult the [official recipe](https://kysely.dev/docs/recipes/excessively-deep-types) and version fixes before suggesting `$assertType` with a structurally equal result type.

Ask for missing evidence instead of claiming an inferred schema or driver type is verified. Do not suppress the cause with `any`, a cast, or `sql<T>`. Type annotations do not convert runtime values; see the [official type explanation](https://kysely.dev/docs/recipes/data-types).

## 5. Explain the result and verification

Provide the requested code or diagnosis, material assumptions (especially version/dialect/schema), the reason for meaningful changes, and what was actually verified. Match the amount of explanation to the request.

Distinguish **query construction**, **SQL compilation**, and **database execution**: a builder constructs a query; `.compile()` produces SQL and parameters; `.execute*()` or `db.executeQuery()` uses the configured driver. Compilation is not proof of server acceptance or correct returned data. See [building and execution](https://kysely.dev/docs/recipes/splitting-query-building-and-execution).

When verification is performed, compare SQL structure and parameter binding as well as result types/shape against the request. Report documentation review, type checking, compilation, and real execution separately; do not imply unperformed checks passed.

## Maintaining version references

Keep the six topic references reusable. Add a separate `references/kysely-<major>.<minor>.md` for a subsequently supported minor release, then link it from this entry point. For patches in the same series, update that file's reviewed patch, date, sources, and relevant differences. Preserve the initial review baseline and distinguish changes that apply only after a particular patch. Do not create historical version files retroactively; consult official evidence for one-off older-version requests.
