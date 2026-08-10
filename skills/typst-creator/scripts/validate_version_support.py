#!/usr/bin/env python3
"""Compile Typst compatibility fixtures with explicitly supplied compilers."""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = SKILL_ROOT / "evals" / "fixtures"
VERSION_PATTERN = re.compile(r"\btypst\s+(\d+\.\d+\.\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class CompilerTarget:
    label: str
    expected_version: str
    compiler: Path
    fixtures: tuple[str, ...]


@dataclass
class Report:
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"PASS: {item}" for item in self.passed]
        lines.extend(f"FAIL: {item}" for item in self.failed)
        lines.append(f"Summary: {len(self.passed)} passed, {len(self.failed)} failed")
        return "\n".join(lines)


def read_compiler_version(compiler: Path) -> tuple[str | None, str]:
    result = subprocess.run(
        [str(compiler), "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    if result.returncode != 0:
        return None, output or f"exit code {result.returncode}"
    match = VERSION_PATTERN.search(output)
    return (match.group(1) if match else None), output


def compile_fixture(compiler: Path, fixture_name: str, output_dir: Path) -> tuple[bool, str]:
    fixture = FIXTURE_ROOT / fixture_name
    output = output_dir / f"{compiler.name}-{fixture.stem}.pdf"
    result = subprocess.run(
        [
            str(compiler),
            "compile",
            "--root",
            str(SKILL_ROOT),
            str(fixture),
            str(output),
        ],
        cwd=SKILL_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    diagnostics = "\n".join(
        part for part in (result.stdout.strip(), result.stderr.strip()) if part
    )
    if result.returncode != 0:
        return False, diagnostics or f"exit code {result.returncode}"
    if not output.is_file() or output.stat().st_size == 0:
        return False, "compiler returned success without a non-empty PDF"
    return True, diagnostics


def validate_target(target: CompilerTarget, output_dir: Path, report: Report) -> None:
    if not target.compiler.is_file():
        report.failed.append(f"{target.label}: compiler not found at {target.compiler}")
        return

    actual_version, version_output = read_compiler_version(target.compiler)
    if actual_version != target.expected_version:
        report.failed.append(
            f"{target.label}: expected {target.expected_version}, got "
            f"{actual_version or 'unparseable'} ({version_output})"
        )
        return

    report.passed.append(f"{target.label}: compiler version {actual_version}")
    for fixture_name in target.fixtures:
        is_success, diagnostics = compile_fixture(target.compiler, fixture_name, output_dir)
        item = f"{target.label}: {fixture_name}"
        if is_success:
            report.passed.append(item)
        else:
            report.failed.append(f"{item}: {diagnostics}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile common and version-specific fixtures with exact Typst compilers."
    )
    parser.add_argument("--typst-0.13", dest="typst_013", type=Path)
    parser.add_argument("--typst-0.14", dest="typst_014", type=Path)
    parser.add_argument("--typst-0.15", dest="typst_015", type=Path)
    args = parser.parse_args()
    if not any((args.typst_013, args.typst_014, args.typst_015)):
        parser.error("provide at least one compiler path")
    return args


def main() -> int:
    args = parse_args()
    candidates = (
        ("Typst 0.13", "0.13.1", args.typst_013, "typst-0.13.typ"),
        ("Typst 0.14", "0.14.2", args.typst_014, "typst-0.14.typ"),
        ("Typst 0.15", "0.15.1", args.typst_015, "typst-0.15.typ"),
    )
    targets = [
        CompilerTarget(
            label=label,
            expected_version=expected_version,
            compiler=compiler.resolve(),
            fixtures=("common.typ", version_fixture),
        )
        for label, expected_version, compiler, version_fixture in candidates
        if compiler is not None
    ]

    report = Report()
    with tempfile.TemporaryDirectory(prefix="typst-version-support-") as temp_dir:
        output_dir = Path(temp_dir)
        for target in targets:
            validate_target(target, output_dir, report)

    print(report.render())
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
