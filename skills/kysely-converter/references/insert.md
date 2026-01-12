# Kysely INSERT Reference

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
```sql
INSERT INTO person (first_name, last_name, middle_name, age)
VALUES ('Jennifer', CONCAT('Ani', 'ston'), first_name, (SELECT AVG(age) FROM person))
```
```ts
db.insertInto('person')
  .values(({ ref, selectFrom, fn }) => ({
    first_name: 'Jennifer',
    last_name: sql<string>`CONCAT(${'Ani'}, ${'ston'})`,
    middle_name: ref('first_name'),
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
  .onDuplicateKeyUpdate({ updated_at: new Date().toISOString() })
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
