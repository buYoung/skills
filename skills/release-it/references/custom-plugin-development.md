# Custom Plugin Development

## Getting Started

A release-it plugin is a class extending the `Plugin` base class. Create a plugin when hooks alone are insufficient — e.g. you need to provide version information, integrate with external APIs, or replace core behavior.

The interfaces below are source-checked for **21.0.1**. Match the applying project's
installed API and runtime before declaring a wider compatibility range. A custom version
provider must follow the [version source contract](plugins.md#version-source-contract).

### Minimal example

```js
import { Plugin } from 'release-it';
import fs from 'node:fs';

class MyVersionPlugin extends Plugin {
  static disablePlugin() {
    return 'npm'; // This example owns VERSION instead of package.json.
  }

  getLatestVersion() {
    return fs.readFileSync('./VERSION', 'utf8').trim();
  }

  bump(version) {
    this.version = version;
    if (this.config.isDryRun) {
      this.log.info(`Would update VERSION to ${version}`);
      return;
    }
    fs.writeFileSync('./VERSION', version);
  }
}

export default MyVersionPlugin;
```

### Plugin package.json

```json
{
  "name": "release-it-my-plugin",
  "version": "1.0.0",
  "main": "index.js",
  "type": "module",
  "keywords": ["release-it", "release-it-plugin"],
  "peerDependencies": {
    "release-it": "21.0.1"
  },
  "devDependencies": {
    "release-it": "21.0.1"
  }
}
```

Use `release-it` as `peerDependency` (and `devDependency` for testing). The example pins
the checked version; widen the peer range only after verifying the interfaces your plugin uses.

### Using the plugin

```json
{
  "plugins": {
    "release-it-my-plugin": {
      "option1": "value1"
    },
    "./scripts/local-plugin.js": {}
  }
}
```

## Plugin Class API

```js
class Plugin {
  // Static methods
  static isEnabled() {}       // → Boolean
  static disablePlugin() {}   // → String | String[] | null

  // Getter methods
  getInitialOptions(options, pluginName) {}  // → Object
  getName() {}                // → String
  getLatestVersion() {}       // → SemVer string
  getChangelog() {}           // → String
  getIncrement({ latestVersion, increment, isPreRelease, preReleaseId }) {} // → String
  getIncrementedVersionCI({ latestVersion, increment, isPreRelease, preReleaseId }) {} // → SemVer
  getIncrementedVersion({ latestVersion, increment, isPreRelease, preReleaseId }) {} // → SemVer

  // Lifecycle methods (all can be async)
  init() {}
  beforeBump() {}
  bump(version) {}
  beforeRelease() {}
  release() {}
  afterRelease() {}

  // Helper methods
  setContext(context) {}      // → void
  getContext(path) {}         // → Object
  registerPrompts(definitions) {} // → void; map keyed by prompt name
  step(options) {}            // → Promise
  exec(command, options) {}   // → Promise
  debug(msg) {}               // → void
  log.verbose|warn|error|log|info()  // → void
}
```

## Static Methods

### isEnabled() → Boolean

Control whether the plugin activates. Default: always enabled.

```js
static isEnabled(options) {
  return options.enabled !== false;
}
```

### disablePlugin() → String | String[] | null

Disable a core plugin when this plugin replaces it. Return the name(s) of core plugins to disable (`version`, `git`, `github`, `gitlab`, `npm`).

```js
static disablePlugin() {
  return 'npm';  // Replace the npm plugin
}

// Disable multiple
static disablePlugin() {
  return ['npm', 'version'];
}
```

## Lifecycle Methods

All lifecycle methods can be `async`. They run in order across all plugins.

### init()

Validate prerequisites, gather details. Runs first.

```js
async init() {
  const hasConfig = fs.existsSync('./my-config.json');
  if (!hasConfig) {
    throw new Error('my-config.json not found');
  }
}
```

### beforeBump()

Prepare for version increment. Output useful information for user confirmation.

```js
async beforeBump() {
  const changelog = await this.generateChangelog();
  this.log.info(`Changes:\n${changelog}`);
}
```

### bump(version)

Update version in files. The `version` parameter is the new version string.

```js
async bump(version) {
  if (this.config.isDryRun) {
    this.log.info(`Would update manifest.json to ${version}`);
    return;
  }
  const manifest = JSON.parse(fs.readFileSync('./manifest.json', 'utf8'));
  manifest.version = version;
  fs.writeFileSync('./manifest.json', JSON.stringify(manifest, null, 2));
}
```

### beforeRelease()

Tasks after bump but before release. Stage files for the release commit.

### release()

Main release logic. Use `this.step()` to create interactive prompts or CI spinners.

```js
async release() {
  if (this.config.isDryRun) {
    this.log.info('Would deploy and send the configured notification');
    return false;
  }
  await this.step({
    enabled: true,
    task: () => this.exec('npm run deploy'),
    label: 'Deploying to production',
    prompt: 'deploy-confirm'
  });

  await this.step({
    enabled: this.options.notify,
    task: () => this.notifySlack(),
    label: 'Sending notification'
  });
}
```

Return `false` to indicate the step was skipped — this prevents `after:[plugin]:release` hooks from running.

### afterRelease()

Post-release tasks. Provide success details, links, etc.

```js
afterRelease() {
  this.log.info(`🎉 Published to ${this.getContext('deployUrl')}`);
}
```

## Getter Methods

The first plugin to return a value from a getter method wins — that value is used throughout the process.

### getName() → String

Return the package/project name.

```js
getName() {
  return JSON.parse(fs.readFileSync('./config.json', 'utf8')).name;
}
```

### getLatestVersion() → SemVer

Return the current/latest version before bump.

```js
getLatestVersion() {
  return fs.readFileSync('./VERSION', 'utf8').trim();
}
```

### getChangelog() → String

Generate and return changelog text.

### getIncrement() → String

Override the increment type. Return `major`, `minor`, or `patch`.

### getIncrementedVersionCI() → SemVer

Calculate next version for CI (non-interactive) mode.

### getIncrementedVersion() → SemVer

Calculate next version. May prompt user if needed.

### getInitialOptions(options, pluginName) → Object

Extend plugin options with values from other plugins' config:

```js
getInitialOptions(options, pluginName) {
  return Object.assign({}, options[pluginName], {
    tagName: options.git.tagName
  });
}
```

## Helper Methods

### this.setContext(context) / this.getContext(path)

Store and retrieve runtime data within the plugin:

```js
async release() {
  const result = await this.deploy();
  this.setContext({ deployUrl: result.url, deployId: result.id });
}

afterRelease() {
  const url = this.getContext('deployUrl');
  this.log.info(`Deployed to ${url}`);
}
```

`getContext()` merges plugin options with runtime context.

### this.exec(command, options)

Execute shell commands with template variable substitution:

```js
// Template variables are auto-replaced
await this.exec('git log ${latestTag}...HEAD');

// Read-only commands run in dry-run mode
this.exec('git log', { options: { write: false } });

// With custom context
this.exec('deploy ${version}', { context: { deployTarget: 'prod' } });
```

Available template variables: `version`, `latestVersion`, `latestTag`, `changelog`, `name`, `repo.remote`, `repo.protocol`, `repo.host`, `repo.owner`, `repo.repository`, `repo.project`, plus all config options.

### this.step(options) → Promise

Display interactive prompt or CI spinner:

```js
await this.step({
  enabled: true,             // Whether to show this step
  task: () => this.doWork(), // The async function to execute
  label: 'Doing work',      // Spinner/prompt label
  prompt: 'my-prompt'       // Prompt name (registered with registerPrompts)
});
```

In CI mode: shows spinner. In interactive mode: shows prompt — if user says "No", `task` is not executed.

### this.registerPrompts(definitions)

Register a map keyed by the names passed to `this.step({ prompt })`. In 21.0.1,
`message` is called with the execution context; use a function, not a string:

```js
init() {
  this.registerPrompts({
    'deploy-confirm': {
      type: 'confirm',
      message: () => 'Deploy to production?',
      default: true
    }
  });
}
```

The stock prompt supports confirm/input/list definitions. A caller's injected prompt
adapter must support the namespace and definition as well: the packaged interactive
adapter accepts only Git commit/tag/push and intentionally rejects this deploy question.
Extend that adapter only for the capabilities requested by the applying workflow.
Sources: [Plugin](https://github.com/release-it/release-it/blob/21.0.1/lib/plugin/Plugin.js)
and [Prompt](https://github.com/release-it/release-it/blob/21.0.1/lib/prompt.js).

### Dry-run and Direct Effects

Lifecycle methods still run in dry-run mode. `this.exec()` routes through release-it's
shell layer, which skips commands classified as writes. Direct filesystem writes,
independent child processes, and `fetch()` calls need an explicit `this.config.isDryRun`
guard. `this.step()` by itself is not a dry-run guard for an arbitrary task callback.
Report the intended effect when skipping it, and verify that files and external sinks
remain unchanged in a dry-run check.

### this.debug(msg)

Debug logging (only visible with `NODE_DEBUG=release-it:*`):

```js
this.debug(`Processing ${files.length} files`);
// Output: release-it:my-plugin Processing 5 files
```

### this.log

User-facing logging:

```js
this.log.info('Starting deployment...');
this.log.warn('No deploy target configured');
this.log.error('Deployment failed');
this.log.verbose('Detailed step info');
```

## Instance Properties

| Property | Description |
|----------|-------------|
| `this.namespace` | Plugin identifier (package name or path) |
| `this.options` | Frozen plugin options from config |
| `this.context` | Runtime context (writable via `setContext`) |
| `this.config` | Global release-it config access |
| `this.log` | Logger instance |
| `this.shell` | Shell executor |
| `this.spinner` | Spinner instance |
| `this.prompt` | Prompt instance |

## Execution Order

Given external plugins A and B:

```json
{ "plugins": { "PluginA": {}, "PluginB": {} } }
```

External plugins run before core plugins through `beforeRelease`, and after core plugins
for `release`/`afterRelease`. The order within each group stays unchanged, so A still
precedes B. See the exact [21.0.1 lifecycle order](hooks-and-lifecycle.md#plugin-order-and-side-effects)
before placing publication, staging, or recovery logic. Getter precedence does not disable
another plugin's bump writes.

## Complete Plugin Example

A plugin that owns a `VERSION` file, disables npm versioning/publishing, and offers a
webhook notification after core release actions. Use it with the stock prompt or an
adapter that supports its question; the Git-only service-app adapter does not:

```js
import { Plugin } from 'release-it';
import fs from 'node:fs';

export default class WebhookPlugin extends Plugin {
  static isEnabled(options) {
    return !!options.webhookUrl;
  }

  static disablePlugin() {
    return 'npm';
  }

  getName() {
    return this.options.name || 'project';
  }

  init() {
    this.registerPrompts({
      webhook: {
        type: 'confirm',
        message: () => 'Send release notification?',
        default: true
      }
    });
  }

  getLatestVersion() {
    if (fs.existsSync('./VERSION')) {
      return fs.readFileSync('./VERSION', 'utf8').trim();
    }
  }

  bump(version) {
    if (this.config.isDryRun) {
      this.log.info(`Would update VERSION to ${version}`);
      return;
    }
    fs.writeFileSync('./VERSION', version);
  }

  async release() {
    if (this.config.isDryRun) {
      this.log.info('Would send release notification');
      return false;
    }
    await this.step({
      enabled: true,
      task: async () => {
        const { version, name } = this.config.getContext();
        const response = await fetch(this.options.webhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: `Released ${name} v${version}`
          })
        });
        this.setContext({ notified: response.ok });
      },
      label: 'Sending webhook notification',
      prompt: 'webhook'
    });
  }

  afterRelease() {
    if (this.getContext('notified')) {
      this.log.info('Webhook notification sent successfully');
    }
  }
}
```

Usage:

```json
{
  "plugins": {
    "./plugins/webhook.js": {
      "name": "my-product",
      "webhookUrl": "https://hooks.slack.com/services/xxx"
    }
  }
}
```

## Plugin Starterkit

Use the official [plugin-starterkit](https://github.com/release-it/plugin-starterkit) to bootstrap a new plugin project with testing setup included.
