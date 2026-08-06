#!/usr/bin/env python3
"""Synchronize documentation from configured sibling k.LAB repositories."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9 and 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = (ROOT / "docs").resolve()
DEFAULT_MANIFEST = ROOT / "doc-sources.toml"
IGNORED_NAMES = {".DS_Store", "Thumbs.db", "__pycache__"}


@dataclass(frozen=True)
class Project:
    id: str
    title: str
    repository: Path
    source: Path
    destination: Path
    required: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="source manifest (default: doc-sources.toml)",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help="synchronize only this project ID; may be repeated",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift and exit nonzero without writing",
    )
    return parser.parse_args()


def contained_path(parent: Path, child: Path, description: str) -> Path:
    resolved = child.resolve()
    try:
        resolved.relative_to(parent.resolve())
    except ValueError as error:
        raise ValueError(f"{description} escapes {parent}: {resolved}") from error
    return resolved


def load_projects(manifest: Path) -> list[Project]:
    manifest = manifest.resolve()
    with manifest.open("rb") as stream:
        configuration = tomllib.load(stream)
    if configuration.get("version") != 1:
        raise ValueError(f"unsupported manifest version in {manifest}")

    projects: list[Project] = []
    identifiers: set[str] = set()
    destinations: set[Path] = set()
    for entry in configuration.get("projects", []):
        identifier = entry["id"]
        if identifier in identifiers:
            raise ValueError(f"duplicate project ID: {identifier}")
        repository = (ROOT / entry["repository"]).resolve()
        source = contained_path(repository, repository / entry["source"], "source path")
        destination = contained_path(
            DOCS_ROOT, DOCS_ROOT / entry["destination"], "destination path"
        )
        if destination in destinations:
            raise ValueError(f"duplicate destination: {destination}")
        identifiers.add(identifier)
        destinations.add(destination)
        projects.append(
            Project(
                id=identifier,
                title=entry.get("title", identifier),
                repository=repository,
                source=source,
                destination=destination,
                required=bool(entry.get("required", True)),
            )
        )
    return projects


def included_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and not any(part in IGNORED_NAMES for part in path.parts):
            yield path


def snapshot(root: Path) -> dict[Path, bytes]:
    if not root.is_dir():
        return {}
    return {path.relative_to(root): path.read_bytes() for path in included_files(root)}


def sources_match(source: Path, destination: Path) -> bool:
    if source.is_file():
        return destination.is_file() and source.read_bytes() == destination.read_bytes()
    source_files = snapshot(source)
    destination_files = snapshot(destination)
    if source_files.keys() != destination_files.keys():
        return False
    return all(source_files[path] == destination_files[path] for path in source_files)


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def synchronize(project: Project, check: bool) -> bool:
    if not project.source.exists():
        if project.required:
            raise FileNotFoundError(
                f"required documentation source is missing for {project.id}: {project.source}"
            )
        if project.destination.exists():
            if check:
                print(
                    f"DRIFT {project.id}: source is absent but synchronized output remains",
                    file=sys.stderr,
                )
                return False
            remove_path(project.destination)
            print(f"REMOVE {project.id}: optional source no longer exists")
            return True
        print(f"SKIP  {project.id}: {project.source} does not exist yet")
        return True

    if sources_match(project.source, project.destination):
        print(f"OK    {project.id}")
        return True

    if check:
        print(f"DRIFT {project.id}: run the synchronizer", file=sys.stderr)
        return False

    project.destination.parent.mkdir(parents=True, exist_ok=True)
    if project.source.is_file():
        remove_path(project.destination)
        shutil.copy2(project.source, project.destination)
        print(f"SYNC  {project.id}: {project.source} -> {project.destination}")
        return True

    with tempfile.TemporaryDirectory(prefix=f".{project.id}-", dir=project.destination.parent) as temp:
        staged = Path(temp) / project.destination.name
        shutil.copytree(
            project.source,
            staged,
            ignore=shutil.ignore_patterns(*IGNORED_NAMES),
        )
        remove_path(project.destination)
        staged.replace(project.destination)
    print(f"SYNC  {project.id}: {project.source} -> {project.destination}")
    return True


def main() -> int:
    args = parse_args()
    try:
        projects = load_projects(args.manifest)
        requested = set(args.project)
        known = {project.id for project in projects}
        unknown = requested - known
        if unknown:
            raise ValueError(f"unknown project ID(s): {', '.join(sorted(unknown))}")
        selected = [project for project in projects if not requested or project.id in requested]
        if not selected:
            raise ValueError("the manifest contains no projects")
        results = [synchronize(project, args.check) for project in selected]
        return 0 if all(results) else 1
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
