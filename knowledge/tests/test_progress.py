from rich.console import Console

from observatory_context.progress import (
    NullObserver,
    RichIngestObserver,
    _summarise_queue,
    render_status,
)


HEALTHY_STATUS = {
    "is_healthy": True,
    "errors": [],
    "components": {
        "queue": {
            "name": "queue",
            "is_healthy": True,
            "has_errors": False,
            "status": (
                "+----+---------+-------------+-----------+----------+--------+-------+\n"
                "|Name| Pending | In Progress | Processed | Requeued | Errors | Total |\n"
                "+----+---------+-------------+-----------+----------+--------+-------+\n"
                "|TOTAL|    0    |      2      |    50     |    0     |   0    |  52  |"
            ),
        },
        "lock": {
            "name": "lock",
            "is_healthy": True,
            "has_errors": False,
            "status": "no locks",
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


def test_summarise_queue_parses_total_line() -> None:
    label = _summarise_queue(HEALTHY_STATUS)
    assert "pending=0" in label
    assert "in_progress=2" in label
    assert "errors=0" in label


def test_summarise_queue_handles_missing_queue() -> None:
    assert _summarise_queue({}) == "polling..."


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
