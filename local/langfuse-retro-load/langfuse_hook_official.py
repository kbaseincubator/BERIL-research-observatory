#!/usr/bin/env python3
"""
Claude Code -> Langfuse hook

Vendored unmodified from Langfuse's official Claude Code integration,
https://langfuse.com/integrations/developer-tools/claude-code, retrieved
2026-08-20. Update by re-fetching from that page, not by hand-editing here.

License: the integration page itself states no separate license for this
code sample. It's published as part of the langfuse/langfuse-docs
repository, which GitHub records as MIT-licensed
(https://github.com/langfuse/langfuse-docs, checked 2026-08-20).
"""

import json
import logging
import os
import sys
import threading
import time
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- Langfuse import (fail-open) ---
try:
    from langfuse import Langfuse, propagate_attributes
    from opentelemetry import trace as otel_trace_api
except Exception:
    sys.exit(0)

# --- Paths ---
STATE_DIR = Path.home() / ".claude" / "state"
LOG_FILE = STATE_DIR / "langfuse_hook.log"
STATE_FILE = STATE_DIR / "langfuse_state.json"
LOCK_FILE = STATE_DIR / "langfuse_state.lock"

DEBUG = os.environ.get("CC_LANGFUSE_DEBUG", "").lower() == "true"
try:
    MAX_CHARS = int(os.environ.get("CC_LANGFUSE_MAX_CHARS", "20000"))
except ValueError:
    MAX_CHARS = 20000

# ----------------- Logging -----------------
_logger: Optional[logging.Logger] = None

def _get_logger() -> Optional[logging.Logger]:
    global _logger
    if _logger is not None:
        return _logger
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        lg = logging.getLogger("langfuse_hook")
        lg.setLevel(logging.DEBUG if DEBUG else logging.INFO)
        if not lg.handlers:
            h = RotatingFileHandler(str(LOG_FILE), maxBytes=5_000_000, backupCount=3)
            h.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            lg.addHandler(h)
        _logger = lg
        return _logger
    except Exception:
        return None

def debug(msg: str) -> None:
    if not DEBUG:
        return
    lg = _get_logger()
    if lg is not None:
        try:
            lg.debug(msg)
        except Exception:
            pass

def info(msg: str) -> None:
    lg = _get_logger()
    if lg is not None:
        try:
            lg.info(msg)
        except Exception:
            pass

# ----------------- State locking (best-effort) -----------------
class FileLock:
    def __init__(self, path: Path, timeout_s: float = 2.0):
        self.path = path
        self.timeout_s = timeout_s
        self._fh = None

    def __enter__(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a+", encoding="utf-8")
        self.acquired = False
        try:
            import fcntl  # Unix only
        except ImportError:
            # No fcntl available (e.g. Windows) — proceed without lock.
            return self
        deadline = time.time() + self.timeout_s
        try:
            while True:
                try:
                    fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.acquired = True
                    return self
                except BlockingIOError:
                    if time.time() > deadline:
                        raise TimeoutError(
                            f"could not acquire {self.path} within {self.timeout_s}s"
                        )
                    time.sleep(0.05)
        except BaseException:
            # __exit__ is not called when __enter__ raises — close the fh
            # we just opened so it doesn't leak.
            try:
                self._fh.close()
            except Exception:
                pass
            raise

    def __exit__(self, exc_type, exc, tb):
        try:
            import fcntl
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            self._fh.close()
        except Exception:
            pass

def load_state() -> Dict[str, Any]:
    try:
        if not STATE_FILE.exists():
            return {}
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_state(state: Dict[str, Any]) -> None:
    try:
        # Drop session entries older than 30 days to keep the file bounded.
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        for k in list(state.keys()):
            entry = state.get(k)
            if not isinstance(entry, dict):
                continue
            updated = entry.get("updated")
            if not isinstance(updated, str):
                continue
            try:
                ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            except Exception:
                continue
            if ts < cutoff:
                del state[k]
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        debug(f"save_state failed: {e}")

def state_key(session_id: str, transcript_path: str) -> str:
    # stable key even if session_id collides
    raw = f"{session_id}::{transcript_path}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

# ----------------- Hook payload -----------------
def read_hook_payload() -> Dict[str, Any]:
    """
    Claude Code hooks pass a JSON payload on stdin.
    This script tolerates missing/empty stdin by returning {}.
    """
    try:
        data = sys.stdin.read()
        debug(f"stdin received {len(data)} chars")
        if not data.strip():
            return {}
        parsed = json.loads(data)
        if isinstance(parsed, dict):
            debug(f"payload top-level keys: {sorted(parsed.keys())}")
        return parsed
    except Exception as e:
        debug(f"read_hook_payload exception: {e!r}")
        return {}

def extract_session_and_transcript(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[Path]]:
    """
    Tries a few plausible field names; exact keys can vary across hook types/versions.
    Prefer structured values from stdin over heuristics.
    """
    session_id = (
        payload.get("sessionId")
        or payload.get("session_id")
        or payload.get("session", {}).get("id")
    )

    transcript = (
        payload.get("transcriptPath")
        or payload.get("transcript_path")
        or payload.get("transcript", {}).get("path")
    )

    if transcript:
        try:
            transcript_path = Path(transcript).expanduser().resolve()
        except Exception:
            transcript_path = None
    else:
        transcript_path = None

    return session_id, transcript_path

# ----------------- Transcript parsing helpers -----------------
def get_content(msg: Dict[str, Any]) -> Any:
    if not isinstance(msg, dict):
        return None
    if "message" in msg and isinstance(msg.get("message"), dict):
        return msg["message"].get("content")
    return msg.get("content")

def get_role(msg: Dict[str, Any]) -> Optional[str]:
    # Claude Code transcript lines commonly have type=user/assistant OR message.role
    t = msg.get("type")
    if t in ("user", "assistant"):
        return t
    m = msg.get("message")
    if isinstance(m, dict):
        r = m.get("role")
        if r in ("user", "assistant"):
            return r
    return None

def is_tool_result(msg: Dict[str, Any]) -> bool:
    role = get_role(msg)
    if role != "user":
        return False
    content = get_content(msg)
    if isinstance(content, list):
        return any(isinstance(x, dict) and x.get("type") == "tool_result" for x in content)
    return False

def iter_tool_results(content: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if isinstance(content, list):
        for x in content:
            if isinstance(x, dict) and x.get("type") == "tool_result":
                out.append(x)
    return out

def iter_tool_uses(content: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if isinstance(content, list):
        for x in content:
            if isinstance(x, dict) and x.get("type") == "tool_use":
                out.append(x)
    return out

def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for x in content:
            if isinstance(x, dict) and x.get("type") == "text":
                parts.append(x.get("text", ""))
            elif isinstance(x, str):
                parts.append(x)
        return "\n".join([p for p in parts if p])
    return ""

def truncate_text(s: str, max_chars: int = MAX_CHARS) -> Tuple[str, Dict[str, Any]]:
    if s is None:
        return "", {"truncated": False, "orig_len": 0}
    orig_len = len(s)
    if orig_len <= max_chars:
        return s, {"truncated": False, "orig_len": orig_len}
    head = s[:max_chars]
    return head, {"truncated": True, "orig_len": orig_len, "kept_len": len(head), "sha256": hashlib.sha256(s.encode("utf-8")).hexdigest()}

def get_model(msg: Dict[str, Any]) -> str:
    m = msg.get("message")
    if isinstance(m, dict):
        return m.get("model") or "claude"
    return "claude"

def get_usage(msg: Dict[str, Any]) -> Optional[Dict[str, int]]:
    """Extract Anthropic token usage from an assistant message, if present."""
    m = msg.get("message")
    if not isinstance(m, dict):
        return None
    u = m.get("usage")
    if not isinstance(u, dict):
        return None
    details: Dict[str, int] = {}
    for src, dst in (
        ("input_tokens", "input"),
        ("output_tokens", "output"),
        ("cache_read_input_tokens", "cache_read_input_tokens"),
        ("cache_creation_input_tokens", "cache_creation_input_tokens"),
    ):
        v = u.get(src)
        if isinstance(v, int) and v > 0:
            details[dst] = v
    return details or None

def get_message_id(msg: Dict[str, Any]) -> Optional[str]:
    m = msg.get("message")
    if isinstance(m, dict):
        mid = m.get("id")
        if isinstance(mid, str) and mid:
            return mid
    return None

def parse_ts(value: Any) -> Optional[datetime]:
    """Parse a Claude Code jsonl row timestamp (ISO 8601 with trailing Z)."""
    if isinstance(value, dict):
        value = value.get("timestamp")
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None

# ----------------- Incremental reader -----------------
@dataclass
class SessionState:
    offset: int = 0
    buffer: str = ""
    turn_count: int = 0

def load_session_state(global_state: Dict[str, Any], key: str) -> SessionState:
    s = global_state.get(key, {})
    return SessionState(
        offset=int(s.get("offset", 0)),
        buffer=str(s.get("buffer", "")),
        turn_count=int(s.get("turn_count", 0)),
    )

def write_session_state(global_state: Dict[str, Any], key: str, ss: SessionState) -> None:
    global_state[key] = {
        "offset": ss.offset,
        "buffer": ss.buffer,
        "turn_count": ss.turn_count,
        "updated": datetime.now(timezone.utc).isoformat(),
    }

def read_new_jsonl(transcript_path: Path, ss: SessionState) -> Tuple[List[Dict[str, Any]], SessionState]:
    """
    Reads only new bytes since ss.offset. Keeps ss.buffer for partial last line.
    Returns parsed JSON lines (best-effort) and updated state.
    """
    if not transcript_path.exists():
        return [], ss

    try:
        file_size = transcript_path.stat().st_size
        if file_size < ss.offset:
            # Transcript was rotated or truncated — restart from the beginning.
            debug(f"transcript shrank ({file_size} < {ss.offset}); restarting")
            ss.offset = 0
            ss.buffer = ""
        with open(transcript_path, "rb") as f:
            f.seek(ss.offset)
            chunk = f.read()
            new_offset = f.tell()
    except Exception as e:
        debug(f"read_new_jsonl failed: {e}")
        return [], ss

    if not chunk:
        return [], ss

    try:
        text = chunk.decode("utf-8", errors="replace")
    except Exception:
        text = chunk.decode(errors="replace")

    combined = ss.buffer + text
    lines = combined.split("\n")
    # last element may be incomplete
    ss.buffer = lines[-1]
    ss.offset = new_offset

    msgs: List[Dict[str, Any]] = []
    for line in lines[:-1]:
        line = line.strip()
        if not line:
            continue
        try:
            msgs.append(json.loads(line))
        except Exception:
            continue

    return msgs, ss

# ----------------- Turn assembly -----------------
@dataclass
class Turn:
    user_msg: Dict[str, Any]
    assistant_msgs: List[Dict[str, Any]]
    tool_results_by_id: Dict[str, Any]

def build_turns(messages: List[Dict[str, Any]]) -> List[Turn]:
    """
    Groups incremental transcript rows into turns:
    user (non-tool-result) -> assistant messages -> (tool_result rows, possibly interleaved)
    Uses:
    - assistant message dedupe by message.id (latest row wins)
    - tool results dedupe by tool_use_id (latest wins)
    """
    turns: List[Turn] = []
    current_user: Optional[Dict[str, Any]] = None

    # assistant messages for current turn:
    assistant_order: List[str] = []             # message ids in order of first appearance (or synthetic)
    assistant_latest: Dict[str, Dict[str, Any]] = {}  # id -> latest msg

    tool_results_by_id: Dict[str, Any] = {}     # tool_use_id -> content

    def flush_turn():
        nonlocal current_user, assistant_order, assistant_latest, tool_results_by_id, turns
        if current_user is None:
            return
        if not assistant_latest:
            return
        assistants = [assistant_latest[mid] for mid in assistant_order if mid in assistant_latest]
        turns.append(Turn(user_msg=current_user, assistant_msgs=assistants, tool_results_by_id=dict(tool_results_by_id)))

    for msg in messages:
        role = get_role(msg)

        # tool_result rows show up as role=user with content blocks of type tool_result
        if is_tool_result(msg):
            row_ts = msg.get("timestamp")
            for tr in iter_tool_results(get_content(msg)):
                tid = tr.get("tool_use_id")
                if tid:
                    tool_results_by_id[str(tid)] = {"content": tr.get("content"), "timestamp": row_ts}
            continue

        if role == "user":
            # new user message -> finalize previous turn
            flush_turn()

            # start a new turn
            current_user = msg
            assistant_order = []
            assistant_latest = {}
            tool_results_by_id = {}
            continue

        if role == "assistant":
            if current_user is None:
                # ignore assistant rows until we see a user message
                continue

            mid = get_message_id(msg) or f"noid:{len(assistant_order)}"
            if mid not in assistant_latest:
                assistant_order.append(mid)
            assistant_latest[mid] = msg
            continue

        # ignore unknown rows

    # flush last
    flush_turn()
    return turns

# ----------------- Langfuse emit -----------------
def _to_ns(ts: Optional[datetime]) -> Optional[int]:
    """Convert a datetime to OTel-style nanoseconds since epoch."""
    if ts is None:
        return None
    return int(ts.timestamp() * 1_000_000_000)


def _start_backdated(langfuse: Langfuse, *, name: str, as_type: str,
                     start_time: Optional[datetime],
                     parent_otel_span: Any = None,
                     **obs_kwargs: Any) -> Any:
    """Create a Langfuse observation with an explicit OTel start_time.

    Bypasses langfuse.start_observation() (which has no start_time kwarg in
    SDK 4.x) by talking to the underlying OTel tracer directly and then
    wrapping the resulting span with the Langfuse observation type.

    Depends on SDK 4.x internals: langfuse._otel_tracer and
    langfuse._create_observation_from_otel_span. If a future SDK version
    renames or removes these, raise a clear error instead of letting an
    AttributeError get swallowed by the broad emit_turn handler.
    """
    if not hasattr(langfuse, "_otel_tracer") or not hasattr(langfuse, "_create_observation_from_otel_span"):
        try:
            sdk_version = getattr(__import__("langfuse"), "__version__", "unknown")
        except Exception:
            sdk_version = "unknown"
        raise RuntimeError(
            f"Langfuse SDK {sdk_version} is missing _otel_tracer or "
            f"_create_observation_from_otel_span. This hook targets SDK 4.x; "
            f"pin with `pip install \"langfuse>=4.0,<5\"` or update the hook script."
        )
    start_ns = _to_ns(start_time)
    if parent_otel_span is not None:
        with otel_trace_api.use_span(parent_otel_span, end_on_exit=False):
            otel_span = langfuse._otel_tracer.start_span(name=name, start_time=start_ns)
    else:
        otel_span = langfuse._otel_tracer.start_span(name=name, start_time=start_ns)
    return langfuse._create_observation_from_otel_span(
        otel_span=otel_span,
        as_type=as_type,
        **obs_kwargs,
    )


def emit_turn(langfuse: Langfuse, session_id: str, turn_num: int, turn: Turn, transcript_path: Path) -> None:
    user_text_raw = extract_text(get_content(turn.user_msg))
    user_text, user_text_meta = truncate_text(user_text_raw)

    last_assistant = turn.assistant_msgs[-1]
    final_assistant_text, _ = truncate_text(extract_text(get_content(last_assistant)))

    user_ts = parse_ts(turn.user_msg)
    last_assistant_ts = parse_ts(last_assistant)
    # Pick a turn end_time: latest among final assistant message or any tool result
    candidate_end_ts = [t for t in [last_assistant_ts] if t is not None]
    for tr in turn.tool_results_by_id.values():
        t = parse_ts(tr)
        if t is not None:
            candidate_end_ts.append(t)
    turn_end_ts = max(candidate_end_ts) if candidate_end_ts else None

    with propagate_attributes(
        session_id=session_id,
        trace_name=f"Claude Code - Turn {turn_num}",
        tags=["claude-code"],
    ):
        trace_span = _start_backdated(
            langfuse,
            name=f"Claude Code - Turn {turn_num}",
            as_type="span",
            start_time=user_ts,
            input={"role": "user", "content": user_text},
            metadata={
                "source": "claude-code",
                "session_id": session_id,
                "turn_number": turn_num,
                "transcript_path": str(transcript_path),
                "user_text": user_text_meta,
                "assistant_message_count": len(turn.assistant_msgs),
            },
        )
        parent_otel_span = trace_span._otel_span

        # Iterate each assistant message: emit generation, then its tool_use children.
        # prev_ts = the moment the next generation could have started (= when the previous
        # batch of tool results all returned, or the original user message timestamp).
        prev_ts = user_ts
        prev_tool_results: List[Dict[str, Any]] = []  # populated after each batch, surfaced as next gen's input

        for idx, am in enumerate(turn.assistant_msgs):
            am_ts = parse_ts(am)
            am_text_raw = extract_text(get_content(am))
            am_text, am_text_meta = truncate_text(am_text_raw)
            model = get_model(am)
            tool_uses = iter_tool_uses(get_content(am))

            # Build generation input: user message for first generation, otherwise tool results from
            # the prior batch (best partial reconstruction of the prompt context).
            if idx == 0:
                gen_input: Any = {"role": "user", "content": user_text}
            elif prev_tool_results:
                gen_input = {"role": "tool", "tool_results": prev_tool_results}
            else:
                gen_input = None

            # Build generation output: include both the text response and any tool calls the LLM
            # decided to make. Most assistant messages in tool-using turns are tool-call-only, so
            # without tool_calls in the output, the observation looks empty.
            gen_tool_calls = []
            for tu in tool_uses:
                tu_input = tu.get("input")
                if isinstance(tu_input, str):
                    tu_input_serialized, _ = truncate_text(tu_input)
                else:
                    tu_input_serialized = tu_input
                gen_tool_calls.append({
                    "id": tu.get("id"),
                    "name": tu.get("name"),
                    "input": tu_input_serialized,
                })

            gen_output: Dict[str, Any] = {"role": "assistant"}
            if am_text:
                gen_output["content"] = am_text
            if gen_tool_calls:
                gen_output["tool_calls"] = gen_tool_calls

            gen_kwargs: Dict[str, Any] = dict(
                model=model,
                input=gen_input,
                output=gen_output,
                metadata={
                    "assistant_index": idx,
                    "assistant_text": am_text_meta,
                    "tool_count": len(tool_uses),
                },
            )
            usage_details = get_usage(am)
            if usage_details is not None:
                gen_kwargs["usage_details"] = usage_details

            gen_span = _start_backdated(
                langfuse,
                name=f"Claude Generation {idx + 1}",
                as_type="generation",
                start_time=prev_ts or am_ts,
                parent_otel_span=parent_otel_span,
                **gen_kwargs,
            )

            # Tool observations: nested under this generation. Each starts when the assistant
            # emitted the tool_use (am_ts) and ends when its tool_result row arrived.
            batch_result_ts: List[datetime] = []
            batch_tool_results: List[Dict[str, Any]] = []
            for tu in tool_uses:
                tid = str(tu.get("id") or "")
                tname = tu.get("name") or "unknown"
                tinput_raw = tu.get("input") if isinstance(tu.get("input"), (dict, list, str, int, float, bool)) else {}
                if isinstance(tinput_raw, str):
                    tinput, tinput_meta = truncate_text(tinput_raw)
                else:
                    tinput, tinput_meta = tinput_raw, None

                tr_entry = turn.tool_results_by_id.get(tid) if tid else None
                if tr_entry:
                    out_raw = tr_entry.get("content")
                    out_str = out_raw if isinstance(out_raw, str) else json.dumps(out_raw, ensure_ascii=False)
                    out_trunc, out_meta = truncate_text(out_str)
                    tr_ts = parse_ts(tr_entry.get("timestamp"))
                else:
                    out_trunc, out_meta, tr_ts = None, None, None
                if tr_ts is not None:
                    batch_result_ts.append(tr_ts)

                tool_span = _start_backdated(
                    langfuse,
                    name=f"Tool: {tname}",
                    as_type="tool",
                    start_time=am_ts,
                    parent_otel_span=gen_span._otel_span,
                    input=tinput,
                    metadata={
                        "tool_name": tname,
                        "tool_id": tid,
                        "input_meta": tinput_meta,
                        "output_meta": out_meta,
                    },
                )
                tool_span.update(output=out_trunc)
                tool_span.end(end_time=_to_ns(tr_ts or am_ts))

                batch_tool_results.append({
                    "tool_use_id": tid,
                    "tool_name": tname,
                    "output": out_trunc,
                })

            # End the generation AFTER its tools so the timeline cleanly contains them.
            # If there were tool calls, gen ends with the last result; otherwise at am_ts.
            gen_end_ts = max(batch_result_ts) if batch_result_ts else am_ts
            gen_span.end(end_time=_to_ns(gen_end_ts or am_ts or prev_ts))

            # Carry this batch's results into the next generation's input.
            prev_tool_results = batch_tool_results

            # Advance prev_ts: next generation can only start after this batch's tool results returned.
            if batch_result_ts:
                prev_ts = max(batch_result_ts)
            elif am_ts is not None:
                prev_ts = am_ts

        trace_span.update(output={"role": "assistant", "content": final_assistant_text})
        trace_span.end(end_time=_to_ns(turn_end_ts or last_assistant_ts or user_ts))

# ----------------- Main -----------------
def main() -> int:
    start = time.time()
    debug("Hook started")

    if os.environ.get("TRACE_TO_LANGFUSE", "") != "true":
        return 0

    public_key = os.environ.get("CC_LANGFUSE_PUBLIC_KEY") or os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("CC_LANGFUSE_SECRET_KEY") or os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("CC_LANGFUSE_BASE_URL") or os.environ.get("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"

    if not public_key or not secret_key:
        return 0

    payload = read_hook_payload()
    session_id, transcript_path = extract_session_and_transcript(payload)

    if not session_id or not transcript_path:
        # No structured payload; fail open (do not guess)
        debug("Missing session_id or transcript_path from hook payload; exiting.")
        return 0

    if not transcript_path.exists():
        debug(f"Transcript path does not exist: {transcript_path}")
        return 0

    langfuse = None
    try:
        langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    except Exception:
        return 0

    try:
        with FileLock(LOCK_FILE):
            state = load_state()
            key = state_key(session_id, str(transcript_path))
            ss = load_session_state(state, key)

            msgs, ss = read_new_jsonl(transcript_path, ss)
            if not msgs:
                write_session_state(state, key, ss)
                save_state(state)
                return 0

            turns = build_turns(msgs)
            if not turns:
                write_session_state(state, key, ss)
                save_state(state)
                return 0

            # emit turns
            emitted = 0
            for t in turns:
                emitted += 1
                turn_num = ss.turn_count + emitted
                try:
                    emit_turn(langfuse, session_id, turn_num, t, transcript_path)
                except Exception as e:
                    # Log at INFO so SDK incompatibilities (and other emit failures)
                    # are visible without needing CC_LANGFUSE_DEBUG=true.
                    info(f"emit_turn failed: {type(e).__name__}: {e}")
                    # continue emitting other turns

            ss.turn_count += emitted
            write_session_state(state, key, ss)
            save_state(state)

        dur = time.time() - start
        info(f"Processed {emitted} turns in {dur:.2f}s (session={session_id})")
        return 0

    except TimeoutError as e:
        debug(f"lock timeout, skipping: {e}")
        return 0

    except Exception as e:
        debug(f"Unexpected failure: {e}")
        return 0

    finally:
        # Cap flush+shutdown at 5s so a slow/unreachable Langfuse can't stall Claude Code.
        if langfuse is not None:
            try:
                def _flush_and_shutdown():
                    try:
                        langfuse.flush()
                    except Exception:
                        pass
                    langfuse.shutdown()
                t = threading.Thread(target=_flush_and_shutdown, daemon=True)
                t.start()
                t.join(5.0)
            except Exception:
                pass

if __name__ == "__main__":
    sys.exit(main())
