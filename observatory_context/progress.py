from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any, Protocol


QUEUE_POLL_INTERVAL_SECONDS = 1.0
IDLE_TICKS_TO_FINISH = 3
EMPTY_TICKS_TO_DECIDE_NO_WORK = 10
WAIT_MAX_SECONDS = 60 * 60  # safety net: 1 hour
TRACKED_QUEUES: tuple[str, ...] = ("Embedding", "Semantic", "Semantic-Nodes")
_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?")


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
        # Poll get_status() instead of calling client.wait_processed(): the SDK's
        # wait endpoint is one big blocking POST that gets killed by httpx's read
        # timeout long before slow LLM workloads finish. Polling is robust and
        # also drives the per-queue progress bars below.
        wait_id = self._progress.add_task(
            "Waiting on OpenViking queue", total=None, label="last activity: ?"
        )
        queue_ids: dict[str, int] = {
            name: self._progress.add_task(name, total=0, completed=0, label="—")
            for name in TRACKED_QUEUES
        }
        try:
            wait_for_queue_idle(
                client,
                on_tick=lambda status: self._update_queue_tasks(wait_id, queue_ids, status),
            )
        finally:
            self._progress.remove_task(wait_id)
            for tid in queue_ids.values():
                self._progress.remove_task(tid)

    def _update_queue_tasks(
        self,
        wait_id: int,
        queue_ids: dict[str, int],
        status: dict[str, Any],
    ) -> None:
        counts = parse_queue_counts(status)
        for name, task_id in queue_ids.items():
            row = counts.get(name) or {}
            processed = int(row.get("processed", 0))
            in_progress = int(row.get("in_progress", 0))
            pending = int(row.get("pending", 0))
            errors = int(row.get("errors", 0))
            total = processed + in_progress + pending
            label = f"pending={pending} in_progress={in_progress} errors={errors}"
            self._progress.update(
                task_id,
                completed=processed,
                total=max(total, processed) or 1,
                label=label,
            )
        self._progress.update(wait_id, label=_format_last_activity(status))

    def done(self) -> None:
        if self._task_id is not None:
            self._progress.update(
                self._task_id,
                completed=self._progress.tasks[self._task_id].total,
            )


def _safe_status(client: Any) -> dict[str, Any]:
    try:
        return client.get_status()
    except Exception:
        return {}


def wait_for_queue_idle(
    client: Any,
    *,
    on_tick: Any = None,
    poll_interval: float = QUEUE_POLL_INTERVAL_SECONDS,
    idle_ticks: int = IDLE_TICKS_TO_FINISH,
    max_empty_ticks: int = EMPTY_TICKS_TO_DECIDE_NO_WORK,
    max_seconds: float = WAIT_MAX_SECONDS,
) -> None:
    """Poll client.get_status() until all tracked queues report idle.

    A queue is idle when ``pending == 0`` and ``in_progress == 0`` for
    ``idle_ticks`` consecutive observations after we have seen any activity.
    If we never observe activity, exit after ``max_empty_ticks`` consecutive
    empty observations (the queue had no work to do). ``on_tick`` is called
    once per poll with the raw status dict, e.g. to update progress bars.
    Raises ``TimeoutError`` if ``max_seconds`` elapses before the queue idles.
    """
    seen_activity = False
    idle_streak = 0
    empty_streak = 0
    deadline = time.monotonic() + max_seconds
    while True:
        status = _safe_status(client)
        if on_tick is not None:
            try:
                on_tick(status)
            except Exception:
                pass
        counts = parse_queue_counts(status)
        if counts:
            active = sum(
                int(c.get("pending", 0)) + int(c.get("in_progress", 0))
                for c in counts.values()
            )
            if active > 0:
                seen_activity = True
                idle_streak = 0
                empty_streak = 0
            elif seen_activity:
                idle_streak += 1
            else:
                empty_streak += 1
        else:
            idle_streak = 0
        if seen_activity and idle_streak >= idle_ticks:
            return
        if empty_streak >= max_empty_ticks:
            return
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"OpenViking queue did not idle within {max_seconds:.0f}s"
            )
        time.sleep(poll_interval)


def parse_queue_counts(status: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Parse the queue ASCII table from get_status() into per-queue counts.

    Returns a dict like:
        {"Embedding": {"pending": 0, "in_progress": 2, "processed": 187,
                       "requeued": 0, "errors": 0, "total": 189}, ...}
    The synthetic "TOTAL" row is omitted.
    """
    queue_component = (status or {}).get("components", {}).get("queue", {})
    raw = queue_component.get("status") if isinstance(queue_component, dict) else None
    if not isinstance(raw, str):
        return {}
    rows = _parse_pretty_table(raw)
    out: dict[str, dict[str, int]] = {}
    for row in rows:
        name = row.get("Queue", "").strip()
        if not name or name == "TOTAL":
            continue
        out[name] = {
            "pending": _to_int(row.get("Pending")),
            "in_progress": _to_int(row.get("In Progress")),
            "processed": _to_int(row.get("Processed")),
            "requeued": _to_int(row.get("Requeued")),
            "errors": _to_int(row.get("Errors")),
            "total": _to_int(row.get("Total")),
        }
    return out


def parse_last_llm_activity(status: dict[str, Any]) -> datetime | None:
    """Find the latest 'Last Updated' timestamp across the model usage tables."""
    models_component = (status or {}).get("components", {}).get("models", {})
    raw = models_component.get("status") if isinstance(models_component, dict) else None
    if not isinstance(raw, str):
        return None
    latest: datetime | None = None
    for match in _TIMESTAMP_RE.finditer(raw):
        ts = _parse_iso(match.group(0))
        if ts is None:
            continue
        if latest is None or ts > latest:
            latest = ts
    return latest


def _format_last_activity(status: dict[str, Any]) -> str:
    ts = parse_last_llm_activity(status)
    if ts is None:
        return "last activity: —"
    delta = datetime.now(timezone.utc) - ts
    seconds = max(int(delta.total_seconds()), 0)
    return f"last LLM call: {seconds}s ago"


def _parse_pretty_table(text: str) -> list[dict[str, str]]:
    """Parse a tabulate "pretty" table into a list of {header: value} dicts."""
    headers: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("+"):
            continue
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if headers is None:
            headers = cells
            continue
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows


def _to_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def _parse_iso(text: str) -> datetime | None:
    candidate = text.replace("Z", "+00:00")
    try:
        ts = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


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
