#!/usr/bin/env python3
"""Collect recent local debug evidence for ai_customer_mining."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import re
import subprocess
from collections import deque
from pathlib import Path
from typing import Iterable


LOG_FILES = [
    ("client", Path("client/.next/dev/logs/next-development.log")),
    ("server", Path("server/.next/dev/logs/next-development.log")),
]

DEFAULT_KEYWORDS = [
    "error",
    "failed",
    "exception",
    "warn",
    "RuntimeService",
    "tool-runner",
    "RuntimeHook",
    "DrizzleRuntimeRepository",
    "ClientBridgeRuntime",
    "client-bridge",
    "BRIDGE_ACTION",
    "xhs",
    "login_required",
    "turnId",
    "sessionId",
]

NOISE_KEYWORDS = [
    "client.heartbeat",
    "touchHeartbeat",
    "handleHeartbeat",
    "ClientRegistryService.heartbeat",
    "cleanupExpiredConnections",
    "removeExpiredConnections",
]


def run_command(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except FileNotFoundError:
        return f"[missing command] {command[0]}"
    return result.stdout.strip() or "(no output)"


def find_repo_root(start: Path) -> Path:
    candidates = [start, *start.parents]
    for candidate in candidates:
        if (candidate / "client").is_dir() and (candidate / "server").is_dir() and (candidate / ".codex").is_dir():
            return candidate
    script_path = Path(__file__).resolve()
    for candidate in [script_path, *script_path.parents]:
        if (candidate / "client").is_dir() and (candidate / "server").is_dir() and (candidate / ".codex").is_dir():
            return candidate
    return start


def tail_lines(path: Path, limit: int) -> list[str]:
    if not path.exists():
        return []
    lines: deque[str] = deque(maxlen=limit)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            lines.append(line.rstrip("\n"))
    return list(lines)


def parse_message(line: str) -> str:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return line
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str):
            return message
    return line


def extract_terms(query: str) -> list[str]:
    terms: list[str] = []
    for term in re.findall(r"[\w.\-:/@\u4e00-\u9fff]+", query):
        if len(term) >= 2:
            terms.append(term)
    return terms


def unique_terms(terms: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for term in terms:
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(term)
    return result


def find_matches(
    lines: list[str],
    keywords: list[str],
    limit: int,
    noise_keywords: list[str] | None = None,
) -> list[str]:
    if not keywords:
        return []
    pattern = re.compile("|".join(re.escape(item) for item in keywords), re.IGNORECASE)
    noise_pattern = None
    if noise_keywords:
        noise_pattern = re.compile("|".join(re.escape(item) for item in noise_keywords), re.IGNORECASE)
    matches: deque[str] = deque(maxlen=limit)
    for line in lines:
        message = parse_message(line)
        if noise_pattern and noise_pattern.search(message):
            continue
        if pattern.search(message):
            matches.append(message)
    return list(matches)


def print_section(title: str, body: str | list[str]) -> None:
    print(f"\n## {title}")
    if isinstance(body, list):
        if not body:
            print("(none)")
            return
        for line in body:
            print(line)
        return
    print(body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="", help="User issue description or keywords.")
    parser.add_argument("--lines", type=int, default=200, help="Tail lines per log file.")
    parser.add_argument("--matches", type=int, default=80, help="Maximum match lines per section.")
    args = parser.parse_args()

    root = find_repo_root(Path.cwd().resolve())
    os_cwd = Path.cwd().resolve()
    if os_cwd != root:
        os.chdir(root)
    query_terms = extract_terms(args.query)
    all_keywords = unique_terms([*query_terms, *DEFAULT_KEYWORDS])
    suppress_noise = not any(term.lower() == "heartbeat" for term in query_terms)

    print("# Local Debug Evidence")
    print(f"root: {root}")
    if os_cwd != root:
        print(f"called_from: {os_cwd}")
    if args.query:
        print(f"query: {args.query}")
    print(f"keywords: {', '.join(all_keywords[:40])}")

    print_section(
        "Dev Processes",
        run_command(["bash", "-lc", "ps aux | rg 'pnpm|next dev|tauri dev|cargo|red-mine|redmine-server' | rg -v 'rg '"]),
    )
    print_section("Ports 3000/8787", run_command(["bash", "-lc", "lsof -nP -iTCP:3000 -iTCP:8787"]))

    for label, path in LOG_FILES:
        lines = tail_lines(path, args.lines)
        if not lines:
            print_section(f"{label} log status", f"missing or empty: {path}")
            continue

        stat = path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime).astimezone().strftime("%Y-%m-%d %H:%M:%S %z")

        print_section(
            f"{label} log summary",
            [
                f"path: {path}",
                f"size: {stat.st_size} bytes",
                f"modified: {modified or stat.st_mtime}",
                f"tail_lines: {len(lines)}",
            ],
        )
        print_section(
            f"{label} errors and warnings",
            find_matches(lines, ["error", "failed", "exception", "warn"], args.matches),
        )
        print_section(
            f"{label} query/high-signal matches",
            find_matches(lines, all_keywords, args.matches, NOISE_KEYWORDS if suppress_noise else None),
        )
        print_section(f"{label} recent tail", [parse_message(line) for line in lines[-min(60, len(lines)) :]])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
