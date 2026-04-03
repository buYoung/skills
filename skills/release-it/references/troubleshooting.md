# Troubleshooting

## Common Errors

### "Working dir not clean"

**Error**: `ERROR Working dir must be clean.`

**Cause**: Uncommitted changes exist in the working directory.

**Solutions**:
1. Commit or stash changes before running release-it
2. Disable the check: `--no-git.requireCleanWorkingDir`
3. In config: `"git": { "requireCleanWorkingDir": false }`

This is common in monorepo setups where other packages modify files during release.

---

### "No upstream configured"

**Error**: `ERROR No upstream configured for current branch.`

**Cause**: Current branch has no tracking remote branch.

**Solutions**:
1. Set upstream: `git push -u origin <branch>`
2. Disable the check: `--no-git.requireUpstream`

When disabled, release-it adds `--set-upstream origin <branch>` to the push command automatically.

---

### "Tag already exists"

**Error**: `ERROR fatal: tag vX.X.X already exists`

**Causes**:
- Tag was already created (e.g. by a previous failed release attempt)
- Stale local tags not in sync with remote (common in GitLab CI)

**Solutions**:
1. Delete the existing tag: `git tag -d vX.X.X && git push origin :refs/tags/vX.X.X`
2. Fetch and prune tags before release:
   ```json
   {
     "hooks": {
       "before:init": "git fetch --prune --prune-tags origin"
     }
   }
   ```
3. Use `git.tagMatch` or `git.tagExclude` to avoid conflicts

---

### "No commits since latest tag"

**Error**: `ERROR There are no commits since the latest tag.`

**Cause**: `git.requireCommits` is `true` and no new commits exist.

**Solutions**:
1. Make a commit before releasing
2. Disable: `"git": { "requireCommits": false }` (default)
3. Check `git.tagMatch` — might be matching unexpected tags
4. Check `git.commitsPath` — might be scoped to wrong directory

---

### npm Authentication Errors

**Error**: `ENEEDAUTH` or `E403` or `E401`

**Causes**:
- Missing or invalid npm token
- `.npmrc` not configured
- Scoped package not configured for public access

**Solutions**:

1. Check npm auth:
   ```bash
   npm whoami
   ```

2. Set token in `.npmrc`:
   ```text
   //registry.npmjs.org/:_authToken=${NPM_TOKEN}
   ```

3. For scoped packages, add to `package.json`:
   ```json
   {
     "publishConfig": {
       "access": "public"
     }
   }
   ```

4. For CI, ensure `NPM_TOKEN` env var is set

5. If registry doesn't support `npm ping`/`npm whoami` (e.g. Nexus):
   ```json
   {
     "npm": {
       "skipChecks": true
     }
   }
   ```

---

### GitHub Token Issues

**Error**: `ERROR Could not authenticate with GitHub.` or `RequestError [HttpError]: Bad credentials`

**Causes**:
- `GITHUB_TOKEN` not set
- Token expired or revoked
- Insufficient permissions

**Solutions**:

1. Verify token:
   ```bash
   echo $GITHUB_TOKEN
   ```

2. Create a new token with `repo` scope:
   - Personal access token (classic): needs `repo` scope
   - Fine-grained token: needs `Contents: Read and write` permission

3. Use a different env var name:
   ```json
   {
     "github": {
       "tokenRef": "GH_RELEASE_TOKEN"
     }
   }
   ```

4. Skip checks (use web mode instead):
   ```json
   {
     "github": {
       "web": true
     }
   }
   ```

---

### Empty Changelog

**Cause**: The changelog command produces no output.

**Possible reasons**:
- No commits between tags
- Wrong tag matching pattern
- Using conventional-changelog plugin but commits don't follow convention

**Solutions**:

1. Check what the changelog command produces:
   ```bash
   release-it --changelog
   ```

2. Verify tag matching:
   ```bash
   git tag --list
   git log --oneline $(git describe --tags --abbrev=0)...HEAD
   ```

3. If using `@release-it/conventional-changelog`, ensure commits follow the `type(scope): message` format

---

### "Required branch" Failure

**Error**: `ERROR Must be on branch "main", got "develop".`

**Solutions**:
1. Switch to the required branch
2. Update config to allow current branch:
   ```json
   {
     "git": {
       "requireBranch": ["main", "develop", "release/*"]
     }
   }
   ```
3. Disable: `"git": { "requireBranch": false }`

---

### CI-Specific Issues

#### No interactive prompts in CI

release-it auto-detects CI environments. If not detected, use `--ci` explicitly:

```bash
npx release-it --ci
```

#### Git user not configured

```bash
git config user.name "${GITHUB_ACTOR}"
git config user.email "${GITHUB_ACTOR}@users.noreply.github.com"
```

#### Shallow clone (missing history)

Use `fetch-depth: 0` in GitHub Actions:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
```

Without this, changelog generation and tag-based version detection may fail.

#### Permission denied in CI

Ensure the CI has push access:
- SSH: add deploy key with write access
- HTTPS: use token with repo permissions in the remote URL

---

### npm version Failure

**Error**: `npm ERR! Version not changed`

**Cause**: New version equals current version.

**Solutions**:
1. Set `npm.allowSameVersion: true`
2. Or use `npm.versionArgs: ["--allow-same-version"]`

---

### Registry 403/404

**Cause**: Package doesn't exist on registry yet, or auth issue.

**Solutions**:
1. For first publish: `npm publish` manually once, or use `npm.skipChecks: true`
2. For scoped packages: ensure `publishConfig.access: "public"`
3. For private registries: ensure `.npmrc` has the correct auth token

---

## Debugging

### Verbose mode

```bash
release-it -V     # Shows hook output
release-it -VV    # Shows internal commands too
```

### Debug mode

Full debug output from all plugins:

```bash
NODE_DEBUG=release-it:* release-it
```

Namespace-specific debug:

```bash
NODE_DEBUG=release-it:git release-it     # Git plugin only
NODE_DEBUG=release-it:npm release-it     # npm plugin only
```

### Dry run for diagnosis

```bash
release-it --dry-run
```

Shows all commands that would execute. Read-only commands (`$`) still run, write commands (`!`) are skipped. Useful to verify:
- What version would be bumped to
- What changelog would be generated
- What git commands would run
- Whether npm publish would execute

### Check configuration

Verify what release-it sees as its final merged config:

```bash
release-it --release-version    # Confirm version detection works
release-it --changelog          # Confirm changelog generation works
```
