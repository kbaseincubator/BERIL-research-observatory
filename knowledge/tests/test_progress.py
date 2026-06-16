from datetime import datetime, timezone

from rich.console import Console

from observatory_context.progress import (
    RichIngestObserver,
    parse_last_llm_activity,
    parse_queue_counts,
    render_status,
    wait_for_queue_idle,
)


QUEUE_STATUS_TEXT = (
    "+----------------+---------+-------------+-----------+----------+--------+-------+\n"
    "|     Queue      | Pending | In Progress | Processed | Requeued | Errors | Total |\n"
    "+----------------+---------+-------------+-----------+----------+--------+-------+\n"
    "|   Embedding    |    0    |      2      |    187    |    0     |   1    |  189  |\n"
    "|    Semantic    |    1    |      2      |     4     |    0     |   0    |   7   |\n"
    "| Semantic-Nodes |    2    |      1      |     5     |    0     |   0    |   8   |\n"
    "|     TOTAL      |    3    |      5      |    196    |    0     |   1    |  204  |\n"
    "+----------------+---------+-------------+-----------+----------+--------+-------+"
)

MODELS_STATUS_TEXT = (
    "VLM Models:\n"
    "| gemini-3-flash | openai | 153 | 129611 | 198041 | 327652 | 2026-05-01T17:00:43.773Z |\n"
    "Embedding Models:\n"
    "| openai/text-embedding-3-large | openai | 230 | 481 | 0 | 481 | 2026-05-01T17:00:50.000Z |"
)

HEALTHY_STATUS = {
    "is_healthy": True,
    "errors": [],
    "components": {
        "queue": {"name": "queue", "is_healthy": True, "has_errors": False, "status": QUEUE_STATUS_TEXT},
        "models": {"name": "models", "is_healthy": True, "has_errors": False, "status": MODELS_STATUS_TEXT},
    },
}

UNHEALTHY_STATUS = {
    "is_healthy": False,
    "errors": ["embedding model unreachable"],
    "components": {
        "models": {"name": "models", "is_healthy": False, "has_errors": True, "status": "model gateway timeout"},
    },
}


def _render(group) -> str:
    console = Console(width=120, record=True)
    console.print(group)
    return console.export_text()


def test_render_status_distinguishes_healthy_and_unhealthy() -> None:
    healthy = _render(render_status(HEALTHY_STATUS))
    assert "HEALTHY" in healthy
    assert "queue" in healthy

    unhealthy = _render(render_status(UNHEALTHY_STATUS))
    assert "UNHEALTHY" in unhealthy
    assert "embedding model unreachable" in unhealthy
    assert "model gateway timeout" in unhealthy


def test_parse_queue_counts_returns_per_queue_dict_without_total() -> None:
    counts = parse_queue_counts(HEALTHY_STATUS)
    assert set(counts) == {"Embedding", "Semantic", "Semantic-Nodes"}
    assert counts["Embedding"] == {
        "pending": 0,
        "in_progress": 2,
        "processed": 187,
        "requeued": 0,
        "errors": 1,
        "total": 189,
    }


def test_parse_last_llm_activity_returns_max_timestamp() -> None:
    assert parse_last_llm_activity(HEALTHY_STATUS) == datetime(
        2026, 5, 1, 17, 0, 50, tzinfo=timezone.utc
    )


def test_rich_observer_start_is_additive_across_repeated_calls() -> None:
    observer = RichIngestObserver(console=Console(record=True, file=open("/dev/null", "w")))
    with observer:
        observer.start(2)
        observer.advance("a")
        observer.advance("b")
        observer.start(3)
        observer.advance("c")
        observer.advance("d")
        observer.advance("e")
        task = observer._progress.tasks[observer._task_id]
        assert task.total == 5
        assert task.completed == 5


def _queue_status(pending: int, in_progress: int, processed: int) -> dict:
    body = (
        "+-----+---------+-------------+-----------+----------+--------+-------+\n"
        "|Queue| Pending | In Progress | Processed | Requeued | Errors | Total |\n"
        "+-----+---------+-------------+-----------+----------+--------+-------+\n"
        f"| Embedding | {pending} | {in_progress} | {processed} | 0 | 0 | {pending + in_progress + processed} |\n"
        f"| Semantic | 0 | 0 | {processed} | 0 | 0 | {processed} |\n"
        f"| Semantic-Nodes | 0 | 0 | {processed} | 0 | 0 | {processed} |"
    )
    return {"components": {"queue": {"status": body}}}


class _ScriptedClient:
    def __init__(self, scripted: list[dict]) -> None:
        self._scripted = list(scripted)

    def get_status(self) -> dict:
        return self._scripted.pop(0) if self._scripted else _queue_status(0, 0, 5)


def test_wait_for_queue_idle_finishes_when_queue_drains_after_activity() -> None:
    client = _ScriptedClient(
        [
            _queue_status(2, 1, 0),
            _queue_status(0, 1, 2),
            _queue_status(0, 0, 3),
            _queue_status(0, 0, 3),
            _queue_status(0, 0, 3),
        ]
    )
    wait_for_queue_idle(client, poll_interval=0.0, idle_ticks=3)


def test_wait_for_queue_idle_exits_when_no_work_ever_observed() -> None:
    client = _ScriptedClient([_queue_status(0, 0, 0) for _ in range(20)])
    wait_for_queue_idle(client, poll_interval=0.0, max_empty_ticks=3)
