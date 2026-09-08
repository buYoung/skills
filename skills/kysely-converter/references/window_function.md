# Kysely Window Functions Reference (MySQL & PostgreSQL)

## When to use

Use for ranking, lag/lead, running or partition aggregates, frames, and top-N-per-group queries.

## Example prerequisites

Examples are independent patterns, not one shared schema or a standalone program. Assume `db` is a configured `Kysely<Database>` with the referenced tables/columns; import `sql` from `kysely` where used. Adapt application inputs and types to the actual schema. SQL blocks show semantic SQL, often with inline values for readability, not captured `.compile()` output. Check the [version reference](kysely-0.29.md) and the target database before using dialect-specific syntax. See [schema and value types](insert.md#schema-and-value-types) for the shared type contract.

## Contents

- [Window semantics and example assumptions](#window-semantics-and-example-assumptions)
- [Standard Window Functions](#standard-window-functions)
- [Basic OVER Clause](#basic-over-clause)
- [Ranking Functions](#ranking-functions)
- [Value Functions](#value-functions)
- [Aggregate Window Functions](#aggregate-window-functions)
- [Window Frame (Raw SQL Required)](#window-frame-raw-sql-required)
- [Filter Clause (PostgreSQL Only)](#filter-clause-postgresql-only)
- [WITH (CTE) + Window Function](#with-cte--window-function)
- [Dialect Specifics](#dialect-specifics)
- [Common Patterns](#common-patterns)

## Window semantics and example assumptions

Examples target PostgreSQL or MySQL 8.0+ as labeled. `eb.fn.agg` can construct a named function with OVER, but does not establish that the server supports the function or modifier combination. `number`, `Date`, and JSON generics assume matching driver output and appropriate nullability; see [schema and value types](insert.md#schema-and-value-types).

An ORDER BY inside OVER controls window calculations, not final result order. Equal sort keys are peers; ROW_NUMBER/top-N choices need a tie-breaker when deterministic individual rows are required. RANK includes ties differently from ROW_NUMBER. Use a CTE/subquery to filter a window result instead of referring to its alias in the same query's WHERE. See [SELECT](select.md) for scope and CTE patterns.

For PostgreSQL and MySQL with ORDER BY and no explicit frame, the default is RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, including peers of the current row. ROWS counts physical rows; it is not the default. Without ORDER BY, the default frame spans the partition. LAST_VALUE uses the frame, so the existing alias `lowest_salary` does not promise the partition minimum. For that intent, explicitly span the full partition. Sources: [PostgreSQL windows](https://www.postgresql.org/docs/18/functions-window.html), [MySQL frames](https://dev.mysql.com/doc/refman/8.0/en/window-functions-frames.html).

MySQL 8.0+ 및 PostgreSQL에서 지원하는 윈도우 함수의 Kysely 변환 패턴입니다.

## Standard Window Functions

| Function | SQL Syntax | Kysely Method |
|----------|------------|---------------|
| **Ranking** | | |
| Row Number | `ROW_NUMBER() OVER (...)` | `eb.fn.agg<number>('ROW_NUMBER').over(...)` |
| Rank | `RANK() OVER (...)` | `eb.fn.agg<number>('RANK').over(...)` |
| Dense Rank | `DENSE_RANK() OVER (...)` | `eb.fn.agg<number>('DENSE_RANK').over(...)` |
| Percent Rank | `PERCENT_RANK() OVER (...)` | `eb.fn.agg<number>('PERCENT_RANK').over(...)` |
| Cume Dist | `CUME_DIST() OVER (...)` | `eb.fn.agg<number>('CUME_DIST').over(...)` |
| N-Tile | `NTILE(n) OVER (...)` | `eb.fn.agg<number>('NTILE', [sql.lit(n)]).over(...)` |
| **Value** | | |
| Lag | `LAG(col, offset, default)` | `eb.fn.agg('LAG', [col, sql.lit(offset), sql.lit(default)]).over(...)` |
| Lead | `LEAD(col, offset, default)` | `eb.fn.agg('LEAD', [col, sql.lit(offset), sql.lit(default)]).over(...)` |
| First Value | `FIRST_VALUE(col)` | `eb.fn.agg('FIRST_VALUE', [col]).over(...)` |
| Last Value | `LAST_VALUE(col)` | `eb.fn.agg('LAST_VALUE', [col]).over(...)` |
| Nth Value | `NTH_VALUE(col, n)` | `eb.fn.agg('NTH_VALUE', [col, sql.lit(n)]).over(...)` |
| **Aggregate** | | |
| Average | `AVG(col) OVER (...)` | `eb.fn.avg(col).over(...)` |
| Count | `COUNT(col) OVER (...)` | `eb.fn.count(col).over(...)` |
| Max | `MAX(col) OVER (...)` | `eb.fn.max(col).over(...)` |
| Min | `MIN(col) OVER (...)` | `eb.fn.min(col).over(...)` |
| Sum | `SUM(col) OVER (...)` | `eb.fn.sum(col).over(...)` |

## Basic OVER Clause

### Empty OVER
```sql
SELECT id, AVG(salary) OVER () AS avg_salary FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'id',
    eb.fn.avg<number>('salary').over().as('avg_salary')
  ])
```

### OVER with PARTITION BY
```sql
SELECT id, department, AVG(salary) OVER (PARTITION BY department) AS dept_avg
FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'id',
    'department',
    eb.fn.avg<number>('salary')
      .over((ob) => ob.partitionBy('department'))
      .as('dept_avg')
  ])
```

### OVER with ORDER BY
```sql
SELECT id, created_at, SUM(amount) OVER (ORDER BY created_at) AS running_total
FROM transactions
```
```ts
db.selectFrom('transactions')
  .select((eb) => [
    'id',
    'created_at',
    eb.fn.sum<number>('amount')
      .over((ob) => ob.orderBy('created_at'))
      .as('running_total')
  ])
```

### OVER with PARTITION BY + ORDER BY
```sql
SELECT id, department, salary,
  RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS salary_rank
FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'id',
    'department',
    'salary',
    eb.fn.agg<number>('RANK')
      .over((ob) => ob.partitionBy('department').orderBy('salary', 'desc'))
      .as('salary_rank')
  ])
```

### Multiple PARTITION BY Columns
```sql
SELECT id, ROW_NUMBER() OVER (PARTITION BY type, status ORDER BY created_at DESC) AS rn
FROM items
```
```ts
db.selectFrom('items')
  .select((eb) => [
    'id',
    eb.fn.agg<number>('ROW_NUMBER')
      .over((ob) => 
        ob.partitionBy(['type', 'status'])
          .orderBy('created_at', 'desc')
      )
      .as('rn')
  ])
```

## Ranking Functions

### ROW_NUMBER
```sql
SELECT name, department, salary,
  ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS row_num
FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'name',
    'department',
    'salary',
    eb.fn.agg<number>('ROW_NUMBER')
      .over((ob) => ob.partitionBy('department').orderBy('salary', 'desc'))
      .as('row_num')
  ])
```

### RANK / DENSE_RANK
```sql
SELECT name, salary,
  RANK() OVER (ORDER BY salary DESC) AS rank,
  DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank
FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'name',
    'salary',
    eb.fn.agg<number>('RANK')
      .over((ob) => ob.orderBy('salary', 'desc'))
      .as('rank'),
    eb.fn.agg<number>('DENSE_RANK')
      .over((ob) => ob.orderBy('salary', 'desc'))
      .as('dense_rank')
  ])
```

### NTILE
```sql
SELECT name, salary,
  NTILE(4) OVER (ORDER BY salary DESC) AS quartile
FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'name',
    'salary',
    eb.fn.agg<number>('NTILE', [sql.lit(4)])
      .over((ob) => ob.orderBy('salary', 'desc'))
      .as('quartile')
  ])
```

## Value Functions

### LAG / LEAD
```sql
SELECT id, order_date,
  LAG(order_date, 1) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order,
  LEAD(order_date, 1) OVER (PARTITION BY customer_id ORDER BY order_date) AS next_order
FROM orders
```
```ts
db.selectFrom('orders')
  .select((eb) => [
    'id',
    'order_date',
    eb.fn.agg<Date | null>('LAG', ['order_date', sql.lit(1)])
      .over((ob) => ob.partitionBy('customer_id').orderBy('order_date'))
      .as('prev_order'),
    eb.fn.agg<Date | null>('LEAD', ['order_date', sql.lit(1)])
      .over((ob) => ob.partitionBy('customer_id').orderBy('order_date'))
      .as('next_order')
  ])
```

### LAG with Default Value
```sql
SELECT id, amount,
  LAG(amount, 1, 0) OVER (ORDER BY created_at) AS prev_amount
FROM transactions
```
```ts
db.selectFrom('transactions')
  .select((eb) => [
    'id',
    'amount',
    eb.fn.agg<number>('LAG', ['amount', sql.lit(1), sql.lit(0)])
      .over((ob) => ob.orderBy('created_at'))
      .as('prev_amount')
  ])
```

### FIRST_VALUE / LAST_VALUE
```sql
SELECT id, department, salary,
  FIRST_VALUE(salary) OVER (PARTITION BY department ORDER BY salary DESC) AS highest_salary,
  LAST_VALUE(salary) OVER (PARTITION BY department ORDER BY salary DESC) AS lowest_salary
FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'id',
    'department',
    'salary',
    eb.fn.agg<number>('FIRST_VALUE', ['salary'])
      .over((ob) => ob.partitionBy('department').orderBy('salary', 'desc'))
      .as('highest_salary'),
    eb.fn.agg<number>('LAST_VALUE', ['salary'])
      .over((ob) => ob.partitionBy('department').orderBy('salary', 'desc'))
      .as('lowest_salary')
  ])
```

### NTH_VALUE
```sql
SELECT id, department, salary,
  NTH_VALUE(salary, 2) OVER (PARTITION BY department ORDER BY salary DESC) AS second_highest
FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'id',
    'department',
    'salary',
    eb.fn.agg<number | null>('NTH_VALUE', ['salary', sql.lit(2)])
      .over((ob) => ob.partitionBy('department').orderBy('salary', 'desc'))
      .as('second_highest')
  ])
```

## Aggregate Window Functions

### Running Total
```sql
SELECT id, amount,
  SUM(amount) OVER (ORDER BY created_at) AS running_total
FROM transactions
```
```ts
db.selectFrom('transactions')
  .select((eb) => [
    'id',
    'amount',
    eb.fn.sum<number>('amount')
      .over((ob) => ob.orderBy('created_at'))
      .as('running_total')
  ])
```

### Partition Total
```sql
SELECT id, department, salary,
  SUM(salary) OVER (PARTITION BY department) AS dept_total,
  salary * 100.0 / SUM(salary) OVER (PARTITION BY department) AS pct_of_dept
FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'id',
    'department',
    'salary',
    eb.fn.sum<number>('salary')
      .over((ob) => ob.partitionBy('department'))
      .as('dept_total'),
    sql<number>`${eb.ref('salary')} * 100.0 / ${eb.fn.sum('salary').over((ob) => ob.partitionBy('department'))}`
      .as('pct_of_dept')
  ])
```

### Moving Average
```sql
SELECT id, created_at, amount,
  AVG(amount) OVER (ORDER BY created_at ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3
FROM transactions
```
```ts
// Window Frame은 raw SQL 사용
db.selectFrom('transactions')
  .select((eb) => [
    'id',
    'created_at',
    'amount',
    sql<number>`AVG(${eb.ref('amount')}) OVER (ORDER BY ${eb.ref('created_at')} ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`
      .as('moving_avg_3')
  ])
```

### COUNT with DISTINCT in Window

The following pair illustrates SQL construction only: PostgreSQL and MySQL 8.0 do not support DISTINCT inside window aggregate calls. Do not use it as executable SQL on either engine. See [PostgreSQL window-call restrictions](https://www.postgresql.org/docs/18/sql-expressions.html#SYNTAX-WINDOW-FUNCTIONS) and [MySQL restrictions](https://dev.mysql.com/doc/refman/8.0/en/window-function-restrictions.html).

```sql
SELECT id, department,
  COUNT(DISTINCT role) OVER (PARTITION BY department) AS unique_roles
FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'id',
    'department',
    eb.fn.count<number>('role')
      .distinct()
      .over((ob) => ob.partitionBy('department'))
      .as('unique_roles')
  ])
```

For this distinct-count intent, use an aggregate subquery instead. This preserves one result per employee, excludes NULL roles as COUNT(DISTINCT role) does, and treats NULL departments as one partition:

```ts
db.selectFrom('employees as e')
  .select((eb) => [
    'e.id',
    'e.department',
    eb.selectFrom('employees as d')
      .select((eb) => eb.fn.count<number>('d.role').distinct().as('count'))
      .where((eb) => eb.or([
        eb('d.department', '=', eb.ref('e.department')),
        eb.and([
          eb('d.department', 'is', null),
          eb('e.department', 'is', null)
        ])
      ]))
      .as('unique_roles')
  ])
```

## Window Frame (Raw SQL Required)

For the 0.29 baseline, use raw SQL for explicit ROWS/RANGE frames; the documented [OVER callback](https://kysely-org.github.io/kysely-apidoc/classes/AggregateFunctionBuilder.html#over) covers partitioning and ordering. Recheck the installed API for another version rather than assuming a frame method exists.

Frame bounds, interval syntax, GROUPS, and exclusions depend on the server. MySQL 8.0 does not support GROUPS or EXCLUDE; PostgreSQL's `INTERVAL '1 day'` spelling in [SELECT](select.md#window-frame-clause-raw-sql-required) is not the MySQL spelling. See [MySQL restrictions](https://dev.mysql.com/doc/refman/8.0/en/window-function-restrictions.html).

To make LAST_VALUE select the end of the entire ordered partition, specify the full frame (assuming a matching numeric driver type and a non-null salary):

```ts
db.selectFrom('employees')
  .select((eb) => [
    'id',
    sql<number>`LAST_VALUE(${eb.ref('salary')}) OVER (
      PARTITION BY ${eb.ref('department')}
      ORDER BY ${eb.ref('salary')} DESC
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )`.as('lowest_salary')
  ])
```

This is an intentional change from the default-frame example, not an equivalent translation of that source SQL.

### ROWS BETWEEN Examples
```sql
-- Explicit physical-row frame, not the default with ORDER BY
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

-- 이전 N개 행부터 현재 행까지
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW

-- 이전 N개 행부터 다음 N개 행까지
ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING

-- 파티션 전체
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
```

```ts
// Kysely에서 Window Frame 사용
db.selectFrom('transactions')
  .select((eb) => [
    'id',
    sql<number>`SUM(${eb.ref('amount')}) OVER (
      PARTITION BY ${eb.ref('type')}
      ORDER BY ${eb.ref('created_at')}
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )`.as('cumulative_sum')
  ])
```
```sql
select "id", SUM("amount") OVER (PARTITION BY "type" ORDER BY "created_at" ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as "cumulative_sum" from "transactions"
```

## Filter Clause (PostgreSQL Only)

PostgreSQL에서는 `FILTER` 절을 사용하여 조건부 집계를 할 수 있습니다.

```sql
-- PostgreSQL
SELECT id, department,
  COUNT(*) FILTER (WHERE status = 'active') OVER (PARTITION BY department) AS active_count
FROM employees
```
```ts
// PostgreSQL
db.selectFrom('employees')
  .select((eb) => [
    'id',
    'department',
    eb.fn.countAll<number>()
      .filterWhere('status', '=', 'active')
      .over((ob) => ob.partitionBy('department'))
      .as('active_count')
  ])
```

## WITH (CTE) + Window Function

```sql
WITH ranked AS (
  SELECT id, department, salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS rn
  FROM employees
)
SELECT * FROM ranked WHERE rn = 1
```
```ts
db.with('ranked', (db) =>
    db.selectFrom('employees')
      .select((eb) => [
        'id',
        'department',
        'salary',
        eb.fn.agg<number>('ROW_NUMBER')
          .over((ob) => ob.partitionBy('department').orderBy('salary', 'desc'))
          .as('rn')
      ])
  )
  .selectFrom('ranked')
  .selectAll()
  .where('rn', '=', 1)
```

## Dialect Specifics

### PostgreSQL Only Functions

| Function | Description | Example |
|----------|-------------|---------|
| `array_agg` | 값들을 배열로 집계 | `eb.fn.agg<string[]>('array_agg', ['name']).over(...)` |
| `string_agg` | 문자열을 구분자로 연결 | `sql\`string_agg(${eb.ref('name')}, ', ') OVER (...)\`` |
| `json_agg` | JSON 배열 집계 | `eb.fn.jsonAgg('pet').over(...)` |
| `bool_and` | 모든 값이 TRUE | `eb.fn.agg<boolean>('bool_and', ['is_active']).over(...)` |
| `bool_or` | 하나라도 TRUE | `eb.fn.agg<boolean>('bool_or', ['is_active']).over(...)` |

```ts
// PostgreSQL - array_agg with window function
db.selectFrom('orders')
  .select((eb) => [
    'customer_id',
    eb.fn.agg<string[]>('array_agg', ['product_name'])
      .over((ob) => ob.partitionBy('customer_id'))
      .as('products')
  ])
```
```sql
select "customer_id", array_agg("product_name") over(partition by "customer_id") as "products" from "orders"
```

### MySQL Specific Notes

- **MySQL 8.0+** 부터 표준 윈도우 함수 지원
- `JSON_ARRAYAGG`, `JSON_OBJECTAGG`는 MySQL 8.0.14부터 윈도우 함수로 사용 가능
- `GROUP_CONCAT`은 윈도우 함수로 사용 **불가** (GROUP BY 절에서만 사용)

```ts
// MySQL - JSON_ARRAYAGG as window function (8.0.14+)
db.selectFrom('orders')
  .select((eb) => [
    'customer_id',
    eb.fn.agg<string>('JSON_ARRAYAGG', ['product_name'])
      .over((ob) => ob.partitionBy('customer_id'))
      .as('products_json')
  ])
```
```sql
select `customer_id`, JSON_ARRAYAGG(`product_name`) over(partition by `customer_id`) as `products_json` from `orders`
```

## Common Patterns

### Top N per Group
```sql
-- 부서별 급여 상위 3명
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS rn
  FROM employees
)
SELECT * FROM ranked WHERE rn <= 3
```
```ts
db.with('ranked', (db) =>
    db.selectFrom('employees')
      .selectAll()
      .select((eb) => 
        eb.fn.agg<number>('ROW_NUMBER')
          .over((ob) => ob.partitionBy('department').orderBy('salary', 'desc'))
          .as('rn')
      )
  )
  .selectFrom('ranked')
  .selectAll()
  .where('rn', '<=', 3)
```

### Calculate Difference from Previous Row
```sql
SELECT id, amount,
  amount - LAG(amount, 1, 0) OVER (ORDER BY created_at) AS diff
FROM transactions
```
```ts
db.selectFrom('transactions')
  .select((eb) => [
    'id',
    'amount',
    sql<number>`${eb.ref('amount')} - LAG(${eb.ref('amount')}, 1, 0) OVER (ORDER BY ${eb.ref('created_at')})`
      .as('diff')
  ])
```

### Percent of Total
```sql
SELECT id, department, salary,
  ROUND(salary * 100.0 / SUM(salary) OVER (), 2) AS pct_of_total
FROM employees
```
```ts
db.selectFrom('employees')
  .select((eb) => [
    'id',
    'department',
    'salary',
    sql<number>`ROUND(${eb.ref('salary')} * 100.0 / ${eb.fn.sum('salary').over()}, 2)`
      .as('pct_of_total')
  ])
```

### Year-over-Year Comparison
```sql
SELECT year, month, revenue,
  LAG(revenue, 12) OVER (ORDER BY year, month) AS prev_year_revenue,
  revenue - LAG(revenue, 12) OVER (ORDER BY year, month) AS yoy_diff
FROM monthly_revenue
```
```ts
db.selectFrom('monthly_revenue')
  .select((eb) => [
    'year',
    'month',
    'revenue',
    eb.fn.agg<number | null>('LAG', ['revenue', sql.lit(12)])
      .over((ob) => ob.orderBy('year').orderBy('month'))
      .as('prev_year_revenue'),
    sql<number | null>`${eb.ref('revenue')} - LAG(${eb.ref('revenue')}, 12) OVER (ORDER BY ${eb.ref('year')}, ${eb.ref('month')})`
      .as('yoy_diff')
  ])
```


Use `sql` for explicit frames or unsupported syntax. Ordinary references (`eb.ref`) and bound values (`eb.val`) do not require a raw SQL wrapper; the fixed `sql.lit` constants above are deliberate inline literals. Bind application-supplied data as explained in [operators](operators.md#choosing-methods-and-binding-values).
