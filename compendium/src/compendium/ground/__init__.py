"""Deterministic grounding: assign CURIEs to entities via dictionary + regex."""

from compendium.ground.grounder import ground, load_dictionary, regex_curie

__all__ = ["ground", "load_dictionary", "regex_curie"]
