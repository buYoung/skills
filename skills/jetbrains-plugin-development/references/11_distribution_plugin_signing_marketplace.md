# Plugin Signing and Marketplace Publishing

## Plugin signing

The Marketplace supports signed plugins, and signed plugins have less friction at install
time on stricter IDE configurations. Configure signing in 2.x:

```kotlin
intellijPlatform {
  signing {
    certificateChain = providers.environmentVariable("JB_CERTIFICATE_CHAIN")
    privateKey       = providers.environmentVariable("JB_PRIVATE_KEY")
    password         = providers.environmentVariable("JB_PRIVATE_KEY_PASSWORD")
  }
}
```

Then `signPlugin` (run by `publishPlugin` if signing is configured). JetBrains provides a
free signing certificate via the Marketplace dashboard.

## Marketplace publishing

```kotlin
intellijPlatform {
  publishing {
    token        = providers.environmentVariable("JETBRAINS_MARKETPLACE_TOKEN")
    channels     = listOf("default")          // or "beta", "eap", custom names
    hidden       = false
    ideServices  = false
  }
}
```

Then `./gradlew publishPlugin` after `signPlugin`.

Channels are independent release streams. Users opt into non-default channels in
`Settings | Plugins | Manage Plugin Repositories | Add custom plugin repository` (channel
URL pattern documented on Marketplace).

`<change-notes>` in `plugin.xml` becomes the changelog displayed in the Marketplace card.
The `intellij-platform-plugin-template` integrates with the `gradle-changelog-plugin` to
populate this from `CHANGELOG.md` automatically.
