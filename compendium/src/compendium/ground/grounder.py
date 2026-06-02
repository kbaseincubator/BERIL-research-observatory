"""Deterministic grounder.

Assigns CURIEs to entities with no network or LLM calls:
  - Organisms are canonicalized via the seed dictionary (``dictionary.yaml``).
  - Gene/ortholog/identifier labels (K#####, COG###, PF#####, PMID:#, DOI) are matched by regex.
"""

from __future__ import annotations

import functools
import pathlib
import re

import yaml

from compendium import ids
from compendium.models import ProjectKG

_DEFAULT_DICT = pathlib.Path(__file__).with_name("dictionary.yaml")

_KEGG = re.compile(r"^K\d{5}$")
_COG = re.compile(r"^COG\d{3,4}$")
_PFAM = re.compile(r"^PF\d{5}$")
_PMID = re.compile(r"^PMID:\d+$")
_DOI = re.compile(r"^10\.\d+/")


def regex_curie(label: str) -> str | None:
    """Map an identifier-like label to a CURIE via deterministic regex, else ``None``."""
    if _KEGG.match(label):
        return "KEGG:" + label
    if _COG.match(label):
        return "COG:" + label
    if _PFAM.match(label):
        return "Pfam:" + label
    if _PMID.match(label):
        return label
    if _DOI.match(label):
        return "DOI:" + label
    return None


@functools.lru_cache(maxsize=None)
def _load_cached(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_dictionary(path: pathlib.Path | None = None) -> dict:
    """Load the grounding dictionary (defaults to the bundled ``dictionary.yaml``)."""
    return _load_cached(path or _DEFAULT_DICT)


def ground(pkg: ProjectKG, dictionary_path: pathlib.Path | None = None) -> ProjectKG:
    """Ground each entity in ``pkg`` in place and return the mutated package.

    Organisms are looked up by normalized label in the dictionary's ``organisms`` table; on a hit
    the entity's ``curie`` and canonical ``label`` are set. All other entities get a regex CURIE if
    one is not already assigned. Node ids are never changed.
    """
    dictionary = load_dictionary(dictionary_path)
    organisms = dictionary.get("organisms", {})
    for entity in pkg.entities:
        if entity.type == "Organism":
            hit = organisms.get(ids.normalize(entity.label))
            if hit:
                entity.curie = hit["curie"]
                entity.label = hit["label"]
        elif entity.curie is None:
            entity.curie = regex_curie(entity.label)
    return pkg
