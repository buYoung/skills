# Kysely SELECT Reference

## When to use

Use for SQL-to-SELECT conversion, new reads, query refactoring, or errors involving selection, reference scope, and result inference.

## Example prerequisites

Examples are independent patterns, not one shared schema or a standalone program. Assume `db` is a configured `Kysely<Database>` with the referenced tables/columns; import `sql` from `kysely` where used. Adapt application inputs and types to the actual schema. SQL blocks show semantic SQL, often with inline values for readability, not captured `.compile()` output. Check the [version reference](kysely-0.29.md) and the target database before using dialect-specific syntax. See [schema and value types](insert.md#schema-and-value-types) for the shared type contract.

## Contents

- [Selection semantics and scope](#selection-semantics-and-scope)
- [Conditional builders and result types](#conditional-builders-and-result-types)
- [Basic SELECT](#basic-select)
- [Select Single Column](#select-single-column)
- [Select with Table Prefix](#select-with-table-prefix)
- [Select All Columns](#select-all-columns)
- [Select All from Specific Table](#select-all-from-specific-table)
- [Aliases](#aliases)
- [DISTINCT](#distinct)
- [DISTINCT ON (PostgreSQL only)](#distinct-on-postgresql-only)
- [WHERE Conditions](#where-conditions)
- [JOIN](#join)
- [GROUP BY](#group-by)
- [HAVING](#having)
- [ORDER BY](#order-by)
- [LIMIT / OFFSET](#limit--offset)
- [Aggregate Functions](#aggregate-functions)
- [Window Functions](#window-functions)
- [CASE WHEN](#case-when)
- [WITH (CTE)](#with-cte)
- [UNION / INTERSECT / EXCEPT](#union--intersect--except)
- [Subquery in SELECT](#subquery-in-select)
- [FOR UPDATE / FOR SHARE (Locking)](#for-update--for-share-locking)
- [Raw SQL](#raw-sql)
- [Dynamic Column Reference](#dynamic-column-reference)
- [Conditional Query Building ($if)](#conditional-query-building-if)
- [WITH RECURSIVE (Recursive CTE)](#with-recursive-recursive-cte)
- [CTE Materialization (PostgreSQL)](#cte-materialization-postgresql)
- [INTERSECT ALL / EXCEPT ALL](#intersect-all--except-all)
- [Data Type Casting (CAST)](#data-type-casting-cast)
- [JSON Data Processing](#json-data-processing)
- [Full Text Search](#full-text-search)
- [BETWEEN SYMMETRIC (PostgreSQL)](#between-symmetric-postgresql)
- [Advanced Grouping (Raw SQL Required)](#advanced-grouping-raw-sql-required)
- [Window Frame Clause (Raw SQL Required)](#window-frame-clause-raw-sql-required)
- [DBMS-Specific Features (Raw SQL Required)](#dbms-specific-features-raw-sql-required)
- [Dialect Differences](#dialect-differences)

## Selection semantics and scope

Use an alias consistently after introducing it. Derived tables and CTEs expose their selected columns, not every column of their source tables. A correlated subquery may use the outer query's visible references; a derived table in FROM/JOIN that references an outer row needs a supported lateral form. Prefer the callback-local expression builder to keep these scopes explicit. See [expressions](https://kysely.dev/docs/recipes/expressions).

An outer join makes the unmatched side nullable, even when the table declares a column non-null. Filtering that side in WHERE can discard unmatched rows; putting the predicate in ON has a different meaning. A one-to-many join multiplies rows. Avoid adding DISTINCT to hide that multiplication. For new queries, select explicit aliases when joined columns have duplicate names; for conversions, explain any collision in the original output contract.

GROUP BY changes row cardinality; HAVING filters groups, whereas WHERE filters input rows. COUNT(column) excludes NULL; COUNT(*) counts rows. Other aggregates can return NULL for empty input, and numeric output depends on the driver. DISTINCT ON needs appropriate ORDER BY to choose a predictable representative. LIMIT/OFFSET without a complete order may select unstable pages; discuss a tie-breaker for new queries without silently changing source SQL. UNION removes duplicates; UNION ALL retains them. See [PostgreSQL SELECT semantics](https://www.postgresql.org/docs/18/sql-select.html).

## Conditional builders and result types

Builders are immutable: retain the returned builder when adding a conditional filter. An ignored `query.where(...)` does not update `query`. For a filter-only branch, reassignment preserves the builder's output shape:

```ts
let query = db.selectFrom('person').select(['id', 'first_name'])
if (minimumAge !== undefined) {
  query = query.where('age', '>=', minimumAge)
}
```

Here `minimumAge` is an application input of type `number | undefined`. An explicit undefined check preserves a valid zero value.

Adding selections or joins can change the inferred type: assigning a richer builder back to an earlier variable can lose that information. `$if` makes newly selected fields optional; optional presence is distinct from SQL NULL. The existing `getPeople` example therefore has an optional `age` field, whose value can also be nullable if the schema says so. Use separate returned branches when a precise union of result shapes is needed. See [conditional selects](https://kysely.dev/docs/recipes/conditional-selects).

## Basic SELECT
```sql
SELECT id, name FROM person
```
```ts
db.selectFrom('person')
  .select(['id', 'name'])
  .execute()
```

## Select Single Column
```sql
SELECT id FROM person WHERE first_name = 'Arnold'
```
```ts
db.selectFrom('person')
  .select('id')
  .where('first_name', '=', 'Arnold')
  .execute()
```

## Select with Table Prefix
```sql
SELECT person.id FROM person, pet
```
```ts
db.selectFrom(['person', 'pet'])
  .select('person.id')
  .execute()
```

## Select All Columns
```sql
SELECT * FROM person
```
```ts
db.selectFrom('person')
  .selectAll()
  .execute()
```

## Select All from Specific Table
```sql
SELECT person.* FROM person
```
```ts
db.selectFrom('person')
  .selectAll('person')
  .execute()
```

## Aliases
```sql
SELECT first_name AS fn, p.last_name AS ln FROM person AS p
```
```ts
db.selectFrom('person as p')
  .select(['first_name as fn', 'p.last_name as ln'])
  .execute()
```

## DISTINCT
```sql
SELECT DISTINCT first_name FROM person
```
```ts
db.selectFrom('person')
  .select('first_name')
  .distinct()
  .execute()
```

## DISTINCT ON (PostgreSQL only)
```sql
SELECT DISTINCT ON (person.id) person.* FROM person
INNER JOIN pet ON pet.owner_id = person.id
WHERE pet.name = 'Doggo'
```
```ts
db.selectFrom('person')
  .innerJoin('pet', 'pet.owner_id', 'person.id')
  .where('pet.name', '=', 'Doggo')
  .distinctOn('person.id')
  .selectAll('person')
  .execute()
```

## WHERE Conditions

### Simple Comparison
```sql
WHERE status = 'active'
```
```ts
.where('status', '=', 'active')
```

### Multiple AND Conditions
```sql
WHERE status = 'active' AND type = 'user'
```
```ts
.where('status', '=', 'active')
.where('type', '=', 'user')
```

### IN Operator
```sql
WHERE id IN (1, 2, 3)
```
```ts
.where('id', 'in', [1, 2, 3])
```

### NOT IN Operator
```sql
WHERE id NOT IN (1, 2, 3)
```
```ts
.where('id', 'not in', [1, 2, 3])
```

### IS NULL / IS NOT NULL
```sql
WHERE deleted_at IS NULL AND name IS NOT NULL
```
```ts
.where('deleted_at', 'is', null)
.where('name', 'is not', null)
```

### LIKE / NOT LIKE
```sql
WHERE name LIKE '%john%'
```
```ts
.where('name', 'like', '%john%')
```

### ILIKE (PostgreSQL only)
```sql
WHERE name ILIKE '%john%'
```
```ts
.where('name', 'ilike', '%john%')
```

### BETWEEN

Use the dedicated expression method; see [operators](operators.md#choosing-methods-and-binding-values).

```sql
WHERE age BETWEEN 18 AND 65
```
```ts
.where((eb) => eb.between('age', 18, 65))
```

### Column to Column Comparison (whereRef)
```sql
WHERE log.created_at >= enrollment.start_dt
```
```ts
.whereRef('log.created_at', '>=', 'enrollment.start_dt')
```

### Complex WHERE (OR/AND)
```sql
WHERE (status = 'active' AND type = 'a') OR (status = 'pending' AND type = 'b')
```
```ts
.where((eb) =>
  eb.or([
    eb.and([
      eb('status', '=', 'active'),
      eb('type', '=', 'a'),
    ]),
    eb.and([
      eb('status', '=', 'pending'),
      eb('type', '=', 'b'),
    ]),
  ])
)
```

### EXISTS Subquery

Alias a raw selection to satisfy [SelectExpression](https://kysely-org.github.io/kysely-apidoc/types/SelectExpression.html). The alias inside EXISTS does not change its truth value.

```sql
WHERE EXISTS (SELECT 1 AS one FROM pet WHERE pet.owner_id = person.id)
```
```ts
.where((eb) =>
  eb.exists(
    eb.selectFrom('pet')
      .whereRef('pet.owner_id', '=', 'person.id')
      .select(sql.lit(1).as('one'))
  )
)
```


## JOIN

Choose only join forms supported by the target engine: for example, MySQL has no native FULL OUTER JOIN (see [MySQL JOIN syntax](https://dev.mysql.com/doc/refman/8.0/en/join.html)). LATERAL derived tables require MySQL 8.0.14+ and have correlation restrictions; see [MySQL LATERAL](https://dev.mysql.com/doc/refman/8.0/en/lateral-derived-tables.html).

### INNER JOIN
```sql
SELECT * FROM person INNER JOIN pet ON pet.owner_id = person.id
```
```ts
db.selectFrom('person')
  .innerJoin('pet', 'pet.owner_id', 'person.id')
  .selectAll()
  .execute()
```

### LEFT JOIN
```sql
SELECT * FROM person LEFT JOIN pet ON pet.owner_id = person.id
```
```ts
db.selectFrom('person')
  .leftJoin('pet', 'pet.owner_id', 'person.id')
  .selectAll()
  .execute()
```

### RIGHT JOIN
```sql
SELECT * FROM person RIGHT JOIN pet ON pet.owner_id = person.id
```
```ts
db.selectFrom('person')
  .rightJoin('pet', 'pet.owner_id', 'person.id')
  .selectAll()
  .execute()
```

### FULL JOIN
```sql
SELECT * FROM person FULL JOIN pet ON pet.owner_id = person.id
```
```ts
db.selectFrom('person')
  .fullJoin('pet', 'pet.owner_id', 'person.id')
  .selectAll()
  .execute()
```

### CROSS JOIN
```sql
SELECT * FROM person CROSS JOIN pet
```
```ts
db.selectFrom('person')
  .crossJoin('pet')
  .selectAll()
  .execute()
```

### Complex JOIN Conditions
```sql
SELECT * FROM person
INNER JOIN pet ON pet.owner_id = person.id AND pet.name = 'Doggo'
```
```ts
db.selectFrom('person')
  .innerJoin('pet', (join) => join
    .onRef('pet.owner_id', '=', 'person.id')
    .on('pet.name', '=', 'Doggo')
  )
  .selectAll()
  .execute()
```

### JOIN with Subquery
```sql
SELECT * FROM person
INNER JOIN (SELECT owner_id, name FROM pet WHERE name = 'Doggo') AS doggos
ON doggos.owner_id = person.id
```
```ts
db.selectFrom('person')
  .innerJoin(
    (eb) => eb
      .selectFrom('pet')
      .select(['owner_id', 'name'])
      .where('name', '=', 'Doggo')
      .as('doggos'),
    (join) => join.onRef('doggos.owner_id', '=', 'person.id')
  )
  .selectAll()
  .execute()
```

### LATERAL JOIN (PostgreSQL, MySQL)
```sql
SELECT person.first_name, p.name FROM person
INNER JOIN LATERAL (SELECT name FROM pet WHERE pet.owner_id = person.id) AS p ON true
```
```ts
db.selectFrom('person')
  .innerJoinLateral(
    (eb) => eb
      .selectFrom('pet')
      .select('name')
      .whereRef('pet.owner_id', '=', 'person.id')
      .as('p'),
    (join) => join.onTrue()
  )
  .select(['first_name', 'p.name'])
  .execute()
```

## GROUP BY
```sql
SELECT type, COUNT(*) AS cnt FROM items GROUP BY type
```
```ts
db.selectFrom('items')
  .select(['type', (eb) => eb.fn.countAll().as('cnt')])
  .groupBy('type')
  .execute()
```

### Multiple GROUP BY
```sql
SELECT first_name, last_name, COUNT(*) FROM person GROUP BY first_name, last_name
```
```ts
db.selectFrom('person')
  .select(['first_name', 'last_name', (eb) => eb.fn.countAll().as('count')])
  .groupBy(['first_name', 'last_name'])
  .execute()
```

## HAVING
```sql
SELECT type, COUNT(*) FROM items GROUP BY type HAVING COUNT(*) > 5
```
```ts
db.selectFrom('items')
  .select(['type', (eb) => eb.fn.countAll().as('cnt')])
  .groupBy('type')
  .having((eb) => eb(eb.fn.countAll(), '>', 5))
  .execute()
```

## ORDER BY
```sql
ORDER BY created_at DESC, id ASC
```
```ts
.orderBy('created_at', 'desc')
.orderBy('id', 'asc')
```

### ORDER BY with NULLS
```sql
ORDER BY created_at DESC NULLS LAST
```
```ts
.orderBy('created_at', (ob) => ob.desc().nullsLast())
```

## LIMIT / OFFSET
```sql
SELECT * FROM person LIMIT 10 OFFSET 20
```
```ts
db.selectFrom('person')
  .selectAll()
  .limit(10)
  .offset(20)
  .execute()
```

## Aggregate Functions
```sql
SELECT COUNT(*), SUM(amount), AVG(price), MIN(age), MAX(age) FROM orders
```
```ts
db.selectFrom('orders')
  .select((eb) => [
    eb.fn.countAll().as('count'),
    eb.fn.sum('amount').as('total'),
    eb.fn.avg('price').as('avg_price'),
    eb.fn.min('age').as('min_age'),
    eb.fn.max('age').as('max_age'),
  ])
  .execute()
```

### COUNT with Column
```sql
SELECT COUNT(id) FROM person
```
```ts
db.selectFrom('person')
  .select((eb) => eb.fn.count('id').as('count'))
  .execute()
```

## Window Functions

### ROW_NUMBER
```sql
SELECT *, ROW_NUMBER() OVER (PARTITION BY type ORDER BY created_at DESC) AS rn FROM items
```
```ts
db.selectFrom('items')
  .selectAll()
  .select((eb) =>
    eb.fn
      .agg<number>('ROW_NUMBER')
      .over((ob) => ob.partitionBy('type').orderBy('created_at', 'desc'))
      .as('rn')
  )
  .execute()
```

### COUNT/SUM/AVG OVER
```sql
SELECT *, COUNT(1) OVER (PARTITION BY type) AS cnt FROM items
```
```ts
db.selectFrom('items')
  .selectAll()
  .select((eb) =>
    eb.fn.count(sql.lit(1))
      .over((ob) => ob.partitionBy('type'))
      .as('cnt')
  )
  .execute()
```

### Multiple PARTITION BY
```sql
PARTITION BY enrollment_id, monitoring_type
```
```ts
.over((ob) => ob.partitionBy(['enrollment_id', 'monitoring_type']))
```

## CASE WHEN
```sql
CASE
  WHEN type = 'a' THEN col1
  WHEN type = 'b' THEN col2
  ELSE col3
END AS result
```
```ts
eb.case()
  .when('type', '=', 'a')
  .then(eb.ref('col1'))
  .when('type', '=', 'b')
  .then(eb.ref('col2'))
  .else(eb.ref('col3'))
  .end()
  .as('result')
```

### Simple CASE
```sql
CASE status WHEN 'active' THEN 1 WHEN 'inactive' THEN 0 ELSE -1 END
```
```ts
eb.case('status')
  .when('active')
  .then(1)
  .when('inactive')
  .then(0)
  .else(-1)
  .end()
```

## WITH (CTE)
```sql
WITH filtered AS (SELECT id FROM person WHERE age > 18)
SELECT * FROM filtered
```
```ts
db.with('filtered', (db) =>
    db.selectFrom('person')
      .select('id')
      .where('age', '>', 18)
  )
  .selectFrom('filtered')
  .selectAll()
  .execute()
```

### Multiple CTEs
```sql
WITH cte1 AS (SELECT id FROM t1),
     cte2 AS (SELECT id FROM cte1)
SELECT * FROM cte2
```
```ts
db.with('cte1', (db) => db.selectFrom('t1').select('id'))
  .with('cte2', (db) => db.selectFrom('cte1').select('id'))
  .selectFrom('cte2')
  .selectAll()
  .execute()
```

## UNION / INTERSECT / EXCEPT
```sql
SELECT id, first_name AS name FROM person
UNION
SELECT id, name FROM pet
```
```ts
db.selectFrom('person')
  .select(['id', 'first_name as name'])
  .union(db.selectFrom('pet').select(['id', 'name']))
  .execute()
```

### UNION ALL
```sql
SELECT id FROM person UNION ALL SELECT id FROM pet
```
```ts
db.selectFrom('person')
  .select('id')
  .unionAll(db.selectFrom('pet').select('id'))
  .execute()
```

### INTERSECT
```ts
db.selectFrom('person')
  .select('id')
  .intersect(db.selectFrom('pet').select('id'))
  .execute()
```

### EXCEPT
```ts
db.selectFrom('person')
  .select('id')
  .except(db.selectFrom('pet').select('id'))
  .execute()
```

## Subquery in SELECT
```sql
SELECT name, (SELECT COUNT(*) FROM pet WHERE pet.owner_id = person.id) AS pet_count
FROM person
```
```ts
db.selectFrom('person')
  .select((eb) => [
    'name',
    eb.selectFrom('pet')
      .whereRef('pet.owner_id', '=', 'person.id')
      .select((eb2) => eb2.fn.countAll().as('count'))
      .as('pet_count')
  ])
  .execute()
```

## FOR UPDATE / FOR SHARE (Locking)
```sql
SELECT * FROM person WHERE id = 1 FOR UPDATE
```
```ts
db.selectFrom('person')
  .selectAll()
  .where('id', '=', 1)
  .forUpdate()
  .execute()
```

### FOR SHARE
```ts
db.selectFrom('person')
  .selectAll()
  .forShare()
  .execute()
```

### SKIP LOCKED
```ts
db.selectFrom('person')
  .selectAll()
  .forUpdate()
  .skipLocked()
  .execute()
```

### NOWAIT
```ts
db.selectFrom('person')
  .selectAll()
  .forUpdate()
  .noWait()
  .execute()
```

## Raw SQL
```ts
import { sql } from 'kysely'

// Raw expression in select
db.selectFrom('person')
  .select([
    'id',
    sql<string>`CONCAT(first_name, ' ', last_name)`.as('full_name')
  ])
  .execute()
```

### Literal Value
```ts
sql.lit(1)
sql.lit('active')
```

## Dynamic Column Reference
```ts
const { ref } = db.dynamic
const columnName = 'first_name'

db.selectFrom('person')
  .select(ref(columnName))
  .execute()
```

## Conditional Query Building ($if)
```ts
async function getPeople(includeAge: boolean) {
  return await db
    .selectFrom('person')
    .select(['id', 'first_name'])
    .$if(includeAge, (qb) => qb.select('age'))
    .execute()
}
```

## WITH RECURSIVE (Recursive CTE)
```sql
WITH RECURSIVE subordinates AS (
  SELECT id, name, manager_id FROM employees WHERE id = 1
  UNION ALL
  SELECT e.id, e.name, e.manager_id 
  FROM employees e
  INNER JOIN subordinates s ON s.id = e.manager_id
)
SELECT * FROM subordinates
```
```ts
db.withRecursive('subordinates', (db) =>
    db.selectFrom('employees')
      .select(['id', 'name', 'manager_id'])
      .where('id', '=', 1)
      .unionAll(
        db.selectFrom('employees as e')
          .innerJoin('subordinates as s', 's.id', 'e.manager_id')
          .select(['e.id', 'e.name', 'e.manager_id'])
      )
  )
  .selectFrom('subordinates')
  .selectAll()
  .execute()
```

## CTE Materialization (PostgreSQL)
```sql
WITH filtered AS MATERIALIZED (SELECT id FROM person WHERE age > 18)
SELECT * FROM filtered
```
```ts
db.with(
    (cte) => cte('filtered').materialized(),
    (db) => db.selectFrom('person')
      .select('id')
      .where('age', '>', 18)
  )
  .selectFrom('filtered')
  .selectAll()
  .execute()
```

### NOT MATERIALIZED
```ts
db.with(
    (cte) => cte('filtered').notMaterialized(),
    (db) => db.selectFrom('person')
      .select('id')
      .where('age', '>', 18)
  )
  .selectFrom('filtered')
  .selectAll()
  .execute()
```

## INTERSECT ALL / EXCEPT ALL
### INTERSECT ALL
```sql
SELECT id FROM person INTERSECT ALL SELECT id FROM pet
```
```ts
db.selectFrom('person')
  .select('id')
  .intersectAll(db.selectFrom('pet').select('id'))
  .execute()
```

### EXCEPT ALL
```sql
SELECT id FROM person EXCEPT ALL SELECT id FROM pet
```
```ts
db.selectFrom('person')
  .select('id')
  .exceptAll(db.selectFrom('pet').select('id'))
  .execute()
```

## Data Type Casting (CAST)
```sql
SELECT CAST(age AS integer) AS age FROM person
```
```ts
db.selectFrom('person')
  .select((eb) => [
    eb.cast<number>('age', 'integer').as('age')
  ])
  .execute()
```

### PostgreSQL Shorthand (::) - Raw SQL
```sql
SELECT age::integer FROM person
```
```ts
import { sql } from 'kysely'

db.selectFrom('person')
  .select(sql<number>`age::integer`.as('age'))
  .execute()
```

## JSON Data Processing

The `->`/`->>` chains below are PostgreSQL-oriented. For MySQL JSON paths, use the `->$`/`->>$` builder operators; see [JSON operators](operators.md#json-operators). The `$` is Kysely path-builder syntax, not a literal database operator.

### JSON Extraction (->)
```sql
-- PostgreSQL: address->'city'
-- MySQL: JSON_EXTRACT(address, '$.city')
SELECT address->'city' AS city FROM person
```
```ts
db.selectFrom('person')
  .select((eb) => 
    eb.ref('address', '->').key('city').as('city')
  )
  .execute()
```

### JSON Text Extraction (->>)
```sql
-- PostgreSQL: address->>'city'
-- MySQL: JSON_UNQUOTE(JSON_EXTRACT(address, '$.city'))
SELECT address->>'city' AS city FROM person
```
```ts
db.selectFrom('person')
  .select((eb) => 
    eb.ref('address', '->>').key('city').as('city')
  )
  .execute()
```

### Nested JSON Access
```sql
SELECT profile->'address'->'city' AS city FROM person
```
```ts
db.selectFrom('person')
  .select((eb) => 
    eb.ref('profile', '->').key('address').key('city').as('city')
  )
  .execute()
```

### JSON Array Access
```sql
SELECT nicknames->0 AS first_nickname FROM person
```
```ts
db.selectFrom('person')
  .select((eb) => 
    eb.ref('nicknames', '->').at(0).as('first_nickname')
  )
  .execute()
```

### JSON Aggregation

Use `eb.fn.jsonAgg` for a PostgreSQL whole-table row reference. Generic function string arguments normally mean columns, not whole rows. See [FunctionModule](https://kysely-org.github.io/kysely-apidoc/interfaces/FunctionModule.html#jsonagg). MySQL output type still depends on the driver/plugins.
```sql
-- PostgreSQL: json_agg(pet)
-- MySQL: JSON_ARRAYAGG(pet.name)
```
```ts
// PostgreSQL
db.selectFrom('person')
  .innerJoin('pet', 'pet.owner_id', 'person.id')
  .select((eb) => [
    'person.id',
    eb.fn.jsonAgg('pet').as('pets')
  ])
  .groupBy('person.id')
  .execute()

// MySQL
db.selectFrom('person')
  .innerJoin('pet', 'pet.owner_id', 'person.id')
  .select((eb) => [
    'person.id',
    eb.fn.agg<string>('JSON_ARRAYAGG', ['pet.name']).as('pet_names')
  ])
  .groupBy('person.id')
  .execute()
```

## Full Text Search

### PostgreSQL (@@)
```sql
SELECT * FROM documents WHERE to_tsvector('english', content) @@ to_tsquery('search')
```
```ts
import { sql } from 'kysely'

db.selectFrom('documents')
  .selectAll()
  .where(
    sql`to_tsvector('english', ${sql.ref('content')})`,
    '@@',
    sql`to_tsquery(${sql.lit('search')})`
  )
  .execute()
```

### MySQL (MATCH AGAINST)
```sql
SELECT * FROM articles WHERE MATCH(title, body) AGAINST('search terms')
```
```ts
import { sql } from 'kysely'

db.selectFrom('articles')
  .selectAll()
  .where(
    sql`MATCH(title, body) AGAINST(${sql.lit('search terms')})`,
    '>',
    0
  )
  .execute()
```

## BETWEEN SYMMETRIC (PostgreSQL)
```sql
SELECT * FROM person WHERE age BETWEEN SYMMETRIC 60 AND 18
```
```ts
db.selectFrom('person')
  .selectAll()
  .where((eb) => eb.betweenSymmetric('age', 60, 18))
  .execute()
```

## Advanced Grouping (Raw SQL Required)

### ROLLUP
> **Note**: Kysely에서 직접 지원하지 않음 - Raw SQL 사용
```sql
SELECT type, region, SUM(amount) FROM sales GROUP BY ROLLUP(type, region)
```
```ts
import { sql } from 'kysely'

db.selectFrom('sales')
  .select(['type', 'region', (eb) => eb.fn.sum('amount').as('total')])
  .groupBy(sql`ROLLUP(type, region)`)
  .execute()
```

### CUBE
> **Note**: Kysely에서 직접 지원하지 않음 - Raw SQL 사용
```sql
SELECT type, region, SUM(amount) FROM sales GROUP BY CUBE(type, region)
```
```ts
import { sql } from 'kysely'

db.selectFrom('sales')
  .select(['type', 'region', (eb) => eb.fn.sum('amount').as('total')])
  .groupBy(sql`CUBE(type, region)`)
  .execute()
```

### GROUPING SETS
> **Note**: Kysely에서 직접 지원하지 않음 - Raw SQL 사용
```sql
SELECT type, region, SUM(amount) FROM sales 
GROUP BY GROUPING SETS ((type), (region), ())
```
```ts
import { sql } from 'kysely'

db.selectFrom('sales')
  .select(['type', 'region', (eb) => eb.fn.sum('amount').as('total')])
  .groupBy(sql`GROUPING SETS ((type), (region), ())`)
  .execute()
```

## Window Frame Clause (Raw SQL Required)

Read [window frame semantics](window_function.md#window-semantics-and-example-assumptions) before choosing ROWS or RANGE. These explicit frames are not interchangeable with the default OVER frame. The interval example below uses PostgreSQL syntax.

### ROWS BETWEEN
> **Note**: Kysely에서 프레임 절 직접 지원하지 않음 - Raw SQL 사용
```sql
SELECT id, amount, 
  SUM(amount) OVER (ORDER BY id ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS running_sum
FROM transactions
```
```ts
import { sql } from 'kysely'

db.selectFrom('transactions')
  .select([
    'id',
    'amount',
    sql<number>`SUM(amount) OVER (ORDER BY id ROWS BETWEEN 1 PRECEDING AND CURRENT ROW)`.as('running_sum')
  ])
  .execute()
```

### RANGE BETWEEN
```sql
SELECT id, amount,
  AVG(amount) OVER (ORDER BY created_at RANGE BETWEEN INTERVAL '1 day' PRECEDING AND CURRENT ROW)
FROM transactions
```
```ts
import { sql } from 'kysely'

db.selectFrom('transactions')
  .select([
    'id',
    'amount',
    sql<number>`AVG(amount) OVER (ORDER BY created_at RANGE BETWEEN INTERVAL '1 day' PRECEDING AND CURRENT ROW)`.as('avg_amount')
  ])
  .execute()
```

## DBMS-Specific Features (Raw SQL Required)

### MySQL Index Hints
> **Note**: Kysely에서 직접 지원하지 않음 - Raw SQL 사용
```sql
SELECT * FROM person USE INDEX (idx_name) WHERE name = 'John'
```
```ts
import { sql } from 'kysely'

sql`SELECT * FROM person USE INDEX (idx_name) WHERE name = ${sql.lit('John')}`
  .execute(db)
```

### PostgreSQL TABLESAMPLE
> **Note**: Kysely에서 직접 지원하지 않음 - Raw SQL 사용
```sql
SELECT * FROM large_table TABLESAMPLE BERNOULLI(10)
```
```ts
import { sql } from 'kysely'

sql`SELECT * FROM large_table TABLESAMPLE BERNOULLI(10)`
  .execute(db)
```

## Dialect Differences

### MySQL
- Uses backticks for identifiers: \`table\`.\`column\`
- `LIMIT offset, count` syntax supported
- Supports `REGEXP` operator
- JSON: use `->$` / `->>$` with the Kysely path builder; MySQL SQL uses a JSON path string.
- Full-Text: `MATCH (...) AGAINST (...)`

### PostgreSQL
- Uses double quotes for identifiers: "table"."column"
- `DISTINCT ON` supported
- `ILIKE` for case-insensitive LIKE
- `~`, `~*`, `!~`, `!~*` regex operators
- `NULLS FIRST` / `NULLS LAST` in ORDER BY
- JSON: Native `->`, `->>`, `#>`, `#>>` operators
- Full-Text: `to_tsvector`, `to_tsquery`, `@@` operator
- Type casting: `::type` shorthand (use raw SQL)
- CTE: `MATERIALIZED` / `NOT MATERIALIZED` hints supported
- `BETWEEN SYMMETRIC` supported
