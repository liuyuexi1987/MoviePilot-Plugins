#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request


REPO_API = "https://api.github.com/repos/jxxghp/MoviePilot"
RAW_BASE = "https://raw.githubusercontent.com/jxxghp/MoviePilot"

CHECKS = {
    "plugin_base": {
        "path": "app/plugins/__init__.py",
        "patterns": [
            r"class\s+_PluginBase\b",
        ],
    },
    "metainfo": {
        "path": "app/core/metainfo.py",
        "patterns": [
            r"(?:class|def)\s+MetaInfo\b",
        ],
    },
    "download_chain": {
        "path": "app/chain/download.py",
        "patterns": [
            r"def\s+download_single\s*\(",
            r"save_path:\s*Optional",
            r"def\s+batch_download\s*\(",
        ],
    },
    "subscribe_chain": {
        "path": "app/chain/subscribe.py",
        "patterns": [
            r"def\s+add\s*\(",
            r"'save_path':\s*self\.__get_default_subscribe_config",
            r"SubscribeOper\(\)\.add",
        ],
    },
    "agent_llm_init": {
        "path": "app/agent/llm/__init__.py",
        "patterns": [
            r"from\s+app\.agent\.llm\.helper\s+import\s+LLMHelper",
        ],
    },
    "agent_llm_helper": {
        "path": "app/agent/llm/helper.py",
        "patterns": [
            r"class\s+LLMHelper\b",
            r"async\s+def\s+get_llm\s*\(",
        ],
    },
    "agent_tool_manager": {
        "path": "app/agent/tools/manager.py",
        "patterns": [
            r"moviepilot_tool_manager\s*=",
        ],
    },
    "agent_tool_base": {
        "path": "app/agent/tools/base.py",
        "patterns": [
            r"class\s+MoviePilotTool\b",
        ],
    },
    "schema_types": {
        "path": "app/schemas/types.py",
        "patterns": [
            r"def\s+media_type_to_agent\s*\(",
            r"class\s+TorrentStatus\b",
            r"class\s+EventType\b",
            r"class\s+ChainEventType\b",
            r"class\s+SystemConfigKey\b",
        ],
    },
}


def show_help() -> None:
    print(
        "Usage:\n"
        "  python3 scripts/check-moviepilot-upstream-compat.py\n"
        "  python3 scripts/check-moviepilot-upstream-compat.py --tag v2.11.4\n\n"
        "Fetches the latest MoviePilot release (or a specific tag) from GitHub and\n"
        "verifies that the upstream files and signatures relied on by this repo are\n"
        "still present."
    )


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"Accept": "text/plain"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def latest_release() -> dict:
    return fetch_json(f"{REPO_API}/releases/latest")


def resolve_tag(explicit_tag: str | None) -> tuple[str, str]:
    if explicit_tag:
        return explicit_tag, f"https://github.com/jxxghp/MoviePilot/releases/tag/{explicit_tag}"
    release = latest_release()
    tag = str(release.get("tag_name") or "").strip()
    if not tag:
        raise RuntimeError("GitHub latest release missing tag_name")
    return tag, str(release.get("html_url") or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--tag", dest="tag")
    parser.add_argument("--help", "-h", action="store_true")
    args = parser.parse_args()
    if args.help:
        show_help()
        return 0

    try:
        tag, release_url = resolve_tag(args.tag)
    except urllib.error.HTTPError as exc:
        print(f"moviepilot_upstream_compat_failed latest_release_http_{exc.code}")
        return 1
    except Exception as exc:
        print(f"moviepilot_upstream_compat_failed latest_release {exc}")
        return 1

    failures: list[str] = []
    checked = 0
    for name, spec in CHECKS.items():
        path = spec["path"]
        raw_url = f"{RAW_BASE}/{tag}/{path}"
        try:
            text = fetch_text(raw_url)
        except urllib.error.HTTPError as exc:
            failures.append(f"{name}: {path} http_{exc.code}")
            continue
        except Exception as exc:
            failures.append(f"{name}: {path} {exc}")
            continue
        missing = [
            pattern
            for pattern in spec["patterns"]
            if not re.search(pattern, text, re.MULTILINE)
        ]
        if missing:
            failures.append(f"{name}: {path} missing_patterns={len(missing)}")
            continue
        checked += 1

    if failures:
        print("moviepilot_upstream_compat_failed")
        print(f"tag={tag}")
        for item in failures:
            print(item)
        return 1

    print(
        f"moviepilot_upstream_compat_ok tag={tag} checks={checked} "
        f"release={release_url}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
