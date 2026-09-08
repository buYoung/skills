# Kysely UPDATE Reference

## When to use

Use for UPDATE conversion, assignment changes, update refactoring, and input/result type diagnosis.

## Example prerequisites

Examples are independent patterns, not one shared schema or a standalone program. Assume `db` is a configured `Kysely<Database>` with the referenced tables/columns; import `sql` from `kysely` where used. Adapt application inputs and types to the actual schema. SQL blocks show semantic SQL, often with inline values for readability, not captured `.compile()` output. Check the [version reference](kysely-0.29.md) and the target database before using dialect-specific syntax. See [schema and value types](insert.md#schema-and-value-types) for the shared type contract.

## Contents

- [Assignments and result contract](#assignments-and-result-contract)
- [Dialect and cardinality boundaries](#dialect-and-cardinality-boundaries)
- [Basic UPDATE](#basic-update)
- [Update Single Row](#update-single-row)
- [Update with Expression](#update-with-expression)
- [Update with Subquery](#update-with-subquery)
- [Update with Column Reference](#update-with-column-reference)
- [Update with Multiple Expressions](#update-with-multiple-expressions)
- [Update with set(column, value) Syntax](#update-with-setcolumn-value-syntax)
- [UPDATE with RETURNING (PostgreSQL)](#update-with-returning-postgresql)
- [WHERE Conditions](#where-conditions)
- [UPDATE with FROM (PostgreSQL)](#update-with-from-postgresql)
- [UPDATE with JOIN (PostgreSQL)](#update-with-join-postgresql)
- [UPDATE Multiple Tables (MySQL)](#update-multiple-tables-mysql)
- [UPDATE with LIMIT (MySQL)](#update-with-limit-mysql)
- [UPDATE with ORDER BY + LIMIT (MySQL)](#update-with-order-by--limit-mysql)
- [WITH CTE + UPDATE](#with-cte--update)
- [Raw SQL in SET](#raw-sql-in-set)
- [Update with JSON Path (PostgreSQL)](#update-with-json-path-postgresql)
- [Conditional Update ($if)](#conditional-update-if)
- [Clear WHERE Clause](#clear-where-clause)
- [Dialect Differences](#dialect-differences)

## Assignments and result contract

Derive `PersonUpdate` from `Updateable<Database['person']>` and check the update slot of `ColumnType`; read types are not necessarily writable types. See [schema and value types](insert.md#schema-and-value-types) for `Generated`, `Insertable`, and driver representation.

In `.set({ middle_name: 'first_name' })`, the right side is a string value. Use `eb.ref('first_name')` for the existing column, or `eb('age', '+', 1)` for arithmetic. A scalar subquery must return at most one row and compatible values; no matching row can produce NULL. LIMIT 1 alone does not specify which row is chosen.

Without RETURNING/OUTPUT, `.execute()` returns `UpdateResult[]`, and `.executeTakeFirst()` returns metadata with `numUpdatedRows` (bigint), not an updated entity. With RETURNING, selected fields define the rows and zero matches can yield no row. `executeTakeFirstOrThrow()` without RETURNING does not prove a row was updated: inspect the count. Conditional RETURNING changes the consumer contract. See [UpdateQueryBuilder](https://kysely-org.github.io/kysely-apidoc/classes/UpdateQueryBuilder.html).

Keep the target filter, transaction instance, execution options, and caller expectations attached to the changed query. Replacing the DB-side clock with an application timestamp or changing a column reference to a bound string changes semantics.

## Dialect and cardinality boundaries

MySQL ORDER BY/LIMIT forms here are single-table updates; they cannot be attached to multi-table updates. Matched rows and actually changed rows can differ with driver flags, so do not interpret every count as changed data. See [MySQL UPDATE](https://dev.mysql.com/doc/refman/8.0/en/update.html).

For PostgreSQL UPDATE FROM, ensure the joined relation selects at most one source row per target, or the chosen update value can be indeterminate. RETURNING and PostgreSQL's JSONB subscripting examples need matching server/type support. The `||` concatenation example is PostgreSQL SQL, not a portable MySQL expression. See [PostgreSQL UPDATE](https://www.postgresql.org/docs/18/sql-update.html). Read [operators](operators.md) for shared predicates and [INSERT result guidance](insert.md#input-and-result-contract) for RETURNING dialect boundaries.

## Basic UPDATE
```sql
UPDATE person SET first_name = 'Jennifer', last_name = 'Aniston' WHERE id = 1
```
```ts
db.updateTable('person')
  .set({
    first_name: 'Jennifer',
    last_name: 'Aniston'
  })
  .where('id', '=', 1)
  .execute()
```

## Update Single Row
```sql
UPDATE person SET first_name = 'Jennifer' WHERE id = 1
```
```ts
const result = await db
  .updateTable('person')
  .set({ first_name: 'Jennifer' })
  .where('id', '=', 1)
  .executeTakeFirst()

console.log(result.numUpdatedRows)
```

## Update with Expression
```sql
UPDATE person SET age = age + 1 WHERE id = 1
```
```ts
db.updateTable('person')
  .set((eb) => ({
    age: eb('age', '+', 1)
  }))
  .where('id', '=', 1)
  .execute()
```

## Update with Subquery
```sql
UPDATE person SET first_name = (SELECT name FROM pet LIMIT 1) WHERE id = 1
```
```ts
db.updateTable('person')
  .set((eb) => ({
    first_name: eb.selectFrom('pet').select('name').limit(1)
  }))
  .where('id', '=', 1)
  .execute()
```

## Update with Column Reference
```sql
UPDATE person SET middle_name = first_name WHERE id = 1
```
```ts
db.updateTable('person')
  .set((eb) => ({
    middle_name: eb.ref('first_name')
  }))
  .where('id', '=', 1)
  .execute()
```

## Update with Multiple Expressions
```sql
UPDATE person SET
  first_name = (SELECT name FROM pet LIMIT 1),
  middle_name = first_name,
  age = age + 1,
  last_name = 'Ani' || 'ston'
WHERE id = 1
```
```ts
db.updateTable('person')
  .set(({ selectFrom, ref, eb }) => ({
    first_name: selectFrom('pet').select('name').limit(1),
    middle_name: ref('first_name'),
    age: eb('age', '+', 1),
    last_name: sql<string>`${'Ani'} || ${'ston'}`
  }))
  .where('id', '=', 1)
  .execute()
```

## Update with set(column, value) Syntax
```ts
db.updateTable('person')
  .set('first_name', 'Foo')
  .set('last_name', 'Bar')
  .where('id', '=', 1)
  .execute()
```

## UPDATE with RETURNING (PostgreSQL)
```sql
UPDATE person SET first_name = 'Jennifer' WHERE id = 1 RETURNING id, first_name
```
```ts
const result = await db
  .updateTable('person')
  .set({ first_name: 'Jennifer' })
  .where('id', '=', 1)
  .returning(['id', 'first_name'])
  .executeTakeFirstOrThrow()
```

### RETURNING All Columns
```sql
UPDATE person SET first_name = 'Jennifer' WHERE id = 1 RETURNING *
```
```ts
db.updateTable('person')
  .set({ first_name: 'Jennifer' })
  .where('id', '=', 1)
  .returningAll()
  .executeTakeFirstOrThrow()
```

## WHERE Conditions

### Simple Comparison
```sql
UPDATE person SET status = 'inactive' WHERE status = 'active'
```
```ts
db.updateTable('person')
  .set({ status: 'inactive' })
  .where('status', '=', 'active')
  .execute()
```

### Multiple Conditions
```sql
UPDATE person SET status = 'inactive' WHERE status = 'active' AND age > 18
```
```ts
db.updateTable('person')
  .set({ status: 'inactive' })
  .where('status', '=', 'active')
  .where('age', '>', 18)
  .execute()
```

### IN Operator
```sql
UPDATE person SET status = 'inactive' WHERE id IN (1, 2, 3)
```
```ts
db.updateTable('person')
  .set({ status: 'inactive' })
  .where('id', 'in', [1, 2, 3])
  .execute()
```

### Complex WHERE (OR/AND)
```sql
UPDATE person SET status = 'reviewed'
WHERE (status = 'pending' AND type = 'a') OR (status = 'draft' AND type = 'b')
```
```ts
db.updateTable('person')
  .set({ status: 'reviewed' })
  .where((eb) =>
    eb.or([
      eb.and([
        eb('status', '=', 'pending'),
        eb('type', '=', 'a')
      ]),
      eb.and([
        eb('status', '=', 'draft'),
        eb('type', '=', 'b')
      ])
    ])
  )
  .execute()
```

### Column to Column Comparison (whereRef)
```sql
UPDATE person SET status = 'synced' WHERE updated_at > synced_at
```
```ts
db.updateTable('person')
  .set({ status: 'synced' })
  .whereRef('updated_at', '>', 'synced_at')
  .execute()
```

## UPDATE with FROM (PostgreSQL)
```sql
UPDATE person SET first_name = pet.name
FROM pet
WHERE pet.owner_id = person.id
```
```ts
db.updateTable('person')
  .from('pet')
  .set((eb) => ({
    first_name: eb.ref('pet.name')
  }))
  .whereRef('pet.owner_id', '=', 'person.id')
  .execute()
```

## UPDATE with JOIN (PostgreSQL)
```sql
UPDATE person SET first_name = pet.name
FROM pet
INNER JOIN toy ON toy.pet_id = pet.id
WHERE pet.owner_id = person.id
```
```ts
db.updateTable('person')
  .from('pet')
  .innerJoin('toy', 'toy.pet_id', 'pet.id')
  .set((eb) => ({
    first_name: eb.ref('pet.name')
  }))
  .whereRef('pet.owner_id', '=', 'person.id')
  .execute()
```

## UPDATE Multiple Tables (MySQL)
```sql
UPDATE person, pet
SET person.first_name = 'Updated person', pet.name = 'Updated doggo'
WHERE person.id = pet.owner_id AND person.id = 1
```
```ts
db.updateTable(['person', 'pet'])
  .set('person.first_name', 'Updated person')
  .set('pet.name', 'Updated doggo')
  .whereRef('person.id', '=', 'pet.owner_id')
  .where('person.id', '=', 1)
  .execute()
```

## UPDATE with LIMIT (MySQL)
```sql
UPDATE person SET first_name = 'Foo' LIMIT 2
```
```ts
db.updateTable('person')
  .set({ first_name: 'Foo' })
  .limit(2)
  .execute()
```

## UPDATE with ORDER BY + LIMIT (MySQL)
```sql
UPDATE person SET status = 'processed'
ORDER BY created_at ASC
LIMIT 10
```
```ts
db.updateTable('person')
  .set({ status: 'processed' })
  .orderBy('created_at', 'asc')
  .limit(10)
  .execute()
```

## WITH CTE + UPDATE
```sql
WITH old_records AS (
  SELECT id FROM person WHERE created_at < '2020-01-01'
)
UPDATE person SET status = 'archived'
WHERE id IN (SELECT id FROM old_records)
```
```ts
db.with('old_records', (db) => db
    .selectFrom('person')
    .where('created_at', '<', '2020-01-01')
    .select('id')
  )
  .updateTable('person')
  .set({ status: 'archived' })
  .where('id', 'in', (eb) => eb.selectFrom('old_records').select('id'))
  .execute()
```

## Raw SQL in SET
```ts
import { sql } from 'kysely'

db.updateTable('person')
  .set({
    updated_at: sql`NOW()`,
    counter: sql`counter + 1`,
    name: sql`UPPER(name)`
  })
  .where('id', '=', 1)
  .execute()
```

## Update with JSON Path (PostgreSQL)
```ts
import { sql } from 'kysely'

db.updateTable('person')
  .set(sql<string>`address['postalCode']`, (eb) => eb.val('61710'))
  .where('id', '=', 1)
  .execute()
```

## Conditional Update ($if)
```ts
async function updatePerson(id: number, data: PersonUpdate, returnResult: boolean) {
  return await db
    .updateTable('person')
    .set(data)
    .where('id', '=', id)
    .$if(returnResult, (qb) => qb.returningAll())
    .execute()
}
```

## Clear WHERE Clause
```ts
db.updateTable('person')
  .set({ status: 'inactive' })
  .where('id', '=', 1)
  .clearWhere()  // Removes the WHERE clause
  .where('id', '=', 2)  // Add new condition
  .execute()
```


## Dialect Differences

### MySQL
- Uses backticks for identifiers: \`table\`.\`column\`
- Supports `UPDATE ... LIMIT`
- Supports `UPDATE ... ORDER BY ... LIMIT`
- Supports multi-table UPDATE with comma-separated tables
- No `RETURNING` clause - `numUpdatedRows` available in result

### PostgreSQL
- Uses double quotes for identifiers: "table"."column"
- Supports `UPDATE ... FROM` for joining tables
- Supports `UPDATE ... RETURNING` clause
- Does not support `LIMIT` in UPDATE
