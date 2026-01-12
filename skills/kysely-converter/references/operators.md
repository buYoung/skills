# Kysely Operators Reference

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
| `BETWEEN` | `'between'` |
| `BETWEEN SYMMETRIC` | `'between symmetric'` |
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
| SQL | Kysely | 비고 |
|-----|--------|------|
| `REGEXP` | `'regexp'` | |
| `RLIKE` | `'regexp'` | `REGEXP`의 동의어 |
| `<=>` (null-safe equal) | `'<=>'` | |
| `!<` | `'!<'` | |
| `!>` | `'!>'` | |

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
| `!!` | `'!!'` | PostgreSQL boolean 테스트 |

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
.where('age', 'between', [18, 65])
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

## Raw SQL Required
다음 연산자들은 Kysely에서 직접 지원하지 않으며 `sql` 템플릿 태그를 사용해야 합니다:

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
| `NOT BETWEEN` | BETWEEN 부정 |
| `NOT BETWEEN SYMMETRIC` | BETWEEN SYMMETRIC 부정 (PostgreSQL) |
| `ALL` | 배열/서브쿼리 전체 비교 |

### Raw SQL Example
```ts
import { sql } from 'kysely'

// NOT BETWEEN
.where(sql`${sql.ref('age')} NOT BETWEEN ${18} AND ${65}`)
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
.where(sql`BINARY ${sql.ref('name')} = ${'John'}`)
```
```sql
WHERE BINARY `name` = 'John'
```

```ts
// SIMILAR TO (PostgreSQL)
.where(sql`${sql.ref('name')} SIMILAR TO ${'%(John|Jane)%'}`)
```
```sql
WHERE "name" SIMILAR TO '%(John|Jane)%'
```

```ts
// OVERLAPS (PostgreSQL)
.where(sql`(${sql.ref('start_date')}, ${sql.ref('end_date')}) OVERLAPS (${startDate}, ${endDate})`)
```
```sql
WHERE ("start_date", "end_date") OVERLAPS ('2024-01-01', '2024-12-31')
```
