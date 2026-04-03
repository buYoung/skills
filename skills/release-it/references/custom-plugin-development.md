# Custom Plugin Development

## Getting Started

A release-it plugin is a class extending the `Plugin` base class. Create a plugin when hooks alone are insufficient — e.g. you need to provide version information, integrate with external APIs, or replace core behavior.

### Minimal example

```js
import { Plugin } from 'release-it';
import fs from 'node:fs';

class MyVersionPlugin extends Plugin {
  getLatestVersion() {
    return fs.readFileSync('./VERSION', 'utf8').trim();
  }

  bump(version) {
    this.version = version;
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
    "release-it": ">=17.0.0"
  },
  "devDependencies": {
    "release-it": "^20.0.0"
  }
}
```

Use `release-it` as `peerDependency` (and `devDependency` for testing).

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
  registerPrompts(...prompts) {} // → void
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

### this.registerPrompts(...prompts)

Register Inquirer.js prompts:

```js
init() {
  this.registerPrompts({
    type: 'confirm',
    name: 'deploy-confirm',
    message: 'Deploy to production?'
  });
}
```

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

**Forward order** (init through beforeRelease):
`PluginA` → `PluginB` → `npm` → `git` → `github` → `gitlab` → `version`

**Reverse order** (release and afterRelease):
`version` → `gitlab` → `github` → `git` → `npm` → `PluginB` → `PluginA`

External plugins run before core plugins for getters (so they can override name, version, changelog) and after for release/afterRelease (so they run after core work is done).

## Complete Plugin Example

A plugin that reads version from a `VERSION` file, posts a webhook after release:

```js
import { Plugin } from 'release-it';
import fs from 'node:fs';

export default class WebhookPlugin extends Plugin {
  static isEnabled(options) {
    return !!options.webhookUrl;
  }

  static disablePlugin() {
    return null;  // Don't disable any core plugins
  }

  init() {
    this.registerPrompts({
      type: 'confirm',
      name: 'webhook',
      message: 'Send release notification?'
    });
  }

  getLatestVersion() {
    if (fs.existsSync('./VERSION')) {
      return fs.readFileSync('./VERSION', 'utf8').trim();
    }
  }

  bump(version) {
    fs.writeFileSync('./VERSION', version);
  }

  async release() {
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
      "webhookUrl": "https://hooks.slack.com/services/xxx"
    }
  }
}
```

## Plugin Starterkit

Use the official [plugin-starterkit](https://github.com/release-it/plugin-starterkit) to bootstrap a new plugin project with testing setup included.
