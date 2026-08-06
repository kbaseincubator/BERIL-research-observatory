"""`beril approve` — the record of the plan-review checkpoint, and of how it happened.

`status: proposed` is written by the agent, so it proves nothing: a plan never
shown to anyone and a plan a scientist read and accepted are byte-identical on
disk. This command is the one manifest write that records HOW an approval was
obtained: WHICH plan was accepted, as a digest, plus `via: terminal` when a
human answered the prompt here, or `via: agent-relayed` when an agent asserts
(`--relayed`) that the user approved in conversation.

Neither mode proves a human was involved. A pty walks straight past the TTY
check, and `--relayed` is an assertion the CLI cannot check at all. What this
produces is a checkable claim, labelled with its own provenance, sitting in the
diff next to the plan it names — a reviewer who sees `agent-relayed` knows what
to ask about.

The witness (`.claude/hooks/plan-gate.py`) compares that digest against the plan
on disk and records a deviation when they differ — it never blocks a write. It
reads only `plan_hash`, so neither `status` nor `via` changes anything the
witness sees.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from beril_cli import config
from beril_cli.audit_cmd import block_span
from beril_cli.claims_cmd import _find_repo_root
from beril_cli.detect import _normalize_orcid
from beril_cli.setup_cmd import _confirm

_REVISION_HISTORY = re.compile(rb"^##[ \t]+Revision History[ \t\r]*$", re.MULTILINE)
_NEXT_SECTION = re.compile(rb"^##[ \t]", re.MULTILINE)
_ORCID = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")


def plan_digest(plan_bytes: bytes) -> str:
    """Hash the material part of a research plan.

    Covers everything ABOVE the ``## Revision History`` heading (the whole file
    when that heading is absent). This preserves the repo's minor/material
    distinction: a minor deviation logged as a Revision History append leaves
    the approval standing, while a material change — a dropped hypothesis, a
    moved threshold, an abandoned discrimination strategy, all of which live
    above that heading — invalidates it.

    Not to be confused with ``tools/review.sh``'s ``plan_hash``, which is a
    whole-file sha256: that one attests "the reviewer saw exactly these bytes",
    this one attests "the approved science is unchanged".

    Twin: ``.claude/hooks/plan-gate.py`` carries a second copy of this rule.
    The hook runs on system python without the venv and cannot import
    beril_cli, so the duplication is deliberate. The two take different
    arguments and are not byte-identical sources — they must agree on OUTPUT,
    and
    ``tests/test_plan_gate.py::test_digest_twins_agree`` runs both over the same
    bytes to catch a drift.

    Takes **bytes**, not text, on purpose: ``Path.read_text`` translates CRLF to
    LF, the hook hashes the file as it lies on disk, and a CRLF plan would
    otherwise record an approval the gate could never match.

    Parameters
    ----------
    plan_bytes
        Raw bytes of a ``RESEARCH_PLAN.md``, read without newline translation.
    """
    match = _REVISION_HISTORY.search(plan_bytes)
    if match is None:
        return hashlib.sha256(plan_bytes).hexdigest()
    tail = plan_bytes[match.end() :]
    following = _NEXT_SECTION.search(tail)
    rest = tail[following.start() :] if following is not None else b""
    return hashlib.sha256(plan_bytes[: match.start()] + rest).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _drop_plan_approval(manifest_text: str) -> str:
    """Remove an existing top-level ``plan_approval:`` block (key + indented lines).

    Re-approving replaces the record rather than stacking a second block that
    YAML would resolve to whichever came last.
    """
    span = block_span(manifest_text, "plan_approval:")
    if span is None:
        return manifest_text
    start, end = span
    return manifest_text[:start] + manifest_text[end:]


def run_approve(args: argparse.Namespace) -> int:
    """Record a human's approval of `projects/<id>/RESEARCH_PLAN.md`."""
    root = _find_repo_root()
    if root is None:
        print("Error: not inside a BERIL repo (no PROJECT.md found)", file=sys.stderr)
        return 1

    # A project id is a directory name, not a path: `../escape` would otherwise
    # stamp an approval into a directory that is not a project at all.
    # `Path("..").name` is `".."`, so the name check alone lets `..` through.
    if not args.project or args.project in (".", "..") or args.project != Path(args.project).name:
        print(
            f"Error: unknown project '{args.project}' — a project id is a single"
            " directory name directly under projects/",
            file=sys.stderr,
        )
        return 1

    project_dir = root / "projects" / args.project
    plan_path = project_dir / "RESEARCH_PLAN.md"
    if not plan_path.exists():
        print(
            f"Error: no plan at {plan_path} — write the plan first (/research-plan)",
            file=sys.stderr,
        )
        return 1

    # Not the security boundary: an agent can allocate a pty and drive the
    # prompt below to completion, so a TTY proves nothing either. What it does
    # is force an agent that cannot prompt to say so, on the record, with
    # --relayed. The actual control is that beril.yaml is a reviewed file: the
    # approval block, `via` included, shows up in the diff at PR time, next to
    # the plan it claims to approve.
    if not args.relayed and not sys.stdin.isatty():
        print(
            "Error: no terminal here, so there is nobody to ask.\n"
            'A user saying "approved" in conversation is not a record of the'
            " approval — this manifest is.\n"
            "If the user did approve this plan, re-run with --relayed to record"
            " that (it lands as via: agent-relayed).\n"
            "If they did not, ask them first.",
            file=sys.stderr,
        )
        return 1

    configured = config.load().get("user", {}).get("orcid", "")
    if not configured:
        print(
            "Error: no ORCID configured — run `beril setup`. No anonymous approvals.",
            file=sys.stderr,
        )
        return 1
    # `beril setup` stores whatever was typed, and this repo's house style is
    # the URL form, so normalize before matching — otherwise pasting a canonical
    # https://orcid.org/... id hard-fails at the mandatory human checkpoint.
    # Report the value as CONFIGURED, not as normalized: an empty normalization
    # means malformed, which is a different diagnosis from "none set".
    orcid = _normalize_orcid(configured)
    if not _ORCID.match(orcid):
        print(
            f"Error: '{configured}' is not a valid ORCID (0000-0000-0000-0000)"
            " — fix it with `beril setup`. An unparseable approver is not an approver.",
            file=sys.stderr,
        )
        return 1

    manifest = project_dir / "beril.yaml"

    # Absolute, because this repo has several live worktrees and approving from
    # the wrong checkout is otherwise undiagnosable.
    print(f"Plan:     {plan_path.resolve()}")
    print(f"Manifest: {manifest.resolve()}")
    print(f"Approver: {orcid}")
    if args.relayed:
        # --relayed is an assertion about provenance, not about the pipe: it
        # records agent-relayed even at a TTY, and there is nobody at the other
        # end of a pipe to prompt, so it never asks.
        print(
            "WARNING: relayed approval — the CLI did not witness this one.\n"
            "  It is recorded as `via: agent-relayed` in beril.yaml, and a"
            " reviewer will see that in the diff.\n"
            "  It is honest only if the user actually said they approve this plan."
        )
    elif not _confirm(f"Approve this plan for '{args.project}'?", default=False):
        print("Not approved — nothing written.")
        return 1

    # Read AFTER the answer, never before: the record has to attest to the plan
    # as it stood when the human said yes, not to bytes that may have been
    # rewritten while the prompt sat open. The relayed path asks nothing, so
    # there is no window: it hashes at the moment it records.
    digest = plan_digest(plan_path.read_bytes())

    text = (
        manifest.read_text(encoding="utf-8")
        if manifest.exists()
        else f"project_id: {args.project}\nstatus: proposed\n"
    )
    text = _drop_plan_approval(text)
    if text and not text.endswith("\n"):
        text += "\n"
    text += (
        "plan_approval:\n"
        f'  by: "{orcid}"\n'
        f'  at: "{_now_iso()}"\n'
        f"  via: {'agent-relayed' if args.relayed else 'terminal'}\n"
        f'  plan_hash: "sha256:{digest}"\n'
    )
    manifest.write_text(text, encoding="utf-8")

    print(f"Approved — plan_approval recorded in {manifest.resolve()}")
    print(
        "It enters the project's history with the next commit, in the diff"
        " beside the plan it names."
    )
    return 0
