"""Test fixtures for knowledge ingest tests.

Disable inter-batch pacing during tests so the suite stays fast.
"""
from __future__ import annotations

import os

os.environ.setdefault("OV_INGEST_INTER_BATCH_PAUSE", "0")
