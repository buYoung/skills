# Kysely Operators Reference

## When to use

Use when translating predicates or expressions, fixing operator errors, or deciding whether raw SQL is necessary.

## Example prerequisites

Examples are independent patterns, not one shared schema or a standalone program. Assume `db` is a configured `Kysely<Database>` with the referenced tables/columns; import `sql` from `kysely` where used. Adapt application inputs and types to the actual schema. SQL blocks show semantic SQL, often with inline values for readability, not captured `.compile()` output. Check the [version reference](kysely-0.29.md) and the target database before using dialect-specific syntax. See [schema and value types](insert.md#schema-and-value-types) for the shared type contract.

## Contents

- [Choosing methods and binding values](#choosing-methods-and-binding-values)
- [Comparison Operators](#comparison-operators)
- [Arithmetic Operators](#arithmetic-operators)
- [JSON Operators](#json-operators)
- [Unary Operators](#unary-operators)
- [Logical Operators](#logical-operators)
- [Usage Examples](#usage-examples)
- [Dialect Differences](#dialect-differences)
- [Array/Subquery Operators](#arraysubquery-operators)
- [Raw SQL and composable alternatives](#raw-sql-and-composable-alternatives)

## Choosing methods and binding values

The operator tables describe syntax mapping, not universal database support. `where(lhs, op, rhs)` and `eb(lhs, op, rhs)` accept binary operators; BETWEEN takes three operands and uses `eb.between(expr, start, end)` or `eb.betweenSymmetric(...)`. A two-element array in a binary comparison does not create the BETWEEN bounds. See [ExpressionBuilder](https://kysely-org.github.io/kysely-apidoc/interfaces/ExpressionBuilder.html) and [ComparisonOperator](https://kysely-org.github.io/kysely-apidoc/types/ComparisonOperator.html).

Use `whereRef`/`onRef` or `eb.ref` for column-to-column comparisons. A normal right-hand string is a value. In `sql` templates, interpolate data as parameters; `sql.val`/`eb.val` are value expressions. `sql.lit` embeds a literal and should be reserved for deliberate trusted constants. Raw text and dynamic identifiers need validation; prefer known schema references. A standalone raw predicate passed to WHERE needs a boolean SQL type, such as `sql<boolean>`. See [Sql](https://kysely-org.github.io/kysely-apidoc/interfaces/Sql.html).

Maintain boolean grouping and SQL NULL semantics. Use IS NULL/IS NOT NULL for null tests. NOT IN can become unknown when its list/subquery contains NULL. Decide the intended behavior for empty IN lists before emitting database-specific SQL. Reuse these patterns in [SELECT](select.md), [UPDATE](update.md), and [DELETE](delete.md).

## Comparison Operators
| SQL | Kysely |
|-----|--------|
| `=` | `'='` |
| `==` | `'=='` |
| `!=` or `<>` | `'!='` or `'<>'` |
| `>` | `'>'` |
| `>=` | `'>='` |
| `<` | `'<'` |
| `<=` | `'<='` |
| `IN` | `'in'` |
| `NOT IN` | `'not in'` |
| `IS` | `'is'` |
| `IS NOT` | `'is not'` |
| `LIKE` | `'like'` |
| `NOT LIKE` | `'not like'` |
| `MATCH` | `'match'` |
| `BETWEEN` | `eb.between(expr, start, end)` |
| `BETWEEN SYMMETRIC` | `eb.betweenSymmetric(expr, start, end)` |
| `IS DISTINCT FROM` | `'is distinct from'` |
| `IS NOT DISTINCT FROM` | `'is not distinct from'` |

### PostgreSQL Specific
| SQL | Kysely |
|-----|--------|
| `ILIKE` | `'ilike'` |
| `NOT ILIKE` | `'not ilike'` |
| `~` (regex match) | `'~'` |
| `~*` (case-insensitive regex) | `'~*'` |
| `!~` (not regex match) | `'!~'` |
| `!~*` (case-insensitive not regex) | `'!~*'` |
| `@@` (full-text search) | `'@@'` |
| `@@@` | `'@@@'` |
| `@>` (contains) | `'@>'` |
| `<@` (contained by) | `'<@'` |
| `^@` (starts with) | `'^@'` |
| `&&` (overlap) | `'&&'` |
| `?` (key exists) | `'?'` |
| `?&` (all keys exist) | `'?&'` |
| `?\|` (any key exists) | `'?\|'` |
| `<->` (distance) | `'<->'` |

### MySQL Specific

`!<` and `!>` are not MySQL comparison operators; use `>=` and `<=` for those intents. `!!` is not a portable unary boolean test. Kysely accepting an operator token does not establish its meaning for a particular database. See [MySQL comparisons](https://dev.mysql.com/doc/refman/8.0/en/comparison-operators.html).

| SQL | Kysely | 비고 |
|-----|--------|------|
| `REGEXP` | `'regexp'` | |
| `RLIKE` | `'regexp'` | `REGEXP`의 동의어 |
| `<=>` (null-safe equal) | `'<=>'` | |

## Arithmetic Operators
| SQL | Kysely | 비고 |
|-----|--------|------|
| `+` | `'+'` | |
| `-` | `'-'` | |
| `*` | `'*'` | |
| `/` | `'/'` | |
| `%` (modulo) | `'%'` | `MOD`와 동일 |
| `^` | `'^'` | **PostgreSQL**: power, **MySQL**: bitwise XOR |
| `&` (bitwise AND) | `'&'` | |
| `\|` (bitwise OR) | `'\|'` | |
| `#` (bitwise XOR) | `'#'` | PostgreSQL only |
| `<<` (left shift) | `'<<'` | |
| `>>` (right shift) | `'>>'` | |
| `\|\|` (concat) | `'\|\|'` | **PostgreSQL**: 문자열/배열/JSONB 연결 |

## JSON Operators
| SQL | Kysely | 비고 |
|-----|--------|------|
| `->` (get JSON element) | `'->'` | |
| `->>` (get JSON element as text) | `'->>'` | |
| `->$` (JSON path) | `'->$'` | MySQL JSON path syntax |
| `->>$` (JSON path as text) | `'->>$'` | MySQL JSON path unquoting |

### JSON Path (for eb.ref)
```ts
// PostgreSQL JSON path
eb.ref('column', '->').key('field').at(0)
```
```sql
"column"->'field'->0
```

```ts
// MySQL JSON path
eb.ref('column', '->$').key('field').at('last')
```
```sql
`column`->'$.field[last]'
```

## Unary Operators
| SQL | Kysely | 비고 |
|-----|--------|------|
| `EXISTS` | `'exists'` | `eb.exists()` |
| `NOT EXISTS` | `'not exists'` | |
| `NOT` | `'not'` | `eb.not()` |
| `-` (negative) | `'-'` | `eb.neg()` |


## Logical Operators

### AND
```ts
// Chained where (implicit AND)
.where('status', '=', 'active')
.where('type', '=', 'user')

// Explicit AND with expression builder
.where((eb) => eb.and([
  eb('status', '=', 'active'),
  eb('type', '=', 'user')
]))
```
```sql
WHERE "status" = 'active' AND "type" = 'user'
```

### OR
```ts
.where((eb) => eb.or([
  eb('status', '=', 'active'),
  eb('status', '=', 'pending')
]))
```
```sql
WHERE ("status" = 'active' OR "status" = 'pending')
```

### Combined AND/OR
```ts
.where((eb) =>
  eb.or([
    eb.and([
      eb('status', '=', 'active'),
      eb('type', '=', 'a')
    ]),
    eb.and([
      eb('status', '=', 'pending'),
      eb('type', '=', 'b')
    ])
  ])
)
```
```sql
WHERE (("status" = 'active' AND "type" = 'a') OR ("status" = 'pending' AND "type" = 'b'))
```

## Usage Examples

### Basic Comparison
```ts
.where('age', '>', 18)
.where('status', '=', 'active')
.where('name', 'like', '%john%')
```
```sql
WHERE "age" > 18 AND "status" = 'active' AND "name" LIKE '%john%'
```

### NULL Checks
```ts
.where('deleted_at', 'is', null)
.where('name', 'is not', null)
```
```sql
WHERE "deleted_at" IS NULL AND "name" IS NOT NULL
```

### IN / NOT IN
```ts
.where('id', 'in', [1, 2, 3])
.where('status', 'not in', ['deleted', 'archived'])
```
```sql
WHERE "id" IN (1, 2, 3) AND "status" NOT IN ('deleted', 'archived')
```

### BETWEEN
```ts
.where((eb) => eb.between('age', 18, 65))
```
```sql
WHERE "age" BETWEEN 18 AND 65
```

### Column to Column (whereRef)
```ts
.whereRef('updated_at', '>', 'created_at')
.whereRef('pet.owner_id', '=', 'person.id')
```
```sql
WHERE "updated_at" > "created_at" AND "pet"."owner_id" = "person"."id"
```

### Negated BETWEEN without raw SQL
```ts
.where((eb) => eb.not(eb.between('age', 18, 65)))
```

### Arithmetic in SET
```ts
.set((eb) => ({
  age: eb('age', '+', 1),
  score: eb('score', '*', 2)
}))
```
```sql
SET "age" = "age" + 1, "score" = "score" * 2
```

## Dialect Differences

### MySQL
- Uses backticks for identifiers: \`table\`.\`column\`
- `REGEXP` for regex matching
- `<=>` for null-safe equality comparison

### PostgreSQL
- Uses double quotes for identifiers: "table"."column"
- `ILIKE` for case-insensitive LIKE
- `~`, `~*`, `!~`, `!~*` for regex operations
- `@@` for full-text search
- `@>`, `<@`, `&&` for array/JSON operations
- `||` for string/array/JSONB concatenation

## Array/Subquery Operators

### ANY / SOME
```ts
// PostgreSQL: value = ANY(array_column)
db.selectFrom('person')
  .selectAll()
  .where((eb) => eb(
    eb.val('Jen'),
    '=',
    eb.fn.any('nicknames')  // nicknames is string[] column
  ))
```
```sql
SELECT * FROM "person" WHERE 'Jen' = ANY("nicknames")
```

```ts
// With subquery
db.selectFrom('person')
  .selectAll()
  .where((eb) => eb(
    eb.val('dog'),
    '=',
    eb.fn.any(
      eb.selectFrom('pet')
        .select('species')
        .whereRef('owner_id', '=', 'person.id')
    )
  ))
```
```sql
SELECT * FROM "person" 
WHERE 'dog' = ANY(SELECT "species" FROM "pet" WHERE "owner_id" = "person"."id")
```

## Raw SQL and composable alternatives

Use raw SQL when the selected API cannot express the required syntax. Negated predicates can often be composed with `eb.not(...)`; raw SQL is not mandatory for every item below.

### MySQL
| SQL | 설명 |
|-----|------|
| `NOT REGEXP` / `NOT RLIKE` | 정규식 불일치 |
| `DIV` | 정수 나눗셈 |
| `XOR` | 논리적 XOR |
| `SOUNDS LIKE` | 발음 유사성 비교 |
| `BINARY` | 대소문자 구분 비교를 위한 바이너리 캐스팅 |

### PostgreSQL
| SQL | 설명 |
|-----|------|
| `SIMILAR TO` | SQL 표준 정규식 패턴 매칭 |
| `NOT SIMILAR TO` | SIMILAR TO 부정 |
| `#>` | JSON 경로로 JSON 객체 접근 |
| `#>>` | JSON 경로로 텍스트 접근 |
| `#-` | JSON 경로 삭제 |
| `OVERLAPS` | 날짜/시간 범위 겹침 |

### Common
| SQL | 설명 |
|-----|------|
| `NOT BETWEEN` | `eb.not(eb.between(...))` or raw SQL |
| `NOT BETWEEN SYMMETRIC` | `eb.not(eb.betweenSymmetric(...))` (PostgreSQL) |
| `ALL` | 배열/서브쿼리 전체 비교 |

### Raw SQL Example
```ts
import { sql } from 'kysely'

// NOT BETWEEN
.where(sql<boolean>`${sql.ref('age')} NOT BETWEEN ${18} AND ${65}`)
```
```sql
WHERE "age" NOT BETWEEN 18 AND 65
```

```ts
// DIV (MySQL)
.select(sql<number>`${sql.ref('amount')} DIV 3`.as('quotient'))
```
```sql
SELECT `amount` DIV 3 AS `quotient`
```

```ts
// BINARY (MySQL) - 대소문자 구분 비교
.where(sql<boolean>`BINARY ${sql.ref('name')} = ${'John'}`)
```
```sql
WHERE BINARY `name` = 'John'
```

```ts
// SIMILAR TO (PostgreSQL)
.where(sql<boolean>`${sql.ref('name')} SIMILAR TO ${'%(John|Jane)%'}`)
```
```sql
WHERE "name" SIMILAR TO '%(John|Jane)%'
```

```ts
// OVERLAPS (PostgreSQL)
.where(sql<boolean>`(${sql.ref('start_date')}, ${sql.ref('end_date')}) OVERLAPS (${startDate}, ${endDate})`)
```
```sql
WHERE ("start_date", "end_date") OVERLAPS ('2024-01-01', '2024-12-31')
```
