from datetime import datetime, timezone

from rich.console import Console

from observatory_context.progress import (
    NullObserver,
    RichIngestObserver,
    _format_last_activity,
    parse_last_llm_activity,
    parse_queue_counts,
    render_status,
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
    "+----------------+----------+-------+--------+------------+--------+--------------------------+\n"
    "|     Model      | Provider | Calls | Prompt | Completion | Total  |       Last Updated       |\n"
    "+----------------+----------+-------+--------+------------+--------+--------------------------+\n"
    "| gemini-3-flash |  openai  |  153  | 129611 |   198041   | 327652 | 2026-05-01T17:00:43.773Z |\n"
    "+----------------+----------+-------+--------+------------+--------+--------------------------+\n"
    "\n"
    "Embedding Models:\n"
    "+-------------------------------+----------+-------+\n"
    "|             Model             | Provider | Calls |\n"
    "+-------------------------------+----------+-------+\n"
    "| openai/text-embedding-3-large |  openai  |  230  |\n"
    "+-------------------------------+----------+-------+\n"
    "Last call timestamps: vlm=2026-05-01T17:00:50.000Z embedding=2026-05-01T17:00:47.872Z"
)

HEALTHY_STATUS = {
    "is_healthy": True,
    "errors": [],
    "components": {
        "queue": {
            "name": "queue",
            "is_healthy": True,
            "has_errors": False,
            "status": QUEUE_STATUS_TEXT,
        },
        "lock": {
            "name": "lock",
            "is_healthy": True,
            "has_errors": False,
            "status": "no locks",
        },
        "models": {
            "name": "models",
            "is_healthy": True,
            "has_errors": False,
            "status": MODELS_STATUS_TEXT,
        },
    },
}

UNHEALTHY_STATUS = {
    "is_healthy": False,
    "errors": ["embedding model unreachable"],
    "components": {
        "models": {
            "name": "models",
            "is_healthy": False,
            "has_errors": True,
            "status": "model gateway timeout",
        },
    },
}


def _render(group) -> str:
    console = Console(width=120, record=True)
    console.print(group)
    return console.export_text()


def test_render_status_healthy_includes_components_and_status_label() -> None:
    output = _render(render_status(HEALTHY_STATUS))
    assert "HEALTHY" in output
    assert "queue" in output
    assert "lock" in output
    assert "no locks" in output


def test_render_status_unhealthy_surfaces_errors_panel() -> None:
    output = _render(render_status(UNHEALTHY_STATUS))
    assert "UNHEALTHY" in output
    assert "embedding model unreachable" in output
    assert "model gateway timeout" in output


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
    assert counts["Semantic"]["pending"] == 1
    assert counts["Semantic-Nodes"]["processed"] == 5


def test_parse_queue_counts_returns_empty_when_status_missing() -> None:
    assert parse_queue_counts({}) == {}
    assert parse_queue_counts({"components": {"queue": {"status": 42}}}) == {}


def test_parse_last_llm_activity_returns_max_timestamp() -> None:
    ts = parse_last_llm_activity(HEALTHY_STATUS)
    assert ts == datetime(2026, 5, 1, 17, 0, 50, tzinfo=timezone.utc)


def test_parse_last_llm_activity_handles_no_models() -> None:
    assert parse_last_llm_activity({}) is None


def test_format_last_activity_falls_back_when_missing() -> None:
    assert _format_last_activity({}) == "last activity: —"


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


def test_null_observer_delegates_wait_to_client() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.calls = 0

        def wait_processed(self) -> None:
            self.calls += 1

    client = FakeClient()
    NullObserver().wait_processed(client)
    assert client.calls == 1
