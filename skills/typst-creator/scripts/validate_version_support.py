#!/usr/bin/env python3
"""Compile compatibility fixtures with explicitly supplied stable Typst releases."""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = SKILL_ROOT / "evals" / "fixtures"
SUPPORTED_RELEASES = (
    "0.13.0", "0.13.1", "0.14.0", "0.14.1", "0.14.2", "0.15.0", "0.15.1",
)
LATEST_PATCHES = {"0.13": "0.13.1", "0.14": "0.14.2", "0.15": "0.15.1"}
# Capture the entire token: a numeric prefix of a prerelease is not stable.
VERSION_PATTERN = re.compile(r"^typst\s+(\S+)(?:\s+\([^\r\n]*\))?\s*$", re.IGNORECASE)
STABLE_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")
VERSION_TIMEOUT_SECONDS = 10
COMPILE_TIMEOUT_SECONDS = 60
COMMON_FIXTURES = (
    "common.typ", "api-regressions.typ", "context.typ", "long-document.typ",
    "presentation.typ", "resources.typ",
)
FEATURE_FIXTURES = (
    ("0.13.0", "typst-0.13.typ"),
    ("0.14.0", "typst-0.14.typ"),
    ("0.15.0", "typst-0.15.typ"),
    ("0.15.0", "typst-0.15-path.typ"),
)


@dataclass(frozen=True)
class CompilerTarget:
    expected_version: str
    compiler: Path
    fixtures: tuple[str, ...]

    @property
    def label(self) -> str:
        return f"Typst {self.expected_version}"


@dataclass
class Report:
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_versions: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"PASS: {item}" for item in self.passed]
        lines.extend(f"WARN: {item}" for item in self.warnings)
        lines.extend(f"FAIL: {item}" for item in self.failed)
        lines.append(f"Checked releases: {', '.join(self.checked_versions) or 'none'}")
        unchecked = [v for v in SUPPORTED_RELEASES if v not in self.checked_versions]
        lines.append(f"Unchecked releases: {', '.join(unchecked) or 'none'}")
        lines.append(
            f"Summary: {len(self.passed)} passed, {len(self.failed)} failed, "
            f"{len(self.warnings)} warnings"
        )
        return "\n".join(lines)


def read_compiler_version(compiler: Path) -> tuple[str | None, str]:
    try:
        result = subprocess.run(
            [str(compiler), "--version"], check=False, capture_output=True,
            text=True, timeout=VERSION_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None, f"version query timed out after {VERSION_TIMEOUT_SECONDS}s"
    except OSError as error:
        return None, f"could not execute compiler: {error}"
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    if result.returncode != 0:
        return None, output or f"exit code {result.returncode}"
    match = VERSION_PATTERN.fullmatch(result.stdout.strip())
    if not match or not STABLE_VERSION_PATTERN.fullmatch(match.group(1)):
        return None, output or "missing stable compiler version"
    return match.group(1), output


def compile_fixture(compiler: Path, fixture_name: str, output_dir: Path) -> tuple[bool, str]:
    fixture = FIXTURE_ROOT / fixture_name
    output = output_dir / f"{fixture.stem}.pdf"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        # Require this invocation to create the output, not inherit a stale artifact.
        output.unlink(missing_ok=True)
        result = subprocess.run(
            [str(compiler), "compile", "--root", str(SKILL_ROOT), str(fixture), str(output)],
            cwd=SKILL_ROOT, check=False, capture_output=True, text=True,
            timeout=COMPILE_TIMEOUT_SECONDS,
        )
        diagnostics = "\n".join(
            part for part in (result.stdout.strip(), result.stderr.strip()) if part
        )
        if result.returncode != 0:
            return False, diagnostics or f"exit code {result.returncode}"
        if not output.is_file() or output.stat().st_size == 0:
            return False, "compiler returned success without a non-empty PDF"
        return True, diagnostics
    except subprocess.TimeoutExpired:
        return False, f"compilation timed out after {COMPILE_TIMEOUT_SECONDS}s"
    except OSError as error:
        return False, f"could not compile fixture: {error}"


def validate_target(target: CompilerTarget, output_dir: Path, report: Report) -> None:
    if not target.compiler.is_file():
        report.failed.append(f"{target.label}: compiler not found at {target.compiler}")
        return
    actual_version, version_output = read_compiler_version(target.compiler)
    if actual_version != target.expected_version:
        report.failed.append(
            f"{target.label}: expected {target.expected_version}, got "
            f"{actual_version or 'unparseable/non-stable'} ({version_output})"
        )
        return
    report.checked_versions.append(actual_version)
    report.passed.append(f"{target.label}: compiler version {actual_version}")
    for fixture_name in target.fixtures:
        is_success, diagnostics = compile_fixture(
            target.compiler, fixture_name, output_dir / actual_version,
        )
        item = f"{target.label}: {fixture_name}"
        if is_success:
            report.passed.append(item)
            if diagnostics:
                report.warnings.append(f"{item}: {diagnostics}")
        else:
            report.failed.append(f"{item}: {diagnostics}")


def fixtures_for_version(version: str) -> tuple[str, ...]:
    numbers = tuple(map(int, version.split(".")))
    return COMMON_FIXTURES + tuple(
        name for minimum, name in FEATURE_FIXTURES
        if tuple(map(int, minimum.split("."))) <= numbers
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compiler", action="append", default=[], metavar="VERSION=PATH",
        help="exact stable release and executable path; repeat for multiple releases",
    )
    parser.add_argument("--require-all", action="store_true", help="require all seven supported releases")
    for minor, patch in LATEST_PATCHES.items():
        parser.add_argument(
            f"--typst-{minor}", dest=f"typst_{minor.replace('.', '')}", type=Path,
            help=f"legacy alias for --compiler {patch}=PATH",
        )
    args = parser.parse_args(argv)
    requested = list(args.compiler)
    for minor, patch in LATEST_PATCHES.items():
        compiler = getattr(args, f"typst_{minor.replace('.', '')}")
        if compiler is not None:
            requested.append(f"{patch}={compiler}")
    if not requested:
        parser.error("provide at least one compiler path")
    targets: dict[str, CompilerTarget] = {}
    for specification in requested:
        version, separator, path = specification.partition("=")
        if not separator or not path.strip():
            parser.error(f"expected VERSION=PATH, got {specification!r}")
        if version not in SUPPORTED_RELEASES:
            parser.error(f"unsupported stable release: {version!r}")
        if version in targets:
            parser.error(f"duplicate compiler release: {version}")
        targets[version] = CompilerTarget(
            version, Path(path).expanduser().resolve(), fixtures_for_version(version),
        )
    missing = [version for version in SUPPORTED_RELEASES if version not in targets]
    if args.require_all and missing:
        parser.error(f"--require-all is missing: {', '.join(missing)}")
    args.targets = [targets[v] for v in SUPPORTED_RELEASES if v in targets]
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = Report()
    with tempfile.TemporaryDirectory(prefix="typst-version-support-") as temp_dir:
        for target in args.targets:
            validate_target(target, Path(temp_dir), report)
    print(report.render())
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
