"""
Interactive disk usage viewer for pydisk.

Provides disk usage information and an interactive directory explorer.

Usage examples:
    pydisk                  # Show all disk partitions
    pydisk /               # Interactive mode for root partition
    pydisk /home           # Interactive mode for home partition
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import ClassVar

try:
    import psutil
except ImportError:
    print(
        "Error: psutil is required for pydisk. Install it with: pip install psutil",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from rich.text import Text
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.widgets import DataTable, Footer, Header, Static
except ImportError:
    print(
        "Error: textual is required for pydisk. Install it with: pip install textual",
        file=sys.stderr,
    )
    sys.exit(1)

from . import __version__

BYTES_UNIT = 1024.0
THRESH_RED = 90
THRESH_YELLOW = 70
THRESH_CYAN = 50
ICON_DIR = "📁"
ICON_FILE = "📄"
ICON_DISK = "💾"


def _format_bytes(bytes_val: float) -> str:
    """Format bytes into human-readable format."""
    if bytes_val < 0:
        return "0B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < BYTES_UNIT:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= BYTES_UNIT
    return f"{bytes_val:.1f}PB"


def _get_usage_color(percent: float) -> str:
    """Get color based on usage percentage."""
    if percent >= THRESH_RED:
        return "red"
    if percent >= THRESH_YELLOW:
        return "yellow"
    if percent >= THRESH_CYAN:
        return "cyan"
    return "green"


def _create_bar(
    percent: float,
    width: int = 20,
    *,
    filled_char: str = "█",
    empty_char: str = "░",
) -> str:
    """Create a visual progress bar."""
    filled = int(percent / 100 * width)
    empty = width - filled
    return f"{filled_char * filled}{empty_char * empty}"


def print_disks() -> None:
    """Print a table of all disk partitions with their usage."""
    partitions = psutil.disk_partitions(all=False)

    if not partitions:
        print("No disk partitions found.", file=sys.stderr)
        return

    # Print header
    print(f"{ICON_DISK} Disk Usage")
    print("=" * 100)
    print(f"{'Device':<20} {'Usage':<10} {'Used / Total':<25} {'Bar':<20} {'Mount Point':<20} ")
    print("-" * 100)

    for partition in partitions:
        # Check permissions first to avoid exception in loop
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except (PermissionError, OSError):
            # Skip partitions we can't access
            continue

        try:
            percent = usage.percent
            color_code = _get_usage_color(percent)

            # ANSI color codes
            colors = {
                "red": "\033[91m",
                "yellow": "\033[93m",
                "cyan": "\033[96m",
                "green": "\033[92m",
            }
            reset = "\033[0m"
            color = colors.get(color_code, "")

            used_str = _format_bytes(usage.used)
            total_str = _format_bytes(usage.total)
            bar = _create_bar(percent)

            print(
                f"{partition.device:<20} "
                f"{color}{percent:>6.1f}%{reset}   "
                f"{used_str:>8} / {total_str:<8} "
                f"{color}{bar}{reset} "
                f"{partition.mountpoint:<20}",
            )
        except (OSError, ValueError, AttributeError):
            # Skip partitions with invalid data or formatting issues
            continue

    print("=" * 100)


def _get_dir_size(path: Path, cache: dict[str, int] | None = None) -> int:
    """
    Calculate total size of a directory recursively.

    Args:
        path: The directory path to calculate size for
        cache: Optional cache dictionary to store/retrieve calculated sizes

    Returns:
        Total size in bytes

    """
    # Check cache first if provided
    if cache is not None:
        path_str = str(path.resolve())
        if path_str in cache:
            return cache[path_str]

    total = 0
    try:
        for entry in path.iterdir():
            try:
                # Skip symbolic links to avoid infinite loops
                if entry.is_symlink():
                    continue
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    # Recursively get size and cache subdirectories
                    subdir_size = _get_dir_size(entry, cache)
                    total += subdir_size
            except (PermissionError, OSError):
                # Skip files/dirs we can't access
                continue
    except (PermissionError, OSError):
        pass

    # Store in cache if provided
    if cache is not None:
        path_str = str(path.resolve())
        cache[path_str] = total

    return total


class DiskExplorerApp(App):
    """Interactive disk usage explorer application."""

    BINDINGS: ClassVar = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("u", "up", "Go Up"),
        ("escape", "up", "Go Up"),
        Binding("shift+r", "clear_cache", "Clear All Cache", show=False),
    ]

    CSS = """
    Screen {
        background: $surface;
    }

    #path_display {
        height: 3;
        background: $primary;
        color: $text;
        padding: 1;
        text-align: center;
    }

    #stats {
        height: 3;
        background: $panel;
        color: $text;
        padding: 1;
    }

    DataTable {
        height: 1fr;
    }

    DataTable > .datatable--header {
        background: $accent;
        color: $text;
    }

    DataTable > .datatable--cursor {
        background: $secondary;
    }
    """

    def __init__(self, start_path: Path) -> None:
        """Initialize the app with a starting path."""
        super().__init__()
        self.current_path = start_path.resolve()
        self.sort_column = "size"
        self.sort_reverse = True
        self.size_cache: dict[str, int] = {}  # Cache for directory sizes

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Static(id="path_display")
        yield Static(id="stats")
        yield DataTable(id="entries", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the app when mounted."""
        table = self.query_one(DataTable)
        table.add_columns("Type", "Name", "Size", "Size (Bytes)")
        table.cursor_type = "row"
        self.update_display()

    def update_display(self) -> None:
        """Update the display with current directory contents."""
        path_display = self.query_one("#path_display", Static)
        stats_display = self.query_one("#stats", Static)
        table = self.query_one(DataTable)

        # Update path display
        path_display.update(f"📂 Current Path: {self.current_path}")

        # Get disk usage for current partition
        try:
            usage = psutil.disk_usage(str(self.current_path))
            percent = usage.percent
            used_str = _format_bytes(usage.used)
            total_str = _format_bytes(usage.total)
            bar = _create_bar(percent, width=30)
            stats_display.update(
                f"Disk Usage: {percent:.1f}% ({used_str} / {total_str})  {bar}",
            )
        except (PermissionError, OSError):
            stats_display.update("Disk Usage: N/A")

        # Clear and populate table
        table.clear()

        entries = []

        try:
            # Get all entries in the directory
            for entry in self.current_path.iterdir():
                try:
                    # Skip symbolic links
                    if entry.is_symlink():
                        continue

                    is_dir = entry.is_dir()

                    if is_dir:
                        # Check cache first
                        entry_path_str = str(entry.resolve())
                        if entry_path_str not in self.size_cache:
                            # Pass cache to _get_dir_size so it can populate subdirectories too
                            size = _get_dir_size(entry, self.size_cache)
                        else:
                            size = self.size_cache[entry_path_str]
                        icon = ICON_DIR
                    else:
                        size = entry.stat().st_size
                        icon = ICON_FILE

                    entries.append(
                        {
                            "icon": icon,
                            "name": entry.name,
                            "size": size,
                            "is_dir": is_dir,
                            "path": entry,
                        },
                    )
                except (PermissionError, OSError):
                    # Skip entries we can't access
                    continue
        except (PermissionError, OSError):
            self.notify("Permission denied", severity="error")
            return

        # Sort entries
        entries.sort(key=lambda e: e["size"], reverse=True)

        # Add ".." entry at the top if not at root
        parent = self.current_path.parent
        if parent != self.current_path:
            table.add_row(
                "⬆️",
                "..",
                "<DIR>",
                "0",
                key=str(parent),
            )

        # Add rows to table
        for entry in entries:
            size_str = _format_bytes(entry["size"])
            table.add_row(
                entry["icon"],
                entry["name"],
                Text(size_str, justify="right"),
                Text(str(entry["size"]), justify="right"),
                key=str(entry["path"]),
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection - navigate into directories."""
        row_key = event.row_key
        path = Path(row_key.value)

        if path.is_dir():
            self.current_path = path
            self.update_display()
            # Show appropriate message
            if path.name == "..":
                self.notify(f"Up to: {path}")
            else:
                self.notify(f"Entered: {path.name}")
        else:
            # Show file info
            try:
                size = path.stat().st_size
                size_str = _format_bytes(size)
                self.notify(f"File: {path.name} ({size_str})")
            except (PermissionError, OSError):
                self.notify("Cannot access file", severity="error")

    def action_up(self) -> None:
        """Go up one directory level."""
        parent = self.current_path.parent
        if parent != self.current_path:
            self.current_path = parent
            self.update_display()
            self.notify(f"Up to: {self.current_path}")
        else:
            self.notify("Already at root", severity="warning")

    def action_refresh(self) -> None:
        """Refresh the current directory display, clearing cache for this directory."""
        # Clear cache for entries in current directory to force recalculation
        try:
            for entry in self.current_path.iterdir():
                entry_path_str = str(entry.resolve())
                if entry_path_str in self.size_cache:
                    del self.size_cache[entry_path_str]
        except (PermissionError, OSError):
            pass

        self.update_display()
        self.notify("Refreshed (cache cleared for current directory)")

    def action_clear_cache(self) -> None:
        """Clear the entire size cache and refresh."""
        cache_size = len(self.size_cache)
        self.size_cache.clear()
        self.update_display()
        self.notify(f"Cleared entire cache ({cache_size} entries) and refreshed")


def build_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser for the pydisk CLI."""
    parser = argparse.ArgumentParser(
        prog="pydisk",
        description="Display disk usage information or explore directory sizes interactively.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"pydisk {__version__}",
        help="Show version and exit",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Disk name or mount point to explore interactively (omit to show all disks)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns an exit status code (0 on success)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.path is None:
            # No path given - show all disks
            print_disks()
            return 0

        # Path given - enter interactive mode
        path = Path(args.path).expanduser().resolve()

        if not path.exists():
            print(f"pydisk: path does not exist: {path}", file=sys.stderr)
            return 1

        if not path.is_dir():
            print(f"pydisk: not a directory: {path}", file=sys.stderr)
            return 1

        app = DiskExplorerApp(path)
        app.run()

    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError) as e:
        print(f"pydisk: error: {e}", file=sys.stderr)
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
