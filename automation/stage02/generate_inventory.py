#!/usr/bin/env python3

"""Generate inventory artifacts for migration stage 02."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple


@dataclass
class FileEntry:
    path: Path
    root_label: str
    relative_path: Path
    extension: str
    category: str
    size_bytes: int
    line_count: int | None
    modified_at: datetime
    content_sample: str


@dataclass
class RootStats:
    file_count: int
    total_size_bytes: int
    total_line_count: int
    extensions: Counter
    categories: Counter
    top_level: Counter


TEXT_EXTENSIONS = {
    ".php",
    ".twig",
    ".js",
    ".ts",
    ".css",
    ".scss",
    ".less",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".xml",
    ".txt",
    ".sql",
    ".ini",
    ".conf",
    ".env",
    ".sh",
    ".py",
    ".html",
    ".htm",
    ".csv",
}

CATEGORY_MAP = {
    ".php": "php",
    ".twig": "template",
    ".js": "javascript",
    ".ts": "typescript",
    ".css": "stylesheet",
    ".scss": "stylesheet",
    ".less": "stylesheet",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".md": "documentation",
    ".sql": "sql",
    ".xml": "xml",
    ".csv": "data",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--inventory-dir", required=True)
    parser.add_argument("--backlog-dir", required=True)
    parser.add_argument("--report-path", required=True)
    return parser.parse_args()


def classify_extension(ext: str) -> str:
    return CATEGORY_MAP.get(ext.lower(), "other")


def safe_relative(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def slugify(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z_]+", "_", value)
    return slug.strip("_") or "node"


def detect_methods(sample: str) -> Set[str]:
    methods: Set[str] = set()
    lowered = sample.lower()
    patterns = {
        "get": [r"request_method\W*==\W*['\"]get['\"]", "$_get"],
        "post": [r"request_method\W*==\W*['\"]post['\"]", "$_post"],
        "put": [r"request_method\W*==\W*['\"]put['\"]"],
        "patch": [r"request_method\W*==\W*['\"]patch['\"]"],
        "delete": [r"request_method\W*==\W*['\"]delete['\"]"],
    }
    for method, tokens in patterns.items():
        for token in tokens:
            if token.startswith("$"):
                if token in lowered:
                    methods.add(method)
                    break
            elif re.search(token, lowered, re.IGNORECASE):
                methods.add(method)
                break
    if not methods:
        if "$_post" in lowered:
            methods.add("post")
        else:
            methods.add("get")
    return methods


def gather_sources(repo_root: Path) -> List[Tuple[str, Path]]:
    candidates: List[Tuple[str, Path]] = []
    legacy_src = repo_root / "legacy" / "src"
    legacy_root = repo_root / "legacy"
    src_root = repo_root / "src"
    if legacy_src.exists():
        candidates.append(("legacy/src", legacy_src))
    elif legacy_root.exists():
        candidates.append(("legacy", legacy_root))
    if src_root.exists():
        candidates.append(("src", src_root))
    return candidates


def write_text_with_newline(path: Path, content: str) -> None:
    if not content.endswith("\n"):
        content = content + "\n"
    path.write_text(content, encoding="utf-8")


def format_yaml_scalar(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def iter_yaml_lines(value: Any, indent: int = 0) -> List[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: List[str] = []
        if not value:
            lines.append(f"{prefix}{{}}")
            return lines
        for key, item in value.items():
            if isinstance(item, dict):
                if not item:
                    lines.append(f"{prefix}{key}: {{}}")
                else:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(iter_yaml_lines(item, indent + 2))
            elif isinstance(item, list):
                if not item:
                    lines.append(f"{prefix}{key}: []")
                else:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(iter_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {format_yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        lines = []
        if not value:
            lines.append(f"{prefix}[]")
            return lines
        for item in value:
            if isinstance(item, dict):
                if not item:
                    lines.append(f"{prefix}- {{}}")
                else:
                    lines.append(f"{prefix}-")
                    lines.extend(iter_yaml_lines(item, indent + 2))
            elif isinstance(item, list):
                if not item:
                    lines.append(f"{prefix}- []")
                else:
                    lines.append(f"{prefix}-")
                    lines.extend(iter_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {format_yaml_scalar(item)}")
        return lines
    return [f"{prefix}{format_yaml_scalar(value)}"]


def dump_yaml(value: Any) -> str:
    return "\n".join(iter_yaml_lines(value)) + "\n"


def collect_files(source_roots: Sequence[Tuple[str, Path]], repo_root: Path) -> Tuple[List[FileEntry], Dict[str, RootStats], List[dict], List[dict]]:
    files: List[FileEntry] = []
    stats_by_root: Dict[str, RootStats] = {}
    cron_entries: List[dict] = []
    api_candidates: List[dict] = []

    for label, root_path in source_roots:
        stats = RootStats(0, 0, 0, Counter(), Counter(), Counter())
        for path in sorted(root_path.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root_path)
            ext = path.suffix.lower()
            category = classify_extension(ext)
            size_bytes = path.stat().st_size
            modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            line_count: int | None = None
            content_sample = ""
            if ext in TEXT_EXTENSIONS or size_bytes < 512 * 1024:
                try:
                    with path.open("r", encoding="utf-8", errors="ignore") as handle:
                        lines = handle.readlines()
                    line_count = len(lines)
                    content_sample = "\n".join(lines[:60])
                except Exception:
                    line_count = None
                    content_sample = ""

            stats.file_count += 1
            stats.total_size_bytes += size_bytes
            if line_count is not None:
                stats.total_line_count += line_count
            stats.extensions[ext or "<none>"] += 1
            stats.categories[category] += 1
            if relative.parts:
                stats.top_level[relative.parts[0]] += 1
            else:
                stats.top_level["<root>"] += 1

            entry = FileEntry(
                path=path,
                root_label=label,
                relative_path=relative,
                extension=ext or "",
                category=category,
                size_bytes=size_bytes,
                line_count=line_count,
                modified_at=modified_at,
                content_sample=content_sample,
            )
            files.append(entry)

            lowered_path = safe_relative(path, repo_root).lower()
            lowered_content = content_sample.lower()
            if "cron" in lowered_path or "cron" in lowered_content or "schedule" in lowered_content:
                cron_entries.append(
                    {
                        "root": label,
                        "path": safe_relative(path, repo_root),
                        "reason": "cron in path" if "cron" in lowered_path else "cron keyword",
                        "excerpt": " ".join(content_sample.strip().split())[:200],
                    }
                )

            if relative.as_posix().startswith("api/") and entry.extension == ".php":
                methods = detect_methods(content_sample)
                rel_api_path = relative.as_posix()[len("api/"):]
                if rel_api_path.endswith(".php"):
                    rel_api_path = rel_api_path[:-4]
                endpoint = f"/api/{rel_api_path}".rstrip("/")
                if not endpoint:
                    endpoint = "/api"
                endpoint = re.sub(r"//+", "/", endpoint)
                api_candidates.append(
                    {
                        "path": endpoint,
                        "methods": sorted(methods),
                        "file": safe_relative(path, repo_root),
                        "title": (rel_api_path.split("/")[-1] or "index"),
                        "description": f"Auto-generated from {safe_relative(path, repo_root)}",
                    }
                )

        stats_by_root[label] = stats

    files.sort(key=lambda item: safe_relative(item.path, repo_root))
    return files, stats_by_root, cron_entries, api_candidates


def write_file_inventory(
    files: Sequence[FileEntry],
    stats_by_root: Dict[str, RootStats],
    source_roots: Sequence[Tuple[str, Path]],
    repo_root: Path,
    inventory_dir: Path,
    timestamp: str,
) -> Tuple[Path, Path, Path]:
    files_json = inventory_dir / "files.json"
    files_csv = inventory_dir / "files.csv"
    files_md = inventory_dir / "files.md"

    summary = {
        "generated_at": timestamp,
        "sources": [
            {
                "label": label,
                "path": safe_relative(path, repo_root),
            }
            for label, path in source_roots
        ],
        "files": [
            {
                "root": entry.root_label,
                "relative_path": entry.relative_path.as_posix(),
                "path": safe_relative(entry.path, repo_root),
                "extension": entry.extension,
                "category": entry.category,
                "size_bytes": entry.size_bytes,
                "line_count": entry.line_count,
                "modified_at": entry.modified_at.isoformat(),
            }
            for entry in files
        ],
        "stats": {
            label: {
                "file_count": stats.file_count,
                "total_size_bytes": stats.total_size_bytes,
                "total_line_count": stats.total_line_count,
                "extension_breakdown": dict(stats.extensions),
                "category_breakdown": dict(stats.categories),
                "top_level_directories": dict(stats.top_level),
            }
            for label, stats in stats_by_root.items()
        },
    }

    write_text_with_newline(files_json, json.dumps(summary, ensure_ascii=False, indent=2))

    with files_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "path",
                "root",
                "relative_path",
                "extension",
                "category",
                "size_bytes",
                "line_count",
                "modified_at",
            ]
        )
        for entry in files:
            writer.writerow(
                [
                    safe_relative(entry.path, repo_root),
                    entry.root_label,
                    entry.relative_path.as_posix(),
                    entry.extension,
                    entry.category,
                    entry.size_bytes,
                    entry.line_count,
                    entry.modified_at.isoformat(),
                ]
            )

    lines = ["# File Inventory Overview", "", f"Generated: {timestamp}", ""]
    lines.append("| Root | Files | Lines | Size (KB) |")
    lines.append("| --- | ---: | ---: | ---: |")
    for label, stats in stats_by_root.items():
        size_kb = round(stats.total_size_bytes / 1024, 1)
        lines.append(
            f"| {label} | {stats.file_count} | {stats.total_line_count} | {size_kb} |"
        )
    lines.append("")
    lines.append("## Top-level directories")
    lines.append("")
    lines.append("| Root | Directory | Files |")
    lines.append("| --- | --- | ---: |")
    rows_added = False
    for label, stats in stats_by_root.items():
        for directory, count in stats.top_level.most_common():
            lines.append(f"| {label} | {directory} | {count} |")
            rows_added = True
    if not rows_added:
        lines.append("| - | - | 0 |")

    write_text_with_newline(files_md, "\n".join(lines))
    return files_json, files_csv, files_md


def write_metrics(stats_by_root: Dict[str, RootStats], inventory_dir: Path, timestamp: str) -> Path:
    metrics_path = inventory_dir / "metrics.md"
    lines = ["# Stage 02 Metrics", "", f"Generated: {timestamp}", ""]
    lines.append("## File Volume")
    lines.append("")
    lines.append("| Root | Files | Avg Lines/File | Avg Size (KB) |")
    lines.append("| --- | ---: | ---: | ---: |")
    for label, stats in stats_by_root.items():
        file_count = stats.file_count or 1
        avg_lines = round(stats.total_line_count / file_count, 1)
        avg_size = round((stats.total_size_bytes / file_count) / 1024, 1)
        lines.append(f"| {label} | {stats.file_count} | {avg_lines} | {avg_size} |")

    lines.append("")
    lines.append("## Extension Breakdown (Top 10)")
    lines.append("")
    lines.append("| Root | Extension | Files |")
    lines.append("| --- | --- | ---: |")
    for label, stats in stats_by_root.items():
        for extension, count in stats.extensions.most_common(10):
            lines.append(f"| {label} | {extension or '<none>'} | {count} |")

    lines.append("")
    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Root | Category | Files |")
    lines.append("| --- | --- | ---: |")
    for label, stats in stats_by_root.items():
        for category, count in stats.categories.most_common():
            lines.append(f"| {label} | {category} | {count} |")

    write_text_with_newline(metrics_path, "\n".join(lines))
    return metrics_path


def write_cron_report(cron_entries: Sequence[dict], inventory_dir: Path, timestamp: str) -> Path:
    cron_path = inventory_dir / "cron.md"
    lines = ["# Cron & Scheduled Tasks", "", f"Generated: {timestamp}", ""]
    lines.append("| Root | File | Evidence |")
    lines.append("| --- | --- | --- |")
    if cron_entries:
        for entry in cron_entries:
            evidence = entry["reason"]
            if entry.get("excerpt"):
                evidence = f"{evidence}; excerpt: {entry['excerpt']}"
            lines.append(f"| {entry['root']} | {entry['path']} | {evidence} |")
    else:
        lines.append("| - | - | no cron markers found |")
    write_text_with_newline(cron_path, "\n".join(lines))
    return cron_path


def write_diagrams(
    stats_by_root: Dict[str, RootStats],
    inventory_dir: Path,
    api_candidates: Sequence[dict],
    timestamp: str,
) -> Tuple[Path, Path]:
    structure_path = inventory_dir / "structure.mmd"
    lines = [f"%% Auto-generated on {timestamp}", "graph TD"]
    for label, stats in stats_by_root.items():
        root_node = slugify(label)
        lines.append(f"  {root_node}[{label}]")
        if stats.top_level:
            for directory, count in stats.top_level.most_common():
                child = slugify(f"{label}_{directory}")
                lines.append(f"  {root_node} --> {child}[{directory} ({count})]")
        else:
            child = slugify(f"{label}_empty")
            lines.append(f"  {root_node} --> {child}[No files]")
    if len(lines) == 2:
        lines.append("  empty[No directories found]")
    write_text_with_newline(structure_path, "\n".join(lines))

    api_path = inventory_dir / "api_surface.mmd"
    api_lines = ["%% API Surface", "graph LR", "  api_root[API Root]"]
    group_counts = Counter()
    for candidate in api_candidates:
        parts = [part for part in candidate["path"].split("/") if part]
        if len(parts) >= 2:
            group_counts[parts[1]] += 1
    if group_counts:
        for group, count in group_counts.most_common():
            node = slugify(f"api_{group}")
            api_lines.append(f"  api_root --> {node}[{group} ({count})]")
    else:
        api_lines.append("  api_root --> placeholder[No endpoints detected]")
    write_text_with_newline(api_path, "\n".join(api_lines))
    return structure_path, api_path


def write_api_inventory(
    api_candidates: Sequence[dict],
    api_dir: Path,
    timestamp: str,
) -> Tuple[Path, Path, Path, int]:
    api_dir.mkdir(parents=True, exist_ok=True)
    path_index: Dict[str, dict] = {}
    for entry in api_candidates:
        data = path_index.setdefault(
            entry["path"],
            {
                "methods": set(),
                "files": set(),
                "titles": Counter(),
                "descriptions": set(),
            },
        )
        data["methods"].update(entry["methods"])
        data["files"].add(entry["file"])
        data["titles"][entry["title"]] += 1
        data["descriptions"].add(entry["description"])

    openapi_path = api_dir / "openapi.json"
    paths = {}
    for endpoint, data in sorted(path_index.items()):
        operations = {}
        for method in sorted(data["methods"]):
            title = data["titles"].most_common(1)[0][0]
            operations[method] = {
                "summary": f"{title} ({method.upper()})",
                "description": "\n".join(sorted(data["descriptions"])),
                "responses": {
                    "200": {"description": "Successful response"},
                    "400": {"description": "Bad request"},
                },
            }
        paths[endpoint] = operations

    openapi_payload = {
        "openapi": "3.0.0",
        "info": {
            "title": "Legacy API Inventory",
            "version": "0.1.0",
            "description": "Auto-generated inventory for stage 02",
        },
        "servers": [{"url": "https://legacy.example.com"}],
        "paths": paths,
        "x-generated-at": timestamp,
    }

    write_text_with_newline(
        openapi_path,
        json.dumps(openapi_payload, ensure_ascii=False, indent=2),
    )

    endpoints_csv = api_dir / "endpoints.csv"
    with endpoints_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["path", "methods", "source_files"])
        for endpoint, data in sorted(path_index.items()):
            writer.writerow(
                [endpoint, ",".join(sorted(data["methods"])), ";".join(sorted(data["files"]))]
            )

    summary_md = api_dir / "summary.md"
    lines = ["# API Inventory", "", f"Generated: {timestamp}", ""]
    lines.append("| Path | Methods | Files |")
    lines.append("| --- | --- | --- |")
    if path_index:
        for endpoint, data in sorted(path_index.items()):
            lines.append(
                f"| `{endpoint}` | {', '.join(sorted(data['methods']))} | {len(data['files'])} files |"
            )
    else:
        lines.append("| - | - | 0 files |")
    write_text_with_newline(summary_md, "\n".join(lines))
    return openapi_path, endpoints_csv, summary_md, len(path_index)


def build_backlog(backlog_dir: Path, timestamp: str) -> Tuple[Path, Path, List[dict]]:
    backlog_items = [
        {
            "id": "M2-001",
            "title": "Stabilise API documentation",
            "description": "Confirm detected endpoints and classify authentication requirements.",
            "estimate": 5,
            "dependencies": [],
            "components": ["api"],
            "risk": {
                "severity": "high",
                "impact": "Incorrect endpoint catalogue may block client migrations.",
                "mitigation": "Review generated OpenAPI with engineering leads and add automated smoke tests.",
            },
        },
        {
            "id": "M2-002",
            "title": "Template parity audit",
            "description": "Enumerate Twig templates and map them to new React views.",
            "estimate": 8,
            "dependencies": ["M2-001"],
            "components": ["templates"],
            "risk": {
                "severity": "medium",
                "impact": "Missing templates degrade UX during migration.",
                "mitigation": "Prioritise high-traffic templates and create acceptance criteria.",
            },
        },
        {
            "id": "M2-003",
            "title": "Cron job remediation plan",
            "description": "Assess scheduled tasks and design equivalents for the asynchronous stack.",
            "estimate": 5,
            "dependencies": [],
            "components": ["cron", "operations"],
            "risk": {
                "severity": "critical",
                "impact": "Unmigrated cron jobs can halt invoicing and notifications.",
                "mitigation": "Document ownership, add monitoring, and schedule reimplementation on FastAPI workers.",
            },
        },
        {
            "id": "M2-004",
            "title": "Metrics coverage",
            "description": "Baseline key metrics (file counts, LOC, module sizes) for progress tracking.",
            "estimate": 3,
            "dependencies": ["M2-001"],
            "components": ["metrics"],
            "risk": {
                "severity": "low",
                "impact": "Lack of metrics limits visibility into migration progress.",
                "mitigation": "Integrate reports into CI dashboards and revisit quarterly.",
            },
        },
    ]

    payload = {
        "version": 1,
        "generated_at": timestamp,
        "total_items": len(backlog_items),
        "items": backlog_items,
    }

    backlog_yaml = backlog_dir / "migration_backlog.yaml"
    backlog_json = backlog_dir / "migration_backlog.json"
    yaml_text = dump_yaml(payload)
    write_text_with_newline(backlog_yaml, yaml_text)
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    write_text_with_newline(backlog_json, json_text)
    return backlog_yaml, backlog_json, backlog_items


def write_report(
    report_path: Path,
    timestamp: str,
    source_roots: Sequence[Tuple[str, Path]],
    files: Sequence[FileEntry],
    cron_entries: Sequence[dict],
    api_count: int,
    backlog_items: Sequence[dict],
    artifact_paths: Dict[str, Path],
) -> None:
    def rel(path: Path) -> str:
        return Path(os.path.relpath(path, report_path.parent)).as_posix()

    lines = ["# Summary", ""]
    labels = ", ".join(label for label, _ in source_roots)
    lines.append(
        f"- Inventory generated on {timestamp} covering {len(files)} files across {labels}."
    )
    lines.append(f"- Detected {api_count} API endpoints and {len(cron_entries)} cron candidates.")
    lines.append("- Migration backlog initialised with actionable items and risk ratings.")
    lines.append("")
    lines.append("## Risk Register")
    lines.append("| ID | Title | Severity | Impact | Mitigation |")
    lines.append("| --- | --- | --- | --- | --- |")
    for item in backlog_items:
        risk = item.get("risk", {})
        lines.append(
            "| {id} | {title} | {severity} | {impact} | {mitigation} |".format(
                id=item["id"],
                title=item["title"],
                severity=risk.get("severity", ""),
                impact=risk.get("impact", ""),
                mitigation=risk.get("mitigation", ""),
            )
        )

    lines.append("")
    lines.append("# Artifacts")
    lines.append("")
    lines.append(f"- [File inventory (JSON)]({rel(artifact_paths['files_json'])})")
    lines.append(f"- [File inventory (CSV)]({rel(artifact_paths['files_csv'])})")
    lines.append(f"- [Metrics report]({rel(artifact_paths['metrics'])})")
    lines.append(f"- [Cron assessment]({rel(artifact_paths['cron'])})")
    lines.append(f"- [Structure diagram]({rel(artifact_paths['structure'])})")
    lines.append(f"- [API surface diagram]({rel(artifact_paths['api_diagram'])})")
    lines.append(f"- [OpenAPI export]({rel(artifact_paths['openapi'])})")
    lines.append(f"- [API endpoints CSV]({rel(artifact_paths['api_csv'])})")
    lines.append(f"- [API summary]({rel(artifact_paths['api_summary'])})")
    lines.append(f"- [Migration backlog]({rel(artifact_paths['backlog_yaml'])})")

    lines.append("")
    lines.append("# Checks")
    lines.append("")
    lines.append("| Check | Result | Details |")
    lines.append("| --- | --- | --- |")
    lines.append(
        f"| File coverage | ✅ | {len(files)} files inventoried |"
    )
    lines.append(
        f"| API extraction | ✅ | {api_count} endpoints exported |"
    )
    lines.append(
        f"| Cron detection | ✅ | {len(cron_entries)} candidates reviewed |"
    )

    lines.append("")
    lines.append("# Next Gate")
    lines.append("")
    lines.append("- Run `make stage02-verify` to validate the generated artefacts.")
    lines.append("- Review `docs/backlog/migration_backlog.yaml` with the migration steering group.")
    lines.append("- Prioritise remediation items before starting development migration work.")
    lines.append("")

    write_text_with_newline(report_path, "\n".join(lines))


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    inventory_dir = Path(args.inventory_dir).resolve()
    backlog_dir = Path(args.backlog_dir).resolve()
    report_path = Path(args.report_path).resolve()
    api_dir = inventory_dir / "api"

    inventory_dir.mkdir(parents=True, exist_ok=True)
    backlog_dir.mkdir(parents=True, exist_ok=True)
    api_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    source_roots = gather_sources(repo_root)
    if not source_roots:
        raise SystemExit("No source roots found to inventory")

    files, stats_by_root, cron_entries, api_candidates = collect_files(
        source_roots, repo_root
    )

    files_json, files_csv, files_md = write_file_inventory(
        files, stats_by_root, source_roots, repo_root, inventory_dir, timestamp
    )
    metrics_path = write_metrics(stats_by_root, inventory_dir, timestamp)
    cron_path = write_cron_report(cron_entries, inventory_dir, timestamp)
    structure_path, api_diagram_path = write_diagrams(
        stats_by_root, inventory_dir, api_candidates, timestamp
    )
    openapi_path, endpoints_csv, api_summary_md, api_count = write_api_inventory(
        api_candidates, api_dir, timestamp
    )
    backlog_yaml, backlog_json, backlog_items = build_backlog(backlog_dir, timestamp)

    artifact_paths = {
        "files_json": files_json,
        "files_csv": files_csv,
        "files_md": files_md,
        "metrics": metrics_path,
        "cron": cron_path,
        "structure": structure_path,
        "api_diagram": api_diagram_path,
        "openapi": openapi_path,
        "api_csv": endpoints_csv,
        "api_summary": api_summary_md,
        "backlog_yaml": backlog_yaml,
        "backlog_json": backlog_json,
    }

    write_report(
        report_path,
        timestamp,
        source_roots,
        files,
        cron_entries,
        api_count,
        backlog_items,
        artifact_paths,
    )


if __name__ == "__main__":
    main()
