"""
CLI entrypoint for shea.

Provides directory listing similar to `ls`, and an optional tree view similar to `tree`.

Usage examples:
    shea
    shea -t
    shea --tree --depth 2 ~/projects
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__

ICON_DIR = "📁"
ICON_FILE = "📄"


def _is_hidden(name: str) -> bool:
    """
    Return True if the filename should be considered hidden.

    Currently treats names starting with '.' as hidden (POSIX style).
    """
    return name.startswith(".")


def _iter_entries(path: str, *, show_all: bool) -> list[os.DirEntry]:
    """
    Return a sorted list of DirEntry objects for the given directory.

    Sort order: directories first, then files; each group sorted by name (case-insensitive).
    Hidden files are filtered unless show_all is True.
    """
    try:
        with os.scandir(path) as it:
            entries = [e for e in it if show_all or not _is_hidden(e.name)]
    except PermissionError:
        print(f"shea: permission denied: {path}", file=sys.stderr)
        return []
    # Directories first, then files; case-insensitive by name
    entries.sort(key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()))
    return entries


def print_listing(path: str, *, show_all: bool = False) -> None:
    """
    Print a flat listing of a directory or file.

    - Directories listed before files, each sorted by name.
    - Uses icons for folders and files.
    """
    if Path(path).is_dir():
        for entry in _iter_entries(path, show_all=show_all):
            icon = ICON_DIR if entry.is_dir(follow_symlinks=False) else ICON_FILE
            print(f"{icon} {entry.name}")
    elif Path(path).is_file():
        print(f"{ICON_FILE} {Path(path).name}")
    else:
        print(f"shea: no such file or directory: {path}", file=sys.stderr)


def print_tree(path: str, *, show_all: bool = False, max_depth: int | None = None) -> None:
    """
    Print a tree view of the path.

    If path is a directory, prints its contents recursively.
    If it's a file, prints just the file name.
    max_depth=None means unlimited. If max_depth=0, only the root line is printed for directories.
    """
    # Normalize path for display
    if Path(path).is_file():
        print(f"{ICON_FILE} {path.name}")
        return

    if not Path(path).is_dir():
        print(f"shea: no such file or directory: {path}", file=sys.stderr)
        return

    # Print the root
    root_label = path.name
    print(root_label if root_label != "" else ".")

    if max_depth == 0:
        return

    def walk(dir_path: str, prefix: str, depth_left: int | None) -> None:
        entries = _iter_entries(dir_path, show_all=show_all)
        total = len(entries)
        for idx, entry in enumerate(entries):
            is_last = idx == total - 1
            connector = "└── " if is_last else "├── "
            icon = ICON_DIR if entry.is_dir(follow_symlinks=False) else ICON_FILE
            print(f"{prefix}{connector}{icon} {entry.name}")

            if entry.is_dir(follow_symlinks=False) and (depth_left is None or depth_left > 0):
                new_prefix = f"{prefix}{'    ' if is_last else '│   '}"
                walk(entry.path, new_prefix, None if depth_left is None else depth_left - 1)

    walk(path, "", None if max_depth is None else max_depth - 1)


def build_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser for the shea CLI."""
    parser = argparse.ArgumentParser(
        prog="shea",
        description="List directory contents with optional tree view.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"shea {__version__}",
        help="Show version and exit",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory or file to list (default: .)",
    )
    parser.add_argument(
        "-t",
        "--tree",
        action="store_true",
        help="Show tree view (recursive)",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Include hidden files (starting with .)",
    )
    parser.add_argument(
        "-d",
        "--depth",
        type=int,
        default=None,
        help="Maximum recursion depth for tree view (0 means root only)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns an exit status code (0 on success)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    path = Path(args.path).expanduser()
    # Validate depth
    if args.depth is not None and args.depth < 0:
        print("shea: depth must be >= 0", file=sys.stderr)
        return 2

    try:
        if args.tree:
            print_tree(path, show_all=args.all, max_depth=args.depth)
        else:
            print_listing(path, show_all=args.all)
    except KeyboardInterrupt:
        return 130
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
