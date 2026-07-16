#!/usr/bin/env python3
"""Create a registered Forge app through a controlled non-interactive command."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from .forge_env import forge_env
_FORGE_ENV = forge_env()
_BLANK_TEMPLATE = "blank"
_DEV_SPACE_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def command_available(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            env=_FORGE_ENV,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def validate_prerequisites():
    """Check command availability; retrieve version requirements before calling."""
    return command_available(["node", "--version"]) and command_available(
        ["forge", "--version"]
    )


def discover_dev_spaces():
    """Return Developer Spaces reported by the current Forge CLI."""
    try:
        result = subprocess.run(
            ["forge", "developer-spaces", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=_FORGE_ENV,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Could not run Forge Developer Space discovery: {exc}") from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Forge Developer Space discovery failed: {detail}")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Forge returned invalid Developer Space JSON") from exc

    if isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict):
        entries = payload.get("data", payload.get("spaces", []))
    else:
        raise RuntimeError("Forge returned an unexpected Developer Space schema")
    if not isinstance(entries, list):
        raise RuntimeError("Forge returned an unexpected Developer Space schema")
    return [
        {"id": item.get("id") or item.get("developerSpaceId"), "name": item.get("name", "")}
        for item in entries
        if isinstance(item, dict) and (item.get("id") or item.get("developerSpaceId"))
    ]


def _validate_creation_inputs(app_name, dev_space_id, accept_terms):
    if not isinstance(app_name, str) or not app_name.strip():
        raise RuntimeError("App name must not be empty")
    if app_name != app_name.strip():
        raise RuntimeError("App name must not start or end with whitespace")
    if app_name in {".", ".."} or app_name.startswith("-"):
        raise RuntimeError("App name is not safe for non-interactive creation")
    if any(char in app_name for char in ("/", "\\", "\x00")):
        raise RuntimeError("App name must be a single directory name")
    if not isinstance(dev_space_id, str) or _DEV_SPACE_ID_RE.fullmatch(dev_space_id) is None:
        raise RuntimeError("Developer Space ID must be a UUID")
    if not accept_terms:
        raise RuntimeError(
            "Explicit authorization to accept current Forge terms and applicable billing consent is required"
        )


def create_app(
    app_name,
    dev_space_id,
    template=None,
    blank=False,
    output_dir=None,
    accept_terms=False,
):
    """Run forge create for a documented template or the blank-app branch."""
    if not validate_prerequisites():
        raise RuntimeError("Node.js and the Forge CLI must be available")

    _validate_creation_inputs(app_name, dev_space_id, accept_terms)

    if blank == (template is not None):
        raise RuntimeError("Choose exactly one of a documented template or the blank branch")
    if template is not None and not template.strip():
        raise RuntimeError("Template must not be empty")
    selected_template = _BLANK_TEMPLATE if blank else template.strip()

    parent = Path(output_dir or os.getcwd()).expanduser().resolve()
    if not parent.is_dir():
        raise RuntimeError(f"Parent directory does not exist: {parent}")
    app_path = parent / app_name
    if app_path.exists():
        raise RuntimeError(f"Target already exists: {app_path}")

    command = [
        "forge",
        "create",
        "--template",
        selected_template,
        "--directory",
        app_name,
        "--developer-space-id",
        dev_space_id,
        "--accept-terms",
        app_name,
    ]
    return subprocess.run(
        command,
        cwd=parent,
        capture_output=True,
        text=True,
        check=False,
        env=_FORGE_ENV,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    scaffold = parser.add_mutually_exclusive_group(required=True)
    scaffold.add_argument(
        "--template",
        help="current documented Forge template name",
    )
    scaffold.add_argument(
        "--blank",
        action="store_true",
        help="create a registered blank app for deliberate module composition",
    )
    parser.add_argument("--name", required=True)
    parser.add_argument("--dev-space-id", required=True)
    parser.add_argument("--directory", help="parent directory in which to create the app")
    parser.add_argument(
        "--accept-terms",
        action="store_true",
        help="confirm explicit authorization to accept current Forge terms and applicable billing consent",
    )
    args = parser.parse_args()

    try:
        result = create_app(
            args.name,
            args.dev_space_id,
            template=args.template,
            blank=args.blank,
            output_dir=args.directory,
            accept_terms=args.accept_terms,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    if result.returncode != 0:
        print("forge create failed; do not manually scaffold a replacement", file=sys.stderr)
        return result.returncode
    print(f"Created registered Forge app: {Path(args.directory or os.getcwd()) / args.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
