# Kysely INSERT Reference

## When to use

Use for INSERT conversion or authoring, upserts, write-input type errors, and shared read/write type questions.

## Example prerequisites

Examples are independent patterns, not one shared schema or a standalone program. Assume `db` is a configured `Kysely<Database>` with the referenced tables/columns; import `sql` from `kysely` where used. Adapt application inputs and types to the actual schema. SQL blocks show semantic SQL, often with inline values for readability, not captured `.compile()` output. Check the [version reference](kysely-0.29.md) and the target database before using dialect-specific syntax. See [schema and value types](insert.md#schema-and-value-types) for the shared type contract.

## Contents

- [Schema and value types](#schema-and-value-types)
- [Input and result contract](#input-and-result-contract)
- [Basic INSERT](#basic-insert)
- [Insert Single Row](#insert-single-row)
- [Insert Multiple Rows](#insert-multiple-rows)
- [INSERT with RETURNING (PostgreSQL)](#insert-with-returning-postgresql)
- [INSERT with Expression Values](#insert-with-expression-values)
- [INSERT ... SELECT (Subquery)](#insert--select-subquery)
- [INSERT DEFAULT VALUES](#insert-default-values)
- [ON CONFLICT (PostgreSQL, SQLite)](#on-conflict-postgresql-sqlite)
- [ON DUPLICATE KEY UPDATE (MySQL)](#on-duplicate-key-update-mysql)
- [INSERT IGNORE (MySQL)](#insert-ignore-mysql)
- [INSERT OR IGNORE (SQLite)](#insert-or-ignore-sqlite)
- [INSERT OR REPLACE (SQLite)](#insert-or-replace-sqlite)
- [WITH CTE + INSERT](#with-cte--insert)
- [Raw SQL in Values](#raw-sql-in-values)
- [Conditional Insert ($if)](#conditional-insert-if)
- [Dialect Differences](#dialect-differences)

## Schema and value types

Model table columns once, then derive operation-specific object types:

| Type | Role |
| --- | --- |
| `ColumnType<Select, Insert, Update>` | Separates the read value from allowed insert/update values; `never` forbids an operation on that column. |
| `Generated<T>` | Equivalent to `ColumnType<T, T \| undefined, T>`; allows omission on insert, but does not create a database default or forbid updates. |
| `Selectable<Table>` | Extracts the table's read shape; a partial query still returns only its selected fields. |
| `Insertable<Table>` | Extracts insertion values and required/optional input keys. |
| `Updateable<Table>` | Extracts update values with optional keys; it is not the same as `Partial<Selectable<Table>>`. |

Sources: [ColumnType](https://kysely-org.github.io/kysely-apidoc/types/ColumnType.html), [Generated](https://kysely-org.github.io/kysely-apidoc/types/Generated.html), [Insertable](https://kysely-org.github.io/kysely-apidoc/types/Insertable.html), [Updateable](https://kysely-org.github.io/kysely-apidoc/types/Updateable.html).

For the examples below, `PersonInput` can be derived as `Insertable<Database['person']>`; UPDATE's `PersonUpdate` can be `Updateable<Database['person']>`. Omitted required columns must have a compatible schema/default. These plain object types do not describe every expression accepted by `.values()` or `.set()`.

TypeScript declarations do not change driver data. `sql<T>`, aggregate generics, `$castTo`, and type assertions describe assumed types; they do not parse JSON, convert strings to numbers, or validate values. Match dates, bigint/numeric values, and JSON to the actual driver and result plugins. SQL CAST changes the database expression; the resulting JavaScript representation still depends on the driver. See [data types](https://kysely.dev/docs/recipes/data-types).

## Input and result contract

A string in `.values()` is data; `eb.ref(...)` is a column reference. Do not use a reference to mean another property of the JavaScript input object. For INSERT ... SELECT, align destination columns with selected expressions by position and type.

Without RETURNING/OUTPUT, execution yields `InsertResult` metadata (`insertId` when supplied by the driver and `numInsertedOrUpdatedRows`), not inserted row objects. With supported RETURNING, selected columns define row results. `.execute()` returns an array; `.executeTakeFirst()` returns its first item; `.executeTakeFirstOrThrow()` throws if no result row exists. DO NOTHING can produce no returned row. Conditional RETURNING can switch between metadata and rows, so callers must handle both paths; `$if` is not a dialect support check. See [InsertQueryBuilder](https://kysely-org.github.io/kysely-apidoc/classes/InsertQueryBuilder.html).

RETURNING examples target PostgreSQL; SQLite supports RETURNING from 3.35.0 with limitations, including no auxiliary-table columns in UPDATE FROM. MySQL does not support these RETURNING forms; do not assume MariaDB behavior applies to MySQL. SQL Server uses OUTPUT. See [SQLite RETURNING](https://www.sqlite.org/lang_returning.html).

## Basic INSERT
```sql
INSERT INTO person (first_name, last_name, age) VALUES ('Jennifer', 'Aniston', 40)
```
```ts
db.insertInto('person')
  .values({
    first_name: 'Jennifer',
    last_name: 'Aniston',
    age: 40
  })
  .execute()
```

## Insert Single Row
```sql
INSERT INTO person (first_name, last_name, age) VALUES ('Jennifer', 'Aniston', 40)
```
```ts
const result = await db
  .insertInto('person')
  .values({
    first_name: 'Jennifer',
    last_name: 'Aniston',
    age: 40
  })
  .executeTakeFirst()

// MySQL: result.insertId contains auto-increment id
// PostgreSQL: use returning() to get inserted data
```

## Insert Multiple Rows
```sql
INSERT INTO person (first_name, last_name, age) VALUES
  ('Jennifer', 'Aniston', 40),
  ('Arnold', 'Schwarzenegger', 70)
```
```ts
db.insertInto('person')
  .values([
    { first_name: 'Jennifer', last_name: 'Aniston', age: 40 },
    { first_name: 'Arnold', last_name: 'Schwarzenegger', age: 70 }
  ])
  .execute()
```

## INSERT with RETURNING (PostgreSQL)
```sql
INSERT INTO person (first_name, last_name, age)
VALUES ('Jennifer', 'Aniston', 40)
RETURNING id, first_name
```
```ts
const result = await db
  .insertInto('person')
  .values({
    first_name: 'Jennifer',
    last_name: 'Aniston',
    age: 40
  })
  .returning(['id', 'first_name'])
  .executeTakeFirstOrThrow()
```

### RETURNING All Columns
```sql
INSERT INTO person (first_name) VALUES ('Jennifer') RETURNING *
```
```ts
db.insertInto('person')
  .values({ first_name: 'Jennifer' })
  .returningAll()
  .executeTakeFirstOrThrow()
```

### RETURNING with Alias
```sql
INSERT INTO person (first_name) VALUES ('Jennifer')
RETURNING id, first_name AS name
```
```ts
db.insertInto('person')
  .values({ first_name: 'Jennifer' })
  .returning(['id', 'first_name as name'])
  .executeTakeFirstOrThrow()
```

## INSERT with Expression Values

This PostgreSQL example repeats the bound input for `middle_name`; a target-column reference in VALUES is not a portable reference to the earlier input value. The scalar aggregate requires compatible nullable/numeric types. See [PostgreSQL INSERT](https://www.postgresql.org/docs/18/sql-insert.html). MySQL permits some earlier-column references in VALUES but restricts selecting the target table in a subquery; do not transplant this example unchanged. See [MySQL INSERT](https://dev.mysql.com/doc/refman/8.0/en/insert.html).

```sql
INSERT INTO person (first_name, last_name, middle_name, age)
VALUES ('Jennifer', CONCAT('Ani', 'ston'), 'Jennifer', (SELECT AVG(age) FROM person))
```
```ts
db.insertInto('person')
  .values(({ selectFrom, fn }) => ({
    first_name: 'Jennifer',
    last_name: sql<string>`CONCAT(${'Ani'}, ${'ston'})`,
    middle_name: 'Jennifer',
    age: selectFrom('person').select(fn.avg<number>('age').as('avg_age'))
  }))
  .execute()
```

## INSERT ... SELECT (Subquery)
```sql
INSERT INTO person (first_name, last_name, age)
SELECT name, 'Petson', 7 FROM pet
```
```ts
db.insertInto('person')
  .columns(['first_name', 'last_name', 'age'])
  .expression((eb) => eb
    .selectFrom('pet')
    .select((eb) => [
      'pet.name',
      eb.val('Petson').as('last_name'),
      eb.lit(7).as('age')
    ])
  )
  .execute()
```

## INSERT DEFAULT VALUES

This spelling applies to PostgreSQL/SQLite; it is not portable MySQL INSERT syntax. Check defaults for every omitted column.

```sql
INSERT INTO person DEFAULT VALUES
```
```ts
db.insertInto('person')
  .defaultValues()
  .execute()
```

## ON CONFLICT (PostgreSQL, SQLite)

### DO NOTHING
```sql
INSERT INTO pet (name, species, owner_id) VALUES ('Catto', 'cat', 3)
ON CONFLICT (name) DO NOTHING
```
```ts
db.insertInto('pet')
  .values({
    name: 'Catto',
    species: 'cat',
    owner_id: 3
  })
  .onConflict((oc) => oc
    .column('name')
    .doNothing()
  )
  .execute()
```

### DO UPDATE SET (Upsert)
```sql
INSERT INTO pet (name, species, owner_id) VALUES ('Catto', 'cat', 3)
ON CONFLICT (name) DO UPDATE SET species = 'hamster'
```
```ts
db.insertInto('pet')
  .values({
    name: 'Catto',
    species: 'cat',
    owner_id: 3
  })
  .onConflict((oc) => oc
    .column('name')
    .doUpdateSet({ species: 'hamster' })
  )
  .execute()
```

### ON CONFLICT with Constraint Name

This ON CONSTRAINT form is PostgreSQL-specific. Conflict columns/expressions must match a suitable unique constraint or index; SQLite does not accept the PostgreSQL constraint-name form.

```sql
INSERT INTO pet (name, species) VALUES ('Catto', 'cat')
ON CONFLICT ON CONSTRAINT pet_name_key DO UPDATE SET species = 'hamster'
```
```ts
db.insertInto('pet')
  .values({ name: 'Catto', species: 'cat' })
  .onConflict((oc) => oc
    .constraint('pet_name_key')
    .doUpdateSet({ species: 'hamster' })
  )
  .execute()
```

### ON CONFLICT with Multiple Columns
```sql
INSERT INTO pet (name, owner_id, species) VALUES ('Catto', 1, 'cat')
ON CONFLICT (name, owner_id) DO UPDATE SET species = 'hamster'
```
```ts
db.insertInto('pet')
  .values({ name: 'Catto', owner_id: 1, species: 'cat' })
  .onConflict((oc) => oc
    .columns(['name', 'owner_id'])
    .doUpdateSet({ species: 'hamster' })
  )
  .execute()
```

### ON CONFLICT with Expression
```sql
INSERT INTO pet (name, species) VALUES ('Catto', 'cat')
ON CONFLICT (lower(name)) DO UPDATE SET species = 'hamster'
```
```ts
db.insertInto('pet')
  .values({ name: 'Catto', species: 'cat' })
  .onConflict((oc) => oc
    .expression(sql<string>`lower(name)`)
    .doUpdateSet({ species: 'hamster' })
  )
  .execute()
```

### ON CONFLICT with WHERE
```sql
INSERT INTO pet (name, species) VALUES ('Catto', 'cat')
ON CONFLICT (name) DO UPDATE SET species = 'hamster'
WHERE excluded.name != 'Catto'
```
```ts
db.insertInto('pet')
  .values({ name: 'Catto', species: 'cat' })
  .onConflict((oc) => oc
    .column('name')
    .doUpdateSet({ species: 'hamster' })
    .where('excluded.name', '!=', 'Catto')
  )
  .execute()
```

### Using excluded Table (Upsert with Original Values)
```sql
INSERT INTO person (id, first_name, last_name, gender)
VALUES (1, 'John', 'Doe', 'male')
ON CONFLICT (id) DO UPDATE SET
  first_name = excluded.first_name,
  last_name = excluded.last_name
```
```ts
db.insertInto('person')
  .values({
    id: 1,
    first_name: 'John',
    last_name: 'Doe',
    gender: 'male'
  })
  .onConflict((oc) => oc
    .column('id')
    .doUpdateSet(({ ref }) => ({
      first_name: ref('excluded.first_name'),
      last_name: ref('excluded.last_name')
    }))
  )
  .execute()
```

## ON DUPLICATE KEY UPDATE (MySQL)
```sql
INSERT INTO person (id, first_name, last_name, gender)
VALUES (1, 'John', 'Doe', 'male')
ON DUPLICATE KEY UPDATE updated_at = NOW()
```
```ts
db.insertInto('person')
  .values({
    id: 1,
    first_name: 'John',
    last_name: 'Doe',
    gender: 'male'
  })
  .onDuplicateKeyUpdate({ updated_at: sql`NOW()` })
  .execute()
```

### ON DUPLICATE KEY with Expression
```ts
db.insertInto('person')
  .values({ id: 1, first_name: 'John' })
  .onDuplicateKeyUpdate((eb) => ({
    first_name: eb.ref('person.first_name'),
    updated_at: sql`NOW()`
  }))
  .execute()
```

## INSERT IGNORE (MySQL)
```sql
INSERT IGNORE INTO person (first_name, last_name) VALUES ('John', 'Doe')
```
```ts
db.insertInto('person')
  .ignore()
  .values({ first_name: 'John', last_name: 'Doe' })
  .execute()
```

## INSERT OR IGNORE (SQLite)
```sql
INSERT OR IGNORE INTO person (first_name, last_name) VALUES ('John', 'Doe')
```
```ts
db.insertInto('person')
  .orIgnore()
  .values({ first_name: 'John', last_name: 'Doe' })
  .execute()
```

## INSERT OR REPLACE (SQLite)

REPLACE may delete a conflicting row before inserting; it is not equivalent to an UPDATE upsert. See [SQLite conflict resolution](https://www.sqlite.org/lang_conflict.html).

```sql
INSERT OR REPLACE INTO person (first_name, last_name) VALUES ('John', 'Doe')
```
```ts
db.insertInto('person')
  .orReplace()
  .values({ first_name: 'John', last_name: 'Doe' })
  .execute()
```

## WITH CTE + INSERT
```sql
WITH jennifer AS (
  SELECT id, first_name FROM person WHERE first_name = 'Jennifer' LIMIT 1
)
INSERT INTO pet (owner_id, name, species)
SELECT id, first_name, 'cat' FROM jennifer
```
```ts
db.with('jennifer', (db) => db
    .selectFrom('person')
    .where('first_name', '=', 'Jennifer')
    .select(['id', 'first_name'])
    .limit(1)
  )
  .insertInto('pet')
  .columns(['owner_id', 'name', 'species'])
  .expression((eb) => eb
    .selectFrom('jennifer')
    .select(['id', 'first_name', eb.val('cat').as('species')])
  )
  .execute()
```

## Raw SQL in Values
```ts
import { sql } from 'kysely'

db.insertInto('person')
  .values({
    first_name: 'John',
    created_at: sql`NOW()`,
    uuid: sql`UUID()`
  })
  .execute()
```

## Conditional Insert ($if)
```ts
async function insertPerson(data: PersonInput, returnId: boolean) {
  return await db
    .insertInto('person')
    .values(data)
    .$if(returnId, (qb) => qb.returning('id'))
    .execute()
}
```

## Dialect Differences

### MySQL
- Uses backticks for identifiers: \`table\`.\`column\`
- `ON DUPLICATE KEY UPDATE` for upsert
- `INSERT IGNORE` for ignoring duplicate key errors
- `insertId` available in result for auto-increment columns

### PostgreSQL
- Uses double quotes for identifiers: "table"."column"
- `ON CONFLICT ... DO NOTHING / DO UPDATE` for upsert
- `RETURNING` clause for getting inserted data
- No `insertId` - use `RETURNING id` instead
