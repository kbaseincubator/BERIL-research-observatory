from __future__ import annotations

import threading
import time
from typing import Any, Protocol


QUEUE_POLL_INTERVAL_SECONDS = 1.0


class IngestObserver(Protocol):
    def start(self, total: int) -> None: ...
    def advance(self, label: str) -> None: ...
    def note(self, message: str) -> None: ...
    def wait_processed(self, client: Any) -> None: ...
    def done(self) -> None: ...


class NullObserver:
    def start(self, total: int) -> None:
        return None

    def advance(self, label: str) -> None:
        return None

    def note(self, message: str) -> None:
        return None

    def wait_processed(self, client: Any) -> None:
        client.wait_processed()

    def done(self) -> None:
        return None


class RichIngestObserver:
    def __init__(self, console: Any | None = None) -> None:
        from rich.console import Console
        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            Progress,
            SpinnerColumn,
            TextColumn,
            TimeElapsedColumn,
        )

        self.console = console or Console()
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}[/bold cyan]"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[dim]{task.fields[label]}[/dim]"),
            TimeElapsedColumn(),
            console=self.console,
        )
        self._task_id: int | None = None
        self._wait_task_id: int | None = None

    def __enter__(self) -> "RichIngestObserver":
        self._progress.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._progress.__exit__(exc_type, exc, tb)

    def start(self, total: int) -> None:
        if self._task_id is None:
            self._task_id = self._progress.add_task(
                "Ingesting", total=max(total, 1), label=""
            )
            return
        existing = self._progress.tasks[self._task_id].total or 0
        self._progress.update(self._task_id, total=existing + max(total, 0))

    def advance(self, label: str) -> None:
        if self._task_id is not None:
            self._progress.update(self._task_id, advance=1, label=label)

    def note(self, message: str) -> None:
        self._progress.console.log(message)

    def wait_processed(self, client: Any) -> None:
        wait_id = self._progress.add_task(
            "Waiting on OpenViking queue", total=None, label="pending=? in_progress=?"
        )
        self._wait_task_id = wait_id

        result_holder: dict[str, Any] = {}

        def _wait() -> None:
            try:
                client.wait_processed()
                result_holder["done"] = True
            except Exception as exc:
                result_holder["error"] = exc

        thread = threading.Thread(target=_wait, daemon=True)
        thread.start()

        while thread.is_alive():
            label = _summarise_queue(_safe_status(client))
            self._progress.update(wait_id, label=label)
            time.sleep(QUEUE_POLL_INTERVAL_SECONDS)

        thread.join()
        self._progress.update(wait_id, label="done", completed=1, total=1)
        self._progress.remove_task(wait_id)
        self._wait_task_id = None
        if "error" in result_holder:
            raise result_holder["error"]

    def done(self) -> None:
        if self._task_id is not None:
            self._progress.update(self._task_id, completed=self._progress.tasks[self._task_id].total)


def _safe_status(client: Any) -> dict[str, Any]:
    try:
        return client.get_status()
    except Exception:
        return {}


def _summarise_queue(status: dict[str, Any]) -> str:
    queue = status.get("components", {}).get("queue", {}) if status else {}
    counts = queue.get("counts") if isinstance(queue, dict) else None
    if isinstance(counts, dict):
        pending = counts.get("pending", "?")
        in_progress = counts.get("in_progress", "?")
        errors = counts.get("errors", 0)
        return f"pending={pending} in_progress={in_progress} errors={errors}"
    raw = queue.get("status") if isinstance(queue, dict) else None
    if isinstance(raw, str):
        for line in raw.splitlines():
            if "TOTAL" in line:
                parts = [p.strip() for p in line.strip("|").split("|")]
                if len(parts) >= 6:
                    return f"pending={parts[1]} in_progress={parts[2]} errors={parts[5]}"
    return "polling..."


def render_status(status: dict[str, Any]) -> Any:
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    sections: list[Any] = []

    healthy = bool(status.get("is_healthy"))
    errors = status.get("errors") or []
    header_style = "bold green" if healthy and not errors else "bold red"
    header = Text(
        "HEALTHY" if healthy and not errors else "UNHEALTHY",
        style=header_style,
    )
    sections.append(Panel(header, title="OpenViking", border_style=header_style))

    if errors:
        err_table = Table(show_header=False, box=None, expand=True)
        for err in errors:
            err_table.add_row(Text(str(err), style="red"))
        sections.append(Panel(err_table, title="Errors", border_style="red"))

    components = status.get("components") or {}
    for name, payload in components.items():
        title = (payload.get("name") or name) if isinstance(payload, dict) else name
        is_healthy = bool(payload.get("is_healthy")) if isinstance(payload, dict) else False
        has_errors = bool(payload.get("has_errors")) if isinstance(payload, dict) else False
        border = "green" if is_healthy and not has_errors else "red"
        body = payload.get("status") if isinstance(payload, dict) else None
        body_renderable: Any
        if isinstance(body, str):
            body_renderable = Text(body.rstrip(), no_wrap=True, overflow="crop")
        else:
            body_renderable = Text(str(payload), no_wrap=True, overflow="crop")
        sections.append(Panel(body_renderable, title=title, border_style=border, expand=True))

    return Group(*sections)
