#!/usr/bin/env python3
"""Run the copied project examples in disposable PTYs; intercept every Git push.

Usage: python3 run_interactive.py --dependencies /path/to/node_modules --output /tmp/results
Requires POSIX PTYs, Node, npm, pnpm, Git, and the dependency versions in the reference.
No installation, remote fetch/push, npm publishing, or deployment is performed.
"""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import select
import shutil
import struct
import subprocess
import sys
import termios
import time


SKILL = Path(__file__).resolve().parents[1]
ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
MARKERS = {
    "app": "Select one service app:",
    "version": "Select version (current:",
    "custom": "Next version (current:",
    "commit": "Commit (",
    "tag": "Tag (",
    "push": "Push?",
}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def record(path, event):
    with path.open("a") as stream:
        stream.write(json.dumps(event) + "\n")


def git(root, *args):
    return subprocess.check_output(
        [shutil.which("git"), "-C", str(root), *args],
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
        stderr=subprocess.DEVNULL, text=True,
    ).strip()


def fixture(case, directory, dependencies):
    root = directory / "project"
    root.mkdir(parents=True)
    shutil.copytree(SKILL / "examples/interactive-release", root / "scripts")
    (root / "node_modules").symlink_to(dependencies, target_is_directory=True)
    (root / ".gitignore").write_text("node_modules/\n")
    root_package = {"name": "fixture", "version": "1.2.3", "private": True,
                    "scripts": {"release": "node scripts/release.mjs"}}
    if case.get("settings_only_workspace"):
        (root / "pnpm-workspace.yaml").write_text("onlyBuiltDependencies: []\n")
    if case.get("mono"):
        root_package["version"] = "9.9.9"
        (root / "pnpm-workspace.yaml").write_text("packages:\n  - apps/*\n  - packages/*\n")
        apps = [{"name": "API", "path": "apps/api", "config": ".release-it.json"},
                {"name": "Web", "path": "apps/web", "config": ".release-it.json"}]
        if case.get("one_app"):
            apps = apps[:1]
        write_json(root / ".release-targets.json", {"serviceApps": apps})
        targets = [("apps/api", "api", "1.2.3"), ("apps/web", "web", "4.5.6")]
        write_json(root / "packages/ui/package.json", {"name": "ui", "version": "0.8.0", "private": True})
    else:
        targets = [(".", "fixture", "1.2.3")]
    write_json(root / "package.json", root_package)

    for relative, name, version in targets:
        app = root / relative
        app.mkdir(parents=True, exist_ok=True)
        if relative != ".":
            write_json(app / "package.json", {"name": name, "version": version, "private": True})
        (app / "CHANGELOG.md").write_text("# Changelog\n")
        (app / "source.txt").write_text("initial\n")
        prefix = f"{name}-v" if case.get("mono") else "v"
        config = {
            "git": {"commit": True, "tag": True, "push": True, "requireBranch": "main",
                    "requireUpstream": True, "tagName": prefix + "${version}",
                    "tagMatch": prefix + "[0-9]*", "commitsPath": ".",
                    "commitMessage": f"chore({name}): release ${{version}}"},
            "npm": {"publish": False, "versionArgs": ["--ignore-scripts", "--workspaces-update=false"]},
            "github": {"release": False}, "gitlab": {"release": False},
            "plugins": {"@release-it/conventional-changelog": {
                "preset": "conventionalcommits", "infile": "CHANGELOG.md", "tagPrefix": prefix,
                "gitRawCommitsOpts": {"path": "."}, "commitsOpts": {"path": "."}}},
        }
        if case.get("inherited"):
            config.update({"ci": True, "only-version": True, "release-version": True,
                           "changelog": True, "increment": "minor", "preRelease": "beta",
                           "snapshot": "canary", "dry-run": True})
        if case.get("guard_mismatch"):
            (app / "override.mjs").write_text(
                "import { Plugin } from 'release-it';\n"
                "export default class Override extends Plugin {\n"
                "  getIncrementedVersionCI() { return '9.0.0'; }\n}\n"
            )
            config["plugins"] = {"./override.mjs": {}, **config["plugins"]}
        write_json(app / ".release-it.json", config)

    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Release Fixture")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "commit.gpgsign", "false")
    git(root, "config", "tag.gpgsign", "false")
    git(root, "add", ".")
    git(root, "commit", "-m", "chore: initialize fixture")
    for relative, name, version in targets:
        prefix = f"{name}-v" if case.get("mono") else "v"
        git(root, "tag", "-a", prefix + version, "-m", "initial release")
        (root / relative / "source.txt").write_text(f"change for {name}\n")
        git(root, "add", str(Path(relative) / "source.txt"))
        git(root, "commit", "-m", f"feat({name})!: {name}-only-change")
    git(root, "remote", "add", "origin", "https://example.invalid/fixture/project.git")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(root, "config", "branch.main.remote", "origin")
    git(root, "config", "branch.main.merge", "refs/heads/main")
    return root


def environment(directory):
    bin_dir = directory / "bin"
    bin_dir.mkdir()
    events = directory / "events.jsonl"
    # Dispatch by Git command, not a pattern matching one expected push argument list.
    # All push variants (including release-it's error cleanup) terminate in this stub.
    wrapper = f'''#!{sys.executable}
import json, os, subprocess, sys
args = sys.argv[1:]
command = args[0] if args else ''
def emit(kind):
    with open(os.environ['RELEASE_EVAL_EVENTS'], 'a') as stream:
        stream.write(json.dumps({{'kind': kind, 'action': command, 'args': args, 'cwd': os.getcwd()}}) + '\\n')
if command == 'fetch':
    emit('fetch-stub')
    sys.exit(0)
is_action = command == 'commit' or (command == 'tag' and '--annotate' in args) or command == 'push'
if is_action:
    emit('action')
if command == 'push':
    emit('action-complete')
    print('push recorded by fixture; no remote contacted')
    sys.exit(0)
code = subprocess.call([{shutil.which('git')!r}, *args])
if is_action and code == 0:
    emit('action-complete')
sys.exit(code)
'''
    (bin_dir / "git").write_text(wrapper)
    (bin_dir / "git").chmod(0o755)
    env = {key: value for key, value in os.environ.items()
           if key not in {"CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILD_NUMBER"}}
    env.update({"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "TERM": "xterm-256color",
                "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                "RELEASE_EVAL_EVENTS": str(events), "npm_config_cache": str(directory / "npm-cache")})
    return env, events


def run_terminal(root, directory, env, events, responses, mode=None, arguments=()):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 160, 0, 0))
    is_input_pipe = mode in {"stdin", "both"}
    is_output_pipe = mode in {"stdout", "both"}
    child = subprocess.Popen(
        [shutil.which("pnpm"), "release", *arguments], cwd=root, env=env,
        stdin=subprocess.PIPE if is_input_pipe else slave,
        stdout=subprocess.PIPE if is_output_pipe else slave,
        stderr=subprocess.STDOUT, start_new_session=True,
    )
    os.close(slave)
    if is_input_pipe:
        try:
            child.stdin.write(b"y\ny\ny\ny\n")
            child.stdin.close()
        except BrokenPipeError:
            pass
    reader = child.stdout.fileno() if is_output_pipe else master
    transcript = b""
    cursor = 0
    sent = 0
    deadline = time.monotonic() + 35
    try:
        while True:
            if time.monotonic() > deadline:
                raise AssertionError("PTY timed out before the expected sequence finished")
            ready, _, _ = select.select([reader], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(reader, 65536)
                except OSError:
                    chunk = b""
                if not chunk:
                    break
                transcript += chunk
                plain = ANSI.sub("", transcript.decode(errors="replace"))
                if sent < len(responses):
                    stage, answer = responses[sent]
                    index = plain.find(MARKERS[stage], cursor)
                    if index >= 0:
                        record(events, {"kind": "question", "stage": stage})
                        os.write(master, answer)
                        cursor = index + len(MARKERS[stage])
                        sent += 1
            elif child.poll() is not None:
                break
        code = child.wait(timeout=5)
        if sent != len(responses):
            raise AssertionError(f"Only {sent}/{len(responses)} expected questions observed")
        return code, ANSI.sub("", transcript.decode(errors="replace"))
    finally:
        if child.poll() is None:
            import signal
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
        os.close(master)
        (directory / "terminal.log").write_bytes(transcript)


def run_case(case, output, dependencies):
    directory = output / case["name"]
    root = fixture(case, directory, dependencies)
    env, event_file = environment(directory)
    env.update(case.get("env", {}))
    head = git(root, "rev-parse", "HEAD")
    tags_before = set(git(root, "tag", "--list").splitlines())
    path = f"apps/{case.get('app', 'api')}" if case.get("mono") else "."
    selected = root / path
    before_files = {str(p.relative_to(root)): p.read_bytes()
                    for p in root.glob("**/package.json") if "node_modules" not in p.parts}
    before_files.update({str(p.relative_to(root)): p.read_bytes() for p in root.glob("**/CHANGELOG.md")
                         if "node_modules" not in p.parts})
    current = json.loads((selected / "package.json").read_text())["version"]
    next_version = case.get("version", "4.5.7" if current == "4.5.6" else "1.2.4")
    responses = []
    stop = case.get("stop")
    if not case.get("mode") and not case.get("arguments"):
        if case.get("mono"):
            responses.append(("app", b"\x1b[B\r" if case.get("app") == "web" else b"\r"))
        responses.append(("version", case.get("version_keys", b"\r")))
        if case.get("custom"):
            responses.append(("custom", next_version.encode() + b"\r"))
        responses.extend((stage, b"y\r") for stage in ("commit", "tag", "push"))
        if stop:
            index = next(i for i, response in enumerate(responses) if response[0] == stop)
            responses = responses[:index] + [(stop, b"n\r" if case.get("decline") else b"\x03")]
        if case.get("guard_mismatch"):
            responses = [("version", b"\r")]
    code, transcript = run_terminal(root, directory, env, event_file, responses,
                                    case.get("mode"), case.get("arguments", ()))
    events = [json.loads(line) for line in event_file.read_text().splitlines()] if event_file.exists() else []
    stopped = bool(stop or case.get("mode") or case.get("arguments") or case.get("guard_mismatch"))
    assert (code != 0) == stopped, f"Unexpected exit {code}: {transcript[-2000:]}"
    stages = [stage for stage, _ in responses]
    actual = [(event["kind"], event.get("stage", event.get("action"))) for event in events
              if event["kind"] != "fetch-stub"]
    expected = []
    for stage in stages:
        expected.append(("question", stage))
        if stage in {"commit", "tag", "push"} and stage != stop:
            expected.extend([("action", stage), ("action-complete", stage)])
    assert actual == expected, f"Question/action ordering differs: {actual} != {expected}"
    should_bump = not case.get("mode") and not case.get("arguments") and not case.get("guard_mismatch") and stop not in {"app", "version", "custom"}
    expected_version = next_version if should_bump else current
    assert json.loads((selected / "package.json").read_text())["version"] == expected_version
    should_commit = should_bump and stop != "commit"
    should_tag = should_commit and stop != "tag"
    assert (git(root, "rev-parse", "HEAD") != head) == should_commit
    tag = (f"{case.get('app', 'api')}-v" if case.get("mono") else "v") + next_version
    assert set(git(root, "tag", "--list").splitlines()) - tags_before == ({tag} if should_tag else set())
    status = git(root, "status", "--porcelain")
    assert bool(status) == (should_bump and not should_commit), f"Unexpected remaining changes: {status}"
    if should_bump:
        changelog = (selected / "CHANGELOG.md").read_text()
        assert next_version in changelog, "Selected version missing from changelog"
        if case.get("mono"):
            other = "api" if case.get("app") == "web" else "web"
            assert f"{other}-only-change" not in changelog, "Other app leaked into changelog"
        assert "HEAD before:" in transcript and "Version on disk:" in transcript
    for relative, content in before_files.items():
        if should_bump and Path(relative).parent == Path(path):
            continue
        assert (root / relative).read_bytes() == content, f"Unexpected write to {relative}"
    pushes = [event for event in events if event.get("action") == "push" and event["kind"] == "action"]
    assert len(pushes) == (0 if stopped else 1)
    if pushes:
        assert pushes[0]["args"] == ["push", "--follow-tags"]
        assert Path(pushes[0]["cwd"]).resolve() == selected.resolve()
    if case.get("mode"):
        assert "interactive terminal is required" in transcript
        assert not events, "Release work started without a terminal"
    if case.get("guard_mismatch"):
        assert "Resolved version differs from the displayed selection" in transcript
    if stages:
        first_questions = [key for key in ("app", "version", "commit", "tag", "push")
                           if MARKERS[key] in transcript]
        assert min(first_questions, key=lambda key: transcript.index(MARKERS[key])) == stages[0]
        if not case.get("mono"):
            assert MARKERS["app"] not in transcript
    return {"name": case["name"], "passed": True, "questions": stages,
            "push_calls": pushes, "version": expected_version, "exit_code": code}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", help="Run only a named case")
    args = parser.parse_args()
    dependencies = args.dependencies.resolve()
    for package in ("release-it", "@clack/prompts", "semver", "@release-it/conventional-changelog"):
        if not (dependencies / package / "package.json").exists():
            parser.error(f"Missing preinstalled dependency: {package}")
    cases = [
        {"name": "single-success"},
        {"name": "single-workspace-settings", "settings_only_workspace": True},
        {"name": "single-minor", "version_keys": b"\x1b[B\r", "version": "1.3.0"},
        {"name": "single-beta", "version_keys": b"\x1b[B" * 3 + b"\r", "version": "1.3.0-beta.0"},
        {"name": "single-custom", "version_keys": b"\x1b[B" * 7 + b"\r", "custom": True, "version": "2.3.4"},
        {"name": "monorepo-api", "mono": True},
        {"name": "monorepo-web", "mono": True, "app": "web"},
        {"name": "monorepo-one-app", "mono": True, "one_app": True},
        {"name": "single-cancel-version", "stop": "version"},
        {"name": "monorepo-cancel-app", "mono": True, "stop": "app"},
        {"name": "monorepo-cancel-version", "mono": True, "stop": "version"},
        {"name": "inherited-modes", "inherited": True},
        {"name": "ci-env", "inherited": True, "env": {"CI": "true"}},
        {"name": "vendor-ci-env", "inherited": True, "env": {"GITHUB_ACTIONS": "true"}},
        {"name": "plugin-version-mismatch", "guard_mismatch": True},
    ]
    cases += [{"name": f"{action}-{stage}", "stop": stage, "decline": action == "decline"}
              for action in ("decline", "cancel") for stage in ("commit", "tag", "push")]
    cases += [{"name": f"non-tty-{mode}", "mode": mode} for mode in ("stdin", "stdout", "both")]
    cases += [{"name": f"reject-{flag}", "arguments": [f"--{flag}"]}
              for flag in ("ci", "only-version", "yes")]
    if args.case:
        cases = [case for case in cases if case["name"] == args.case]
        if not cases:
            parser.error("Unknown case")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "environment.json", {
        "dependencies": {package: json.loads((dependencies / package / "package.json").read_text())["version"]
                         for package in ("release-it", "@clack/prompts", "semver", "@release-it/conventional-changelog")},
        "tools": {tool: subprocess.check_output([shutil.which(tool), "--version"], text=True).strip()
                  for tool in ("node", "npm", "pnpm", "git")},
        "example_sha256": {file.name: hashlib.sha256(file.read_bytes()).hexdigest()
                           for file in (SKILL / "examples/interactive-release").glob("*.mjs")},
    })
    results = []
    for case in cases:
        try:
            result = run_case(case, output, dependencies)
        except Exception as error:
            result = {"name": case["name"], "passed": False, "error": str(error)}
        results.append(result)
        print(json.dumps(result), flush=True)
        write_json(output / "results.json", results)
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
