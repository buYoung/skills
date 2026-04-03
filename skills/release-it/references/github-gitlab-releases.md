# GitHub and GitLab Releases

## GitHub Releases

### Setup

Two modes:

1. **Automated** (API): Requires `GITHUB_TOKEN` personal access token with "repo" scope
2. **Manual** (Web): Opens browser with pre-populated fields. Auto-enabled when `GITHUB_TOKEN` is not set

```json
{
  "github": {
    "release": true
  }
}
```

### Token Configuration

Set `GITHUB_TOKEN` as environment variable:

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

Use `.env` file with `dotenv-cli`:

```json
{
  "scripts": {
    "release": "dotenv release-it --"
  }
}
```

Change env var name: `"github.tokenRef": "MY_GH_TOKEN"`

Do not put the actual token in the config file.

### Release Name

```json
{
  "github": {
    "releaseName": "Release ${version}"
  }
}
```

Or from CLI: `--github.releaseName="Arcade Silver"`

### Release Notes

By default, uses the output of `git.changelog`. Override with:

#### String (shell command)

```json
{
  "github": {
    "releaseNotes": "generate-notes.sh --from=${latestTag} --to=${tagName}"
  }
}
```

#### Function (JS/CJS config only)

```js
{
  github: {
    release: true,
    releaseNotes(context) {
      return context.changelog.split('\n').slice(1).join('\n');
    }
  }
}
```

#### Object (template-based from GitHub API)

```json
{
  "github": {
    "releaseNotes": {
      "commit": "* ${commit.subject} (${sha}){ - thanks @${author.login}!}",
      "excludeMatches": ["bot-user"]
    }
  }
}
```

Blocks in `{...}` render only if all placeholders inside resolve to values not in `excludeMatches`.

#### Auto-generate (GitHub native)

```json
{
  "github": {
    "autoGenerate": true
  }
}
```

Overrides other release notes settings. Does not work with `web: true`.

### Assets

Upload binary assets (executables, docs, etc.) to the release:

```json
{
  "github": {
    "release": true,
    "assets": ["dist/*.zip", "docs/**/*.pdf"]
  }
}
```

### Pre-release and Draft

Pre-release status is auto-set for semver pre-release versions. Can be set manually:

```json
{
  "github": {
    "preRelease": true,
    "draft": false
  }
}
```

### Comments on Issues/PRs

Auto-comment on merged PRs and closed issues included in the release:

```json
{
  "github": {
    "release": true,
    "comments": {
      "submit": true,
      "issue": ":rocket: _This issue has been resolved in v${version}. See [${releaseName}](${releaseUrl}) for release notes._",
      "pr": ":rocket: _This pull request is included in v${version}. See [${releaseName}](${releaseUrl}) for release notes._"
    }
  }
}
```

Requires `github.release: true` (not web mode).

### GitHub Discussions

Auto-create a Discussion for the release:

```json
{
  "github": {
    "discussionCategoryName": "Announcements"
  }
}
```

### Non-Latest Release

For support/backport releases that shouldn't be marked as "latest":

```json
{
  "github": {
    "makeLatest": false
  }
}
```

### GitHub Enterprise

```json
{
  "github": {
    "release": true,
    "host": "github.mycompany.com"
  }
}
```

API endpoint becomes `https://github.mycompany.com/api/v3`.

### Behind a Proxy

```json
{
  "github": {
    "proxy": "http://proxy:8080"
  }
}
```

### Update Existing Release

Update assets, notes, or draft status of an existing release:

```bash
release-it --no-increment --no-git --no-npm \
  --github.release --github.update \
  --github.assets=dist/*.zip --no-github.draft
```

---

## GitLab Releases

Requires GitLab v11.7+. Token needs `api` and `self_rotate` scopes.

### Setup

```json
{
  "gitlab": {
    "release": true
  }
}
```

Set `GITLAB_TOKEN` environment variable.

### Release Notes

Same as GitHub — string command or function (JS config):

```json
{
  "gitlab": {
    "releaseNotes": "generate-notes.sh ${latestVersion} ${version}"
  }
}
```

### Milestones

Associate releases with GitLab milestones:

```json
{
  "gitlab": {
    "release": true,
    "milestones": ["${version}"]
  }
}
```

Release fails if a milestone doesn't exist. Skip with `gitlab.skipChecks`.

### Assets

```json
{
  "gitlab": {
    "release": true,
    "assets": ["dist/*.dmg"]
  }
}
```

For GitLab 17.2+, set `useIdsForUrls: true`.

#### Generic Package Repository

```json
{
  "gitlab": {
    "release": true,
    "useGenericPackageRepositoryForAssets": true,
    "genericPackageRepositoryName": "release-it",
    "assets": ["dist/*.dmg"]
  }
}
```

### Self-Hosted GitLab

#### Custom origin

```json
{
  "gitlab": {
    "origin": "http://gitlab.internal:3000"
  }
}
```

#### Private CA certificate

```json
{
  "gitlab": {
    "certificateAuthorityFile": "./my-root-ca.crt"
  }
}
```

Or disable certificate verification:

```json
{
  "gitlab": {
    "secure": false
  }
}
```

### GitLab CI Configuration

```yaml
before_script:
  - apk add --no-cache git openssh
  - eval `ssh-agent -s`
  - echo "${SSH_PRIVATE_KEY}" | tr -d '\r' | ssh-add - > /dev/null
  - mkdir -p ~/.ssh
  - chmod 700 ~/.ssh
  - '[[ -f /.dockerenv ]] && echo -e "Host *\n\tStrictHostKeyChecking no\n\n" > ~/.ssh/config'
  - git checkout $CI_COMMIT_REF_NAME
  - git remote set-url origin "git@gitlab.com:$CI_PROJECT_PATH.git"
  - git config --global user.name "${CI_USERNAME}"
  - git config --global user.email "${CI_EMAIL}"
  - npm install
script:
  - npx release-it --ci
```

### Update Existing Release

```bash
release-it --no-increment --no-git --no-npm \
  --gitlab.release --gitlab.assets=dist/*.zip
```
