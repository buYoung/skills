# DynamoDB Local 3.x

Checked: 2026-11-27 against https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocalHistory.html and container output from `amazon/dynamodb-local:latest` (reports `Version: 3.3.2`)

Read this when tests run against DynamoDB local 3.x, or when moving test infrastructure from 2.x.

## Lifecycle

Current and recommended. 3.0.0 shipped 2025-07-17; the latest release is 3.3.2 (2026-10-15). No end-of-support date is published.

| Release | Date | Change that matters |
|---|---|---|
| 3.3.2 | 2026-10-15 | SDK for Java 2.55.15; dependency CVE fixes |
| 3.3.1 | 2026-07-31 | PartiQL dependencies added to the POM; SDK 2.48.3; CVE fixes |
| 3.3.0 | 2026-01-19 | Multi-attribute keys for GSIs |
| 3.2.0 | 2026-01-09 | `ShardFilter` on `DescribeStream`; fix for deletion protection on `UpdateTable`; Kotlin version compatibility |
| 3.1.0 | 2025-09-14 | Faster PartiQL; Joda-time included; CVE fixes |
| 3.0.0 | 2025-07-17 | Moved from SDK for Java v1 to v2; package `com.amazonaws.services.dynamodbv2` replaced by `software.amazon.dynamodb.services` (the setup page says `software.amazon.dynamodb`); v1 dependencies removed |

## Changed Defaults

The Docker image starts with `-inMemory` on port 8000 with `SharedDb: false` and `shouldDelayTransientStatuses: false` (container log). Data is lost when the container stops unless you override the command with `-sharedDb -dbPath ./data` and mount a volume.

## Removed or Deprecated

AWS SDK for Java v1 classes are gone from the embedded artifact. Code that starts DynamoDB local in-process through the v1 package names must change.

## Worth Adopting

- Multi-attribute GSI keys (3.3.0) let tests cover indexes that use the 2026 key schema form.
- `ShardFilter` (3.2.0) lets stream-consumer tests exercise child-shard discovery.

## Upgrading Into This Series

1. Docker users: change the tag, or pin `amazon/dynamodb-local:3.3.2` rather than `latest` so CI results are reproducible. The digest seen on 2026-11-27 is in [dynamodb-local.md](../dynamodb-local.md).
2. Maven or embedded users: change imports from `com.amazonaws.services.dynamodbv2` to `software.amazon.dynamodb` and use the `software.amazon.dynamodb:DynamoDBLocal:3.3.2` dependency.
3. JRE 17 or newer is required (required since 2.6.0).
4. Re-run the suite; confirm the startup log shows the expected version.
5. Rollback: pin the previous tag or artifact.

See [dynamodb-local](../dynamodb-local.md) for behavior differences from the service.
