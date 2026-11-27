# DynamoDB Local 2.x (and 1.x)

Checked: 2026-11-27 against https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocalHistory.html and https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html

Read this when a test environment still runs DynamoDB local 2.x or 1.x and needs to move to [3.x](local-3.x.md).

## Lifecycle

2.x is legacy; 1.x is deprecated. No end dates are published. Last releases in the history: 2.6.0 (2025-03-13) and 1.25.1 (2024-11-06).

| Release | Date | Change that matters |
|---|---|---|
| 2.6.0 | 2025-03-13 | Table ARN accepted as table name in several APIs; JRE 17 required; CVE fixes |
| 2.5.4 | 2024-12-12 | Jetty 12.0.14 |
| 2.5.0 to 2.5.2 | 2024-05-28 to 2024-06-20 | Configurable on-demand maximum throughput; `ReturnValuesOnConditionCheckFailure`; `BatchExecuteStatement` and `ExecuteTransaction` fixes; on-demand to provisioned with GSI fix |
| 2.3.0 | 2024-03-14 | JDK 17, Jetty 12 |
| 2.2.0 | 2023-12-14 | Deletion protection, `ReturnValuesOnConditionCheckFailure`, `-version` flag |
| 2.1.0 | 2023-10-23 | Telemetry added (disable with `-disableTelemetry`) |
| 2.0.0 | 2023-07-05 | `javax` to `jakarta` namespace; JDK 11 |
| 1.25.0 / 1.25.1 | 2023-12-18 / 2024-11-06 | Backports of deletion protection, `ReturnValuesOnConditionCheckFailure`, `-version`; Jackson fix |
| 1.21.0 | 2023-01-26 | 100 actions per transaction (was 25) |

The history dates 1.17.1 and 1.17.2 (Log4j fixes) January 2021; quote them as published.

## Removed or Deprecated

1.x is deprecated. 1.17.0 deprecated the JavaScript web shell.

## Upgrading Into This Series

Not a target; move straight to 3.x. From 1.x, the `jakarta` namespace change (2.0.0) and the Java 17 requirement (2.3.0, enforced from 2.6.0) are the blockers; from 2.x, the package rename in 3.0.0. A test suite that passes on 1.x with transactions of more than 25 actions needs 1.21.0 or later.
