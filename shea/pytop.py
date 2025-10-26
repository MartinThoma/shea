"""
Interactive TUI process viewer for pytop.

Provides a process viewer similar to `top` and `htop`, showing running processes by CPU usage.

Usage examples:
    pytop
"""

from __future__ import annotations

import operator
import sys
import time
from contextlib import suppress
from typing import ClassVar

try:
    import psutil
except ImportError:
    print(
        "Error: psutil is required for pytop. Install it with: pip install psutil",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal
    from textual.widgets import DataTable, Footer, Header, Static
except ImportError:
    print(
        "Error: textual is required for pytop. Install it with: pip install textual",
        file=sys.stderr,
    )
    sys.exit(1)

from . import __version__

BYTES_UNIT = 1024.0
SEC_MIN = 60
SEC_HOUR = 3600
THRESH_RED = 90
THRESH_YELLOW = 70
THRESH_CYAN = 50


def _format_bytes(bytes_val: int) -> str:
    """Format bytes into human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < BYTES_UNIT:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= BYTES_UNIT
    return f"{bytes_val:.1f}PB"


def _format_time(seconds: float) -> str:
    """Format seconds into human-readable time."""
    if seconds < SEC_MIN:
        return f"{int(seconds)}s"
    if seconds < SEC_HOUR:
        mins = int(seconds / SEC_MIN)
        secs = int(seconds % SEC_MIN)
        return f"{mins}m{secs}s"
    hours = int(seconds / SEC_HOUR)
    mins = int((seconds % SEC_HOUR) / SEC_MIN)
    return f"{hours}h{mins}m"


def _create_bar(
    percent: float,
    width: int = 30,
    *,
    filled_char: str = "█",
    empty_char: str = "░",
) -> str:
    """Create a visual progress bar."""
    filled = int(percent / 100 * width)
    empty = width - filled
    return f"{filled_char * filled}{empty_char * empty}"


def _get_bar_color(percent: float) -> str:
    """Get color based on usage percentage."""
    if percent >= THRESH_RED:
        return "red"
    if percent >= THRESH_YELLOW:
        return "yellow"
    if percent >= THRESH_CYAN:
        return "cyan"
    return "green"


class CPUWidget(Static):
    """Widget to display CPU usage per core."""

    def on_mount(self) -> None:
        """Set up the widget when mounted."""
        self.update_cpu()  # Initial update
        self.set_interval(1, self.update_cpu)

    def update_cpu(self) -> None:
        """Update CPU information."""
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_count = len(cpu_percent)

        lines = ["🔥 [bold cyan]CPU Usage[/bold cyan]\n"]

        for i, percent in enumerate(cpu_percent):
            bar = _create_bar(percent, width=20)
            color = _get_bar_color(percent)
            lines.append(f"Core {i:2d}: [{color}]{bar}[/{color}] {percent:5.1f}%")

        avg_cpu = sum(cpu_percent) / cpu_count
        bar = _create_bar(avg_cpu, width=20)
        color = _get_bar_color(avg_cpu)
        lines.append(f"\n[bold]Average: [{color}]{bar}[/{color}] {avg_cpu:5.1f}%[/bold]")

        self.update("\n".join(lines))


class MemoryWidget(Static):
    """Widget to display memory usage."""

    def on_mount(self) -> None:
        """Set up the widget when mounted."""
        self.update_memory()  # Initial update
        self.set_interval(1, self.update_memory)

    def update_memory(self) -> None:
        """Update memory information."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        mem_bar = _create_bar(mem.percent, width=40)
        mem_color = _get_bar_color(mem.percent)

        swap_bar = _create_bar(swap.percent, width=40)
        swap_color = _get_bar_color(swap.percent)

        lines = [
            "💾 [bold cyan]Memory Usage[/bold cyan]\n",
            f"RAM:  [{mem_color}]{mem_bar}[/{mem_color}]",
            f"      {mem.percent:5.1f}% ({_format_bytes(mem.used)} / {_format_bytes(mem.total)})\n",
            f"Swap: [{swap_color}]{swap_bar}[/{swap_color}]",
            (
                f"      {swap.percent:5.1f}% ("
                f"{_format_bytes(swap.used)} / {_format_bytes(swap.total)})"
            ),
        ]

        self.update("\n".join(lines))


class SystemInfoWidget(Static):
    """Widget to display system information."""

    def on_mount(self) -> None:
        """Set up the widget when mounted."""
        self.update_info()  # Initial update
        self.set_interval(2, self.update_info)

    def update_info(self) -> None:
        """Update system information."""
        uptime_seconds = time.time() - psutil.boot_time()
        process_count = len(psutil.pids())

        lines = [
            "⚙️ [bold cyan]System Info[/bold cyan]\n",
            f"⏱️  Uptime:    {_format_time(uptime_seconds)}",
            f"📊 Processes: {process_count}",
        ]

        self.update("\n".join(lines))


class ProcessTable(DataTable):
    """Widget to display process list."""

    # Track sorting state
    sort_column = "CPU%"
    sort_reverse = True
    # Track sort order for toggle columns (PID, USER, COMMAND)
    toggle_sort_order: ClassVar[dict[str, bool]] = {}

    def on_mount(self) -> None:
        """Set up the table when mounted."""
        self.cursor_type = "row"
        # Define columns with explicit keys so header-click sorting works reliably
        self.add_column("PID", key="PID")
        self.add_column("USER", key="USER")
        self.add_column("CPU%", key="CPU%")
        self.add_column("MEMORY", key="MEMORY")
        self.add_column("TIME", key="TIME")
        self.add_column("COMMAND", key="COMMAND")
        self.set_interval(2, self.update_processes)

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header clicks for sorting."""
        column_key = event.column_key
        column_label = str(column_key.value)

        # Determine sort order
        if column_label in {"CPU%", "MEMORY", "TIME"}:
            # These always sort descending (highest first)
            self.sort_column = column_label
            self.sort_reverse = True
        else:
            # PID, USER, COMMAND toggle sort order
            if self.sort_column == column_label:
                # Toggle if clicking same column
                self.toggle_sort_order[column_label] = not self.toggle_sort_order.get(
                    column_label,
                    False,
                )
            else:
                # Default to ascending for new column
                self.toggle_sort_order[column_label] = False

            self.sort_column = column_label
            self.sort_reverse = self.toggle_sort_order[column_label]

        # Immediately update to show new sort
        self.update_processes()

    def _snapshot_processes(self) -> list[psutil.Process]:
        """Return a snapshot list of running processes."""
        return list(psutil.process_iter(["pid"]))

    @staticmethod
    def _prime_cpu(procs: list[psutil.Process]) -> None:
        """Prime CPU counters for each process so next read gives a delta."""
        for p in procs:
            with suppress(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                p.cpu_percent(None)

    @staticmethod
    def _gather_info(procs: list[psutil.Process], now: float) -> list[dict]:
        """Gather display info for processes."""
        items: list[dict] = []
        for p in procs:
            with suppress(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                with p.oneshot():
                    pid = p.pid
                    name = p.name()
                    username = p.username()
                    cpu = p.cpu_percent(None) or 0.0
                    mem_percent = p.memory_percent() or 0.0
                    mem_info = p.memory_info()
                    mem_bytes = mem_info.rss if mem_info else 0
                    create_time = p.create_time()
                    cmdline_list = p.cmdline()

                cmdline = " ".join(cmdline_list) if cmdline_list else name
                max_chars = 60
                if len(cmdline) > max_chars:
                    cmdline = cmdline[: max_chars - 3] + "..."

                runtime_seconds = now - create_time
                runtime = _format_time(runtime_seconds)
                username_short = username.split("\\")[-1][:12]

                items.append(
                    {
                        "pid": pid,
                        "username": username_short,
                        "cpu": cpu,
                        "mem_percent": mem_percent,
                        "mem_bytes": mem_bytes,
                        "runtime": runtime,
                        "runtime_seconds": runtime_seconds,
                        "cmdline": cmdline,
                    },
                )
        return items

    def _sort_processes(self, processes: list[dict]) -> None:
        """Sort processes in-place based on current sort column/direction."""
        key_funcs: dict[str, callable] = {
            "PID": operator.itemgetter("pid"),
            "USER": lambda p: p["username"].lower(),
            "CPU%": operator.itemgetter("cpu"),
            "MEMORY": operator.itemgetter("mem_bytes"),
            "TIME": operator.itemgetter("runtime_seconds"),
            "COMMAND": lambda p: p["cmdline"].lower(),
        }
        key_func = key_funcs.get(self.sort_column, operator.itemgetter("cpu"))
        processes.sort(key=key_func, reverse=self.sort_reverse)

    def update_processes(self) -> None:
        """Update the process list."""
        self.clear()

        now = time.time()
        procs = self._snapshot_processes()
        self._prime_cpu(procs)
        time.sleep(0.1)
        processes = self._gather_info(procs, now)
        self._sort_processes(processes)

        # Add top 50 processes
        for proc in processes[:50]:
            mem_display = f"{proc['mem_percent']:.1f}% / {_format_bytes(proc['mem_bytes'])}"
            self.add_row(
                str(proc["pid"]),
                proc["username"],
                f"{proc['cpu']:.1f}%",
                mem_display,
                proc["runtime"],
                proc["cmdline"],
            )


class PyTopApp(App):
    """A Textual app for process monitoring."""

    CSS = """
    Screen {
        background: $background;
    }

    #top-section {
        height: auto;
        margin: 1;
    }

    #stats-container {
        height: auto;
        layout: horizontal;
    }

    CPUWidget {
        width: 1fr;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-right: 1;
    }

    MemoryWidget {
        width: 1fr;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-right: 1;
    }

    SystemInfoWidget {
        width: 30;
        height: auto;
        border: solid $primary;
        padding: 1;
    }

    ProcessTable {
        height: 1fr;
        margin: 1;
        border: solid $primary;
    }
    """

    BINDINGS = [  # noqa: RUF012
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)

        with Container(id="top-section"), Horizontal(id="stats-container"):
            yield CPUWidget()
            yield MemoryWidget()
            yield SystemInfoWidget()

        yield ProcessTable()
        yield Footer()

    def action_refresh(self) -> None:
        """Refresh all widgets."""
        for widget in self.query(CPUWidget):
            widget.update_cpu()
        for widget in self.query(MemoryWidget):
            widget.update_memory()
        for widget in self.query(SystemInfoWidget):
            widget.update_info()
        for widget in self.query(ProcessTable):
            widget.update_processes()


def main() -> None:
    """Start pytop."""
    app = PyTopApp()
    app.title = f"pytop v{__version__}"
    app.sub_title = "Process Monitor"
    app.run()


if __name__ == "__main__":
    main()
