# Plugin Signing and Marketplace Publishing

## Plugin signing

The Marketplace supports signed plugins, and signed plugins have less friction at install time on stricter IDE configurations. Configure signing in 2.x:

```kotlin
intellijPlatform {
  signing {
    certificateChain = providers.environmentVariable("JB_CERTIFICATE_CHAIN")
    privateKey       = providers.environmentVariable("JB_PRIVATE_KEY")
    password         = providers.environmentVariable("JB_PRIVATE_KEY_PASSWORD")
  }
}
```

`signPlugin` runs automatically right before `publishPlugin` when `certificateChain` and `privateKey` are set; otherwise it is skipped. In the [Plugin Signing guide](https://plugins.jetbrains.com/docs/intellij/plugin-signing.html), the plugin author generates the key and certificate with OpenSSL: an encrypted 4096-bit RSA key (`openssl genpkey -aes-256-cbc -algorithm RSA -pkeyopt rsa_keygen_bits:4096`), converted with `openssl rsa`, and a self-signed chain from `openssl req -key private.pem -new -x509 -days 365 -out chain.crt`. Pass the key and chain contents, or use `privateKeyFile` / `certificateChainFile`. Uploading the public key to Marketplace is described there as not available yet.

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

Channels are independent release streams. Users opt into non-default channels in `Settings | Plugins | Manage Plugin Repositories | Add custom plugin repository` (channel URL pattern documented on Marketplace).

`<change-notes>` in `plugin.xml` becomes the changelog displayed in the Marketplace card. The `intellij-platform-plugin-template` integrates with the `gradle-changelog-plugin` to populate this from `CHANGELOG.md` automatically.
