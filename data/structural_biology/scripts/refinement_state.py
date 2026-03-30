#!/usr/bin/env python3
"""
Project lifecycle state machine for structural biology workflows.

Manages project states and transitions through the structure determination
pipeline: data assessment, phasing, building, refinement, human inspection,
convergence, and completion.

Can be used standalone or imported by other scripts (run_pipeline.py, cycle_manager.py).

Usage:
  from refinement_state import ProjectState

  state = ProjectState.load(project_dir)
  state.transition("refining")
  state.record_cycle_metrics(cycle=3, r_work=0.21, r_free=0.25, ...)
  state.save()
"""

import json
import os
from datetime import datetime


# Valid states and allowed transitions
STATES = {
    "new",
    "xtriage",
    "phasing",
    "building",
    "refining",
    "awaiting_inspection",
    "converged",
    "complete",
}

TRANSITIONS = {
    "new": {"xtriage", "phasing", "building", "refining", "complete"},
    "xtriage": {"phasing", "building", "refining"},
    "phasing": {"building", "refining"},
    "building": {"refining", "awaiting_inspection"},
    "refining": {"awaiting_inspection", "converged", "refining"},
    "awaiting_inspection": {"refining", "converged", "complete"},
    "converged": {"refining", "complete"},  # can resume refinement if user wants
    "complete": set(),  # terminal state
}


class InvalidTransition(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class ProjectState:
    """Manages project lifecycle state backed by project_notes.json."""

    def __init__(self, project_dir, data=None):
        self.project_dir = project_dir
        self._path = os.path.join(project_dir, "project_notes.json")
        if data is not None:
            self._data = data
        else:
            self._data = {
                "project_id": os.path.basename(project_dir),
                "status": "new",
                "method": None,
                "current_cycle": 0,
                "steps_completed": [],
                "cycle_metrics": [],
                "created": datetime.now().isoformat(),
            }

    @classmethod
    def load(cls, project_dir):
        """Load project state from project_notes.json."""
        path = os.path.join(project_dir, "project_notes.json")
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            # Ensure required fields exist
            data.setdefault("status", "new")
            data.setdefault("current_cycle", 0)
            data.setdefault("steps_completed", [])
            data.setdefault("cycle_metrics", [])
            return cls(project_dir, data=data)
        return cls(project_dir)

    def save(self):
        """Save project state to project_notes.json."""
        self._data["last_updated"] = datetime.now().isoformat()
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def status(self):
        return self._data["status"]

    @property
    def method(self):
        return self._data.get("method")

    @method.setter
    def method(self, value):
        self._data["method"] = value

    @property
    def current_cycle(self):
        return self._data["current_cycle"]

    @property
    def cycle_metrics(self):
        return self._data.get("cycle_metrics", [])

    @property
    def project_id(self):
        return self._data.get("project_id", os.path.basename(self.project_dir))

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def transition(self, new_status):
        """Transition to a new state, validating the transition is allowed."""
        current = self._data["status"]
        if new_status not in STATES:
            raise InvalidTransition(f"Unknown state: {new_status}")
        if new_status not in TRANSITIONS.get(current, set()):
            raise InvalidTransition(
                f"Cannot transition from '{current}' to '{new_status}'. "
                f"Allowed: {TRANSITIONS.get(current, set())}"
            )
        self._data["status"] = new_status
        if new_status not in self._data["steps_completed"]:
            self._data["steps_completed"].append(new_status)

    def is_waiting_for_human(self):
        """Check if the project is waiting for human inspection."""
        return self._data["status"] == "awaiting_inspection"

    def is_terminal(self):
        """Check if the project is in a terminal state."""
        return self._data["status"] == "complete"

    def record_cycle_metrics(self, cycle_num, **metrics):
        """Record metrics for a refinement cycle."""
        record = {"cycle": cycle_num, "timestamp": datetime.now().isoformat()}
        record.update(metrics)
        self._data["cycle_metrics"].append(record)
        self._data["current_cycle"] = cycle_num

    def get_latest_metrics(self):
        """Get metrics from the most recent cycle."""
        if not self._data["cycle_metrics"]:
            return None
        return self._data["cycle_metrics"][-1]

    def get_metrics_history(self, metric_name):
        """Get a specific metric across all cycles."""
        return [
            (m["cycle"], m.get(metric_name))
            for m in self._data["cycle_metrics"]
            if metric_name in m
        ]

    def advance(self):
        """Determine the recommended next action based on current state and metrics.

        Returns (action, reason) tuple.
        """
        status = self._data["status"]

        if status == "new":
            return "run_xtriage", "Start with data quality assessment"

        if status == "xtriage":
            return "run_phaser", "Proceed to molecular replacement"

        if status == "phasing":
            return "run_autobuild", "Phasing done — build initial model"

        if status == "building":
            return "run_refine", "Model built — start refinement"

        if status == "refining":
            return "process_output", "Refinement cycle complete — parse results"

        if status == "awaiting_inspection":
            return "wait_for_human", "Waiting for human model inspection in Coot"

        if status == "converged":
            return "finalize", "Refinement converged — prepare final model"

        if status == "complete":
            return "done", "Project complete"

        return "unknown", f"Unrecognized state: {status}"

    def to_dict(self):
        """Return the full state as a dict."""
        return dict(self._data)

    def summary(self):
        """Return a human-readable summary string."""
        lines = [
            f"Project: {self.project_id}",
            f"Status: {self.status}",
            f"Method: {self.method or 'not set'}",
            f"Cycle: {self.current_cycle}",
            f"Steps: {', '.join(self._data['steps_completed']) or 'none'}",
        ]
        latest = self.get_latest_metrics()
        if latest:
            for key in ["r_work", "r_free", "molprobity_score", "map_model_cc"]:
                if key in latest:
                    lines.append(f"  {key}: {latest[key]}")
        action, reason = self.advance()
        lines.append(f"Next: {action} — {reason}")
        return "\n".join(lines)
