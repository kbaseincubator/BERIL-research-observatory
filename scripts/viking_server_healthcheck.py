"""Check whether the configured OpenViking server is reachable and display status."""

from __future__ import annotations

import argparse
import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def _parse_ascii_table(raw: str) -> list[list[str]]:
    """Parse a prettytable-style ASCII table into rows of strings."""
    rows: list[list[str]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("+"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    return rows


def _render_table(title: str, raw: str, *, max_rows: int | None = None) -> Table:
    """Convert an ASCII table string into a Rich Table."""
    rows = _parse_ascii_table(raw)
    if not rows:
        table = Table(title=title)
        table.add_row("[dim]No data[/]")
        return table

    header, data = rows[0], rows[1:]
    table = Table(title=title, show_lines=False)
    for col in header:
        justify = "right" if col in {"Pending", "In Progress", "Processed", "Errors", "Total",
                                      "Index Count", "Vector Count", "Prompt", "Completion",
                                      "Locks", "Value"} else "left"
        table.add_column(col, justify=justify)

    if max_rows and len(data) > max_rows:
        for row in data[:max_rows]:
            table.add_row(*row)
        table.add_row(*[f"[dim]… +{len(data) - max_rows} more[/]"] + [""] * (len(header) - 1))
    else:
        for row in data:
            # Highlight TOTAL rows
            if row and row[0].upper() == "TOTAL":
                table.add_row(*[f"[bold]{c}[/]" for c in row], end_section=True)
            else:
                table.add_row(*row)

    return table


def _queue_progress(raw: str) -> Table:
    """Render queue status with progress-bar-style coloring."""
    rows = _parse_ascii_table(raw)
    if not rows:
        return _render_table("Processing Queues", raw)

    header, data = rows[0], rows[1:]
    table = Table(title="Processing Queues", show_lines=False)
    table.add_column("Queue")
    table.add_column("Pending", justify="right")
    table.add_column("In Progress", justify="right")
    table.add_column("Processed", justify="right")
    table.add_column("Errors", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Progress", justify="left", min_width=14)

    for row in data:
        if len(row) < 6:
            continue
        name, pending, in_progress, processed, errors, total = row[:6]
        try:
            n_processed = int(processed.strip())
            n_total = int(total.strip())
            n_pending = int(pending.strip())
            n_errors = int(errors.strip())
            pct = (n_processed / n_total * 100) if n_total > 0 else 0
        except ValueError:
            pct, n_pending, n_errors = 0, 0, 0

        if pct >= 100:
            pct_str = "[green]done[/]"
        else:
            pct_str = f"[cyan]{pct:5.1f}%[/]"

        pending_style = "yellow" if n_pending > 0 else "dim"
        error_style = "red bold" if n_errors > 0 else "dim"
        is_total = name.strip().upper() == "TOTAL"
        name_str = f"[bold]{name}[/]" if is_total else name

        table.add_row(
            name_str,
            f"[{pending_style}]{pending}[/]",
            in_progress,
            f"[green]{processed}[/]",
            f"[{error_style}]{errors}[/]",
            f"[bold]{total}[/]" if is_total else total,
            pct_str,
        )

    return table


def _health_banner(is_healthy: bool, errors: list[str]) -> Panel:
    """Render the top-level health banner."""
    if is_healthy:
        content = Text("HEALTHY", style="bold green")
        return Panel(content, title="OpenViking", border_style="green", expand=False)

    lines = Text()
    lines.append("UNHEALTHY", style="bold red")
    for err in errors:
        lines.append(f"\n  • {err}", style="red")
    return Panel(lines, title="OpenViking", border_style="red", expand=False)


def _component_badge(name: str, healthy: bool, has_errors: bool) -> str:
    """Return a styled badge for a component."""
    if has_errors:
        return f"[red]✗ {name}[/]"
    if healthy:
        return f"[green]✓ {name}[/]"
    return f"[yellow]? {name}[/]"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check whether the configured OpenViking server is reachable."
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Refresh status every few seconds until queues drain.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Refresh interval in seconds for --watch mode (default: 5).",
    )
    return parser


def _render_status(status: dict) -> None:
    """Render the full status display."""
    is_healthy = status.get("is_healthy", False)
    errors = status.get("errors", [])
    components = status.get("components", {})

    console.print()
    console.print(_health_banner(is_healthy, errors))
    console.print()

    # Component badges
    badges = "  ".join(
        _component_badge(name, comp.get("is_healthy", False), comp.get("has_errors", False))
        for name, comp in components.items()
    )
    console.print(f"  {badges}")
    console.print()

    # Queue (special rendering with progress)
    if "queue" in components:
        console.print(_queue_progress(components["queue"].get("status", "")))
        console.print()

    # VikingDB
    if "vikingdb" in components:
        console.print(_render_table("Vector Store", components["vikingdb"].get("status", "")))
        console.print()

    # VLM (language model usage)
    if "vlm" in components:
        console.print(_render_table("Language Model", components["vlm"].get("status", "")))
        console.print()

    # Retrieval
    if "retrieval" in components:
        console.print(_render_table("Retrieval", components["retrieval"].get("status", "")))
        console.print()

    # Lock — only show if there are errors, and cap rows
    if "lock" in components:
        lock = components["lock"]
        if lock.get("has_errors"):
            console.print(_render_table(
                "[red]Lock Issues[/]",
                lock.get("status", ""),
                max_rows=10,
            ))
            console.print()


def _queues_drained(status: dict) -> bool:
    """Return True if all queue pending counts are zero."""
    raw = status.get("components", {}).get("queue", {}).get("status", "")
    for match in re.finditer(r"\|\s*(\d+)\s*\|", raw):
        pass  # We need the parsed table
    rows = _parse_ascii_table(raw)
    if len(rows) < 2:
        return True
    for row in rows[1:]:
        if len(row) >= 3:
            try:
                pending = int(row[1].strip())
                in_progress = int(row[2].strip())
                if pending > 0 or in_progress > 0:
                    return False
            except ValueError:
                continue
    return True


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    from observatory_context import runtime

    try:
        client = runtime.build_client()
        if not client.health():
            console.print("[red]FAIL: OpenViking server is not reachable.[/]")
            return 1
    except Exception as exc:
        console.print(f"[red]FAIL: Could not connect to OpenViking: {exc}[/]")
        return 1

    if args.watch:
        import time

        from rich.live import Live

        try:
            with Live(console=console, refresh_per_second=1) as live:
                while True:
                    status = client.get_status()
                    # Capture rendered output
                    from io import StringIO
                    buf = StringIO()
                    temp_console = Console(file=buf, force_terminal=True, width=console.width)
                    _render_status_to(temp_console, status)
                    live.update(Text.from_ansi(buf.getvalue()))

                    if _queues_drained(status):
                        break
                    time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
        console.print("[green]Queues drained.[/]" if _queues_drained(client.get_status()) else "")
    else:
        status = client.get_status()
        _render_status(status)

    return 0


def _render_status_to(target_console: Console, status: dict) -> None:
    """Render status to a specific console (for live mode)."""
    is_healthy = status.get("is_healthy", False)
    errors = status.get("errors", [])
    components = status.get("components", {})

    target_console.print()
    target_console.print(_health_banner(is_healthy, errors))
    target_console.print()

    badges = "  ".join(
        _component_badge(name, comp.get("is_healthy", False), comp.get("has_errors", False))
        for name, comp in components.items()
    )
    target_console.print(f"  {badges}")
    target_console.print()

    if "queue" in components:
        target_console.print(_queue_progress(components["queue"].get("status", "")))
        target_console.print()

    if "vikingdb" in components:
        target_console.print(_render_table("Vector Store", components["vikingdb"].get("status", "")))
        target_console.print()

    if "lock" in components and components["lock"].get("has_errors"):
        target_console.print(_render_table(
            "[red]Lock Issues[/]",
            components["lock"].get("status", ""),
            max_rows=5,
        ))
        target_console.print()


if __name__ == "__main__":
    raise SystemExit(main())
