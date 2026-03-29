"""CBORG-based entity extraction and tier generation for observatory ingest."""

from __future__ import annotations

import json
import logging
from typing import Literal

import httpx
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

_ENTITY_TYPES = Literal["organism", "gene", "pathway", "method", "concept"]
_CONFIDENCE = Literal["high", "moderate", "low"]


class Entity(BaseModel):
    """A named entity extracted from a report."""

    type: _ENTITY_TYPES
    id: str
    name: str
    metadata: dict = Field(default_factory=dict)


class Relation(BaseModel):
    """A directed relationship between two entities."""

    subject: str
    predicate: str
    object: str
    evidence: str
    confidence: _CONFIDENCE


class HypothesisUpdate(BaseModel):
    """An update to a tracked hypothesis."""

    id: str
    status: str
    claim: str
    evidence_delta: str


class TimelineEvent(BaseModel):
    """A dated event in the research timeline."""

    date: str
    event: str
    type: str
    project: str | None = None


class EntityExtraction(BaseModel):
    """Container for all extracted knowledge from a single report."""

    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    hypotheses: list[HypothesisUpdate] = Field(default_factory=list)
    timeline_events: list[TimelineEvent] = Field(default_factory=list)


_EXTRACTION_SYSTEM = """\
You are a scientific knowledge extraction assistant. Given a research report \
and provenance metadata, extract structured knowledge in JSON format matching \
the schema below. Return ONLY valid JSON with no markdown fences or commentary.

Schema:
{
  "entities": [
    {"type": "<organism|gene|pathway|method|concept>", "id": "<slug>", "name": "<display name>", "metadata": {}}
  ],
  "relations": [
    {"subject": "<entity id>", "predicate": "<verb phrase>", "object": "<entity id>",
     "evidence": "<brief citation or description>", "confidence": "<high|moderate|low>"}
  ],
  "hypotheses": [
    {"id": "<hypothesis id>", "status": "<open|supported|refuted|updated>",
     "claim": "<hypothesis statement>", "evidence_delta": "<what this report adds>"}
  ],
  "timeline_events": [
    {"date": "<YYYY-MM-DD>", "event": "<description>", "type": "<milestone|experiment|publication|meeting>",
     "project": "<project name or null>"}
  ]
}
"""


class CBORGExtractor:
    """Extract entities and generate text tiers via the CBORG API.

    Parameters
    ----------
    api_url:
        Base URL for the CBORG API (e.g. ``https://api.cborg.lbl.gov/v1``).
    model:
        Model identifier to use for all completions.
    api_key:
        Bearer token for the CBORG API.
    max_input_tokens:
        Maximum input tokens the model supports. Reports exceeding this
        (estimated at ~4 chars/token) are skipped.
    max_output_tokens:
        Maximum output tokens the model supports. Used as the default
        ``max_tokens`` for extraction calls.
    """

    def __init__(
        self,
        api_url: str,
        model: str,
        api_key: str,
        max_input_tokens: int | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        self.model = model
        self._api_url = api_url.rstrip("/")
        self._max_input_tokens = max_input_tokens
        self._max_output_tokens = max_output_tokens or 16384
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120.0,
        )

    def extract_knowledge(self, report: str, provenance: dict) -> EntityExtraction:
        """Extract entities, relations, hypotheses, and timeline events from *report*.

        Parameters
        ----------
        report:
            Raw text of the project report.
        provenance:
            Metadata about the report origin (project name, date, etc.).

        Returns
        -------
        EntityExtraction
            Parsed extraction result; empty on parse failure.

        Raises
        ------
        ValueError
            If the prompt exceeds the model's max input token estimate.
        """
        prompt = self._build_extraction_prompt(report, provenance)
        total_chars = len(_EXTRACTION_SYSTEM) + len(prompt)
        estimated_tokens = total_chars // 4  # conservative ~4 chars/token
        if self._max_input_tokens and estimated_tokens > self._max_input_tokens:
            raise ValueError(
                f"Prompt too large (~{estimated_tokens} tokens) for model limit "
                f"({self._max_input_tokens} tokens)"
            )
        raw = self._chat(
            system=_EXTRACTION_SYSTEM,
            user=prompt,
            max_tokens=self._max_output_tokens,
        )
        try:
            data = json.loads(raw)
            return EntityExtraction.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Failed to parse extraction response: %s", exc)
            return EntityExtraction()

    def generate_abstract(self, content: str, max_tokens: int = 80) -> str:
        """Generate a concise L0 abstract (one or two sentences).

        Parameters
        ----------
        content:
            Full report or document text.
        max_tokens:
            Maximum tokens for the response.

        Returns
        -------
        str
            Short abstract suitable for L0 storage.
        """
        system = (
            "You are a scientific writing assistant. "
            "Summarise the provided research content in one or two sentences, "
            "capturing the core finding or objective."
        )
        return self._chat(system=system, user=content, max_tokens=max_tokens)

    def generate_overview(self, content: str, max_tokens: int = 300) -> str:
        """Generate a structured L1 overview paragraph.

        Parameters
        ----------
        content:
            Full report or document text.
        max_tokens:
            Maximum tokens for the response.

        Returns
        -------
        str
            Medium-length overview suitable for L1 storage.
        """
        system = (
            "You are a scientific writing assistant. "
            "Write a concise overview (3-5 sentences) of the provided research content, "
            "covering background, methods, key results, and significance."
        )
        return self._chat(system=system, user=content, max_tokens=max_tokens)

    def _build_extraction_prompt(self, report: str, provenance: dict) -> str:
        """Format the user-turn extraction prompt.

        Parameters
        ----------
        report:
            Raw report text.
        provenance:
            Metadata dict to include as context.

        Returns
        -------
        str
            Formatted prompt string.
        """
        provenance_lines = "\n".join(f"  {k}: {v}" for k, v in provenance.items())
        return (
            f"Provenance:\n{provenance_lines}\n\n"
            f"Extract entities, relations, hypotheses, and timeline_events "
            f"from the following report.\n\n"
            f"Report:\n{report}"
        )

    def _chat(self, system: str, user: str, max_tokens: int) -> str:
        """Call the /chat/completions endpoint and return the response text.

        Parameters
        ----------
        system:
            System message content.
        user:
            User message content.
        max_tokens:
            Maximum tokens for the completion.

        Returns
        -------
        str
            Stripped response text from the model.
        """
        import time

        for attempt in range(5):
            response = self._client.post(
                f"{self._api_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.0,
                },
            )
            if response.status_code == 429:
                wait = float(response.headers.get("retry-after", 2 ** attempt))
                logger.info("Rate limited, retrying in %.1fs (attempt %d/5)", wait, attempt + 1)
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

        response.raise_for_status()  # raise on final failure
        return ""  # unreachable
