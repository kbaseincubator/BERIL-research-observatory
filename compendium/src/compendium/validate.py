"""File-level validation helpers for synthesis-wiki artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import yaml

from .models import PagePlan, StatementCard


ValidatedRecord = StatementCard | PagePlan


@dataclass(frozen=True)
class ValidationResult:
    """Structured result for a validated artifact file."""

    artifact_type: str
    path: str
    count: int
    ids: list[str]
    records: list[ValidatedRecord]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "path": self.path,
            "count": self.count,
            "ids": list(self.ids),
        }


def validate_statement_card_file(path: str | Path) -> ValidationResult:
    """Load and validate a single ``StatementCard`` YAML/JSON file."""

    fp = Path(path)
    data = _load_data(fp)
    card = _build_statement_card(data, fp, "statement card")
    return ValidationResult(
        artifact_type="statement_card",
        path=str(fp),
        count=1,
        ids=[card.id],
        records=[card],
    )


def validate_page_plan_file(path: str | Path) -> ValidationResult:
    """Load and validate a single ``PagePlan`` YAML/JSON file."""

    fp = Path(path)
    data = _load_data(fp)
    if not isinstance(data, dict):
        raise ValueError(f"{fp}: page plan must be a mapping")
    try:
        plan = PagePlan.from_dict(data)
    except KeyError as exc:
        raise ValueError(f"{fp}: page plan missing required field {exc.args[0]!r}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{fp}: page plan invalid: {exc}") from exc
    return ValidationResult(
        artifact_type="page_plan",
        path=str(fp),
        count=1,
        ids=[plan.id],
        records=[plan],
    )


def validate_project_kg_file(path: str | Path) -> ValidationResult:
    """Load and validate project KG statement cards.

    Accepted shapes are either ``{"statements": [...]}`` or a bare list of
    statement-card mappings.
    """

    fp = Path(path)
    data = _load_data(fp)
    if isinstance(data, dict):
        if "statements" not in data:
            raise ValueError(f"{fp}: project KG mapping must contain a 'statements' list")
        statements = data["statements"]
    elif isinstance(data, list):
        statements = data
    else:
        raise ValueError(f"{fp}: project KG must be a mapping or list")

    if not isinstance(statements, list):
        raise ValueError(f"{fp}: project KG 'statements' must be a list")

    cards = [
        _build_statement_card(item, fp, f"statement card at index {index}")
        for index, item in enumerate(statements)
    ]
    return ValidationResult(
        artifact_type="project_kg",
        path=str(fp),
        count=len(cards),
        ids=[card.id for card in cards],
        records=cards,
    )


def _load_data(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"{path}: could not read file: {exc}") from exc

    if path.suffix not in {".json", ".yaml", ".yml"}:
        raise ValueError(f"{path}: expected a .json, .yaml, or .yml file")

    try:
        data = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except Exception as exc:
        raise ValueError(f"{path}: could not parse {path.suffix or 'file'}: {exc}") from exc

    if data is None:
        raise ValueError(f"{path}: file is empty")
    return data


def _build_statement_card(data: Any, path: Path, context: str) -> StatementCard:
    if not isinstance(data, dict):
        raise ValueError(f"{path}: {context} must be a mapping")
    try:
        return StatementCard.from_dict(data)
    except KeyError as exc:
        raise ValueError(f"{path}: {context} missing required field {exc.args[0]!r}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path}: {context} invalid: {exc}") from exc
