# Kysely DELETE Reference

## When to use

Use for DELETE conversion or modification, joined deletion, and affected-row versus returned-row diagnosis.

## Example prerequisites

Examples are independent patterns, not one shared schema or a standalone program. Assume `db` is a configured `Kysely<Database>` with the referenced tables/columns; import `sql` from `kysely` where used. Adapt application inputs and types to the actual schema. SQL blocks show semantic SQL, often with inline values for readability, not captured `.compile()` output. Check the [version reference](kysely-0.29.md) and the target database before using dialect-specific syntax. See [schema and value types](insert.md#schema-and-value-types) for the shared type contract.

## Contents

- [Predicates and result contract](#predicates-and-result-contract)
- [Dialect boundaries](#dialect-boundaries)
- [Basic DELETE](#basic-delete)
- [Delete with Result](#delete-with-result)
- [DELETE with RETURNING (PostgreSQL)](#delete-with-returning-postgresql)
- [WHERE Conditions](#where-conditions)
- [DELETE with USING (PostgreSQL)](#delete-with-using-postgresql)
- [DELETE with JOIN (MySQL)](#delete-with-join-mysql)
- [DELETE with LIMIT (MySQL)](#delete-with-limit-mysql)
- [DELETE with ORDER BY + LIMIT (MySQL)](#delete-with-order-by--limit-mysql)
- [WITH CTE + DELETE](#with-cte--delete)
- [Conditional Delete ($if)](#conditional-delete-if)
- [Clear WHERE Clause](#clear-where-clause)
- [Clear LIMIT Clause](#clear-limit-clause)
- [Dialect Differences](#dialect-differences)

## Predicates and result contract

Use the [shared schema types](insert.md#schema-and-value-types) to understand filter and returned column values; `Insertable`/`Updateable` are write-object types, not DELETE payloads. A literal right-hand string is data; use `whereRef` for column comparisons. Read [operators](operators.md) for parentheses, NULL, and subquery predicates. NOT IN with a NULL-containing input is not generally interchangeable with NOT EXISTS.

Without RETURNING/OUTPUT, `.execute()` returns `DeleteResult[]`; `.executeTakeFirst()` returns metadata with `numDeletedRows` (bigint). With supported RETURNING, results are selected row objects and zero matches can yield an empty array. `executeTakeFirstOrThrow()` without RETURNING does not assert a nonzero deletion count. Conditional RETURNING requires the consumer to handle metadata and row paths. See [DeleteQueryBuilder](https://kysely-org.github.io/kysely-apidoc/classes/DeleteQueryBuilder.html).

Trace the deletion predicate through helper construction to execution. `clearWhere()` removes previous restrictions and `clearLimit()` removes a bound; their examples demonstrate rebuilding behavior, not equivalent refactors. Preserve the requested target rows, transaction instance, options, and return shape.

## Dialect boundaries

PostgreSQL USING joins determine qualifying target rows; RETURNING from a USING table does not mean that table was deleted. See [PostgreSQL DELETE](https://www.postgresql.org/docs/18/sql-delete.html). RETURNING support differs by engine; see [INSERT result guidance](insert.md#input-and-result-contract).

MySQL DELETE ORDER BY/LIMIT applies to single-table forms, not the multi-table USING/JOIN form. The LEFT JOIN example's WHERE predicate on `person` removes unmatched rows; moving it to ON would change the deletion set. See [MySQL DELETE](https://dev.mysql.com/doc/refman/8.0/en/delete.html).

## Basic DELETE
```sql
DELETE FROM person WHERE id = 1
```
```ts
db.deleteFrom('person')
  .where('id', '=', 1)
  .execute()
```

## Delete with Result
```sql
DELETE FROM person WHERE id = 1
```
```ts
const result = await db
  .deleteFrom('person')
  .where('id', '=', 1)
  .executeTakeFirst()

console.log(result.numDeletedRows)
```

## DELETE with RETURNING (PostgreSQL)
```sql
DELETE FROM person WHERE id = 1 RETURNING id, first_name
```
```ts
const deleted = await db
  .deleteFrom('person')
  .where('id', '=', 1)
  .returning(['id', 'first_name'])
  .executeTakeFirstOrThrow()
```

### RETURNING All Columns
```sql
DELETE FROM person WHERE id = 1 RETURNING *
```
```ts
db.deleteFrom('person')
  .where('id', '=', 1)
  .returningAll()
  .executeTakeFirstOrThrow()
```

### RETURNING from Specific Table
```sql
DELETE FROM toy USING pet, person
WHERE toy.pet_id = pet.id AND pet.owner_id = person.id AND person.first_name = 'Bob'
RETURNING pet.*
```
```ts
db.deleteFrom('toy')
  .using(['pet', 'person'])
  .whereRef('toy.pet_id', '=', 'pet.id')
  .whereRef('pet.owner_id', '=', 'person.id')
  .where('person.first_name', '=', 'Bob')
  .returningAll('pet')
  .execute()
```

## WHERE Conditions

### Simple Comparison
```sql
DELETE FROM person WHERE status = 'inactive'
```
```ts
db.deleteFrom('person')
  .where('status', '=', 'inactive')
  .execute()
```

### Multiple Conditions
```sql
DELETE FROM person WHERE status = 'inactive' AND age > 18
```
```ts
db.deleteFrom('person')
  .where('status', '=', 'inactive')
  .where('age', '>', 18)
  .execute()
```

### IN Operator
```sql
DELETE FROM person WHERE id IN (1, 2, 3)
```
```ts
db.deleteFrom('person')
  .where('id', 'in', [1, 2, 3])
  .execute()
```

### NOT IN Operator
```sql
DELETE FROM person WHERE id NOT IN (1, 2, 3)
```
```ts
db.deleteFrom('person')
  .where('id', 'not in', [1, 2, 3])
  .execute()
```

### IS NULL / IS NOT NULL
```sql
DELETE FROM person WHERE deleted_at IS NOT NULL
```
```ts
db.deleteFrom('person')
  .where('deleted_at', 'is not', null)
  .execute()
```

### LIKE
```sql
DELETE FROM person WHERE name LIKE 'test%'
```
```ts
db.deleteFrom('person')
  .where('name', 'like', 'test%')
  .execute()
```

### Complex WHERE (OR/AND)
```sql
DELETE FROM person
WHERE (status = 'deleted' AND type = 'a') OR (status = 'archived' AND type = 'b')
```
```ts
db.deleteFrom('person')
  .where((eb) =>
    eb.or([
      eb.and([
        eb('status', '=', 'deleted'),
        eb('type', '=', 'a')
      ]),
      eb.and([
        eb('status', '=', 'archived'),
        eb('type', '=', 'b')
      ])
    ])
  )
  .execute()
```

### Column to Column Comparison (whereRef)
```sql
DELETE FROM person WHERE expires_at < created_at
```
```ts
db.deleteFrom('person')
  .whereRef('expires_at', '<', 'created_at')
  .execute()
```

### Subquery in WHERE
```sql
DELETE FROM person WHERE id IN (SELECT owner_id FROM pet WHERE species = 'cat')
```
```ts
db.deleteFrom('person')
  .where('id', 'in', (eb) => eb
    .selectFrom('pet')
    .where('species', '=', 'cat')
    .select('owner_id')
  )
  .execute()
```

### EXISTS Subquery
```sql
DELETE FROM person WHERE EXISTS (SELECT 1 AS one FROM pet WHERE pet.owner_id = person.id)
```
```ts
db.deleteFrom('person')
  .where((eb) =>
    eb.exists(
      eb.selectFrom('pet')
        .whereRef('pet.owner_id', '=', 'person.id')
        .select(sql.lit(1).as('one'))
    )
  )
  .execute()
```

## DELETE with USING (PostgreSQL)
```sql
DELETE FROM pet USING person
WHERE pet.owner_id = person.id AND person.first_name = 'Bob'
```
```ts
db.deleteFrom('pet')
  .using('person')
  .whereRef('pet.owner_id', '=', 'person.id')
  .where('person.first_name', '=', 'Bob')
  .execute()
```

### USING with Multiple Tables
```sql
DELETE FROM toy USING pet, person
WHERE toy.pet_id = pet.id AND pet.owner_id = person.id AND person.first_name = 'Bob'
```
```ts
db.deleteFrom('toy')
  .using(['pet', 'person'])
  .whereRef('toy.pet_id', '=', 'pet.id')
  .whereRef('pet.owner_id', '=', 'person.id')
  .where('person.first_name', '=', 'Bob')
  .execute()
```

## DELETE with JOIN (MySQL)
```sql
DELETE FROM pet USING pet
LEFT JOIN person ON person.id = pet.owner_id
WHERE person.first_name = 'Bob'
```
```ts
db.deleteFrom('pet')
  .using('pet')
  .leftJoin('person', 'person.id', 'pet.owner_id')
  .where('person.first_name', '=', 'Bob')
  .execute()
```

### INNER JOIN
```ts
db.deleteFrom('pet')
  .using('pet')
  .innerJoin('person', 'person.id', 'pet.owner_id')
  .where('person.first_name', '=', 'Bob')
  .execute()
```

## DELETE with LIMIT (MySQL)
```sql
DELETE FROM person WHERE status = 'inactive' LIMIT 10
```
```ts
db.deleteFrom('person')
  .where('status', '=', 'inactive')
  .limit(10)
  .execute()
```

## DELETE with ORDER BY + LIMIT (MySQL)
```sql
DELETE FROM person ORDER BY created_at ASC LIMIT 5
```
```ts
db.deleteFrom('person')
  .orderBy('created_at', 'asc')
  .limit(5)
  .execute()
```

## WITH CTE + DELETE
```sql
WITH old_records AS (
  SELECT id FROM person WHERE created_at < '2020-01-01'
)
DELETE FROM person WHERE id IN (SELECT id FROM old_records)
```
```ts
db.with('old_records', (db) => db
    .selectFrom('person')
    .where('created_at', '<', '2020-01-01')
    .select('id')
  )
  .deleteFrom('person')
  .where('id', 'in', (eb) => eb.selectFrom('old_records').select('id'))
  .execute()
```

## Conditional Delete ($if)
```ts
async function deletePerson(id: number, returnDeleted: boolean) {
  return await db
    .deleteFrom('person')
    .where('id', '=', id)
    .$if(returnDeleted, (qb) => qb.returningAll())
    .execute()
}
```

## Clear WHERE Clause
```ts
db.deleteFrom('person')
  .where('id', '=', 1)
  .clearWhere()  // Removes the WHERE clause
  .where('id', '=', 2)  // Add new condition
  .execute()
```

## Clear LIMIT Clause
```ts
db.deleteFrom('person')
  .where('status', '=', 'inactive')
  .limit(10)
  .clearLimit()  // Removes the LIMIT clause
  .execute()
```


## Dialect Differences

### MySQL
- Uses backticks for identifiers: \`table\`.\`column\`
- Supports `DELETE ... LIMIT`
- Supports `DELETE ... ORDER BY ... LIMIT`
- For JOIN in DELETE, use `USING table` + JOIN clause
- No `RETURNING` clause - `numDeletedRows` available in result

### PostgreSQL
- Uses double quotes for identifiers: "table"."column"
- Supports `DELETE ... USING` for joining tables
- Supports `DELETE ... RETURNING` clause
- Does not support `LIMIT` in DELETE
