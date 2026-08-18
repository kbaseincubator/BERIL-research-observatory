// Top-level component. Owns turn state (messages, in-flight state, errors)
// and the credential modal. All I/O is injected as props so the component
// can be dropped into other hosts later without code changes.

import { useMemo, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { CredentialsModal } from "./CredentialsModal";
import { InputBox } from "./InputBox";
import { Transcript } from "./Transcript";
import {
  getCredentialsFor,
  hasAllCredentials,
} from "./credentialsStore";
import { streamTurn } from "./sseClient";
import type { ProviderConfig, SSEFrame, TranscriptMessage, ToolActivity } from "./types";

export interface ChatAppProps {
  sessionId: string;
  providerCatalog: ProviderConfig[];
  currentProviderId: string;
  currentModel: string;
  streamEndpoint: string; // e.g. "/api/chat/{id}/stream"
  initialMessages: TranscriptMessage[];
}

export function ChatApp(props: ChatAppProps) {
  const provider = useMemo(
    () =>
      props.providerCatalog.find((p) => p.id === props.currentProviderId) ?? null,
    [props.providerCatalog, props.currentProviderId],
  );

  const [messages, setMessages] = useState<TranscriptMessage[]>(props.initialMessages);
  const [streaming, setStreaming] = useState(false);
  const [showCreds, setShowCreds] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  // Guard against re-entry: a stray double-click on Send, or a StrictMode
  // double-render, would otherwise kick off two concurrent turns that
  // compete for the same DOM slots. `streaming` is state (renders lag), so
  // we also keep a synchronous ref.
  const inFlightRef = useRef(false);

  if (!provider) {
    return (
      <p style={{ color: "#ff6b6b" }}>
        Unknown provider {JSON.stringify(props.currentProviderId)} — check the chat
        config on the server.
      </p>
    );
  }

  function send(text: string) {
    if (!provider) return;
    if (!hasAllCredentials(provider.id, provider.credential_fields)) {
      setShowCreds(true);
      return;
    }
    startTurn(text);
  }

  function startTurn(text: string) {
    if (inFlightRef.current) return;
    inFlightRef.current = true;

    setError(null);
    const userId = tempId("user");
    const assistantId = tempId("assistant");

    // Flush the insertion synchronously before dispatching the stream so
    // that subsequent setMessages(prev => ...) calls from onFrame see the
    // new rows in `prev`. Without flushSync, the fetch/microtask scheduling
    // can race: a `text_delta` frame arrives, calls prev.map(...), but the
    // assistant row isn't in `prev` yet, so the map no-ops and the text is
    // silently lost.
    flushSync(() => {
      setMessages((prev) => [
        ...prev,
        { id: userId, role: "user", text, pending: true },
        {
          id: assistantId,
          role: "assistant",
          text: "",
          tool_activity: [],
          pending: true,
        },
      ]);
    });

    setStreaming(true);
    const controller = new AbortController();
    abortRef.current = controller;

    const activity: ToolActivity[] = [];

    streamTurn(
      {
        url: props.streamEndpoint,
        body: {
          message: text,
          credentials: getCredentialsFor(provider!.id),
        },
        signal: controller.signal,
      },
      {
        onFrame: (frame) => handleFrame(frame, userId, assistantId, activity),
        onHttpError: (status, body) => {
          // 401 → reauth. 400 → missing creds. 429 → cap. 403/404 → gone.
          let msg = `Request failed (${status})`;
          try {
            const parsed = JSON.parse(body);
            if (parsed?.error) msg = parsed.error;
          } catch {
            /* body wasn't JSON */
          }
          if (status === 401) msg = "Please log in and try again.";
          else if (status === 400 && /credential/i.test(msg)) {
            // Credentials look invalid server-side (shouldn't normally happen —
            // we pre-check on the client). Prompt the user to re-enter.
            setShowCreds(true);
          }
          setError(msg);
          finalizeAssistantWithError(userId, assistantId, msg, activity);
        },
        onNetworkError: (err) => {
          const msg =
            err instanceof Error ? err.message : "Network error — the server may be down.";
          setError(msg);
          finalizeAssistantWithError(userId, assistantId, msg, activity);
        },
        onDone: () => {
          setStreaming(false);
          abortRef.current = null;
          inFlightRef.current = false;
          // Belt-and-suspenders: clear pending on both the user and assistant
          // rows of this turn in case the stream ended without a
          // `turn_persisted` or `error` frame. Use the captured IDs so we
          // don't accidentally touch messages from an earlier turn.
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId || m.id === userId
                ? { ...m, pending: false }
                : m,
            ),
          );
        },
      },
    );
  }

  function handleFrame(
    frame: SSEFrame,
    userId: string,
    assistantId: string,
    activity: ToolActivity[],
  ) {
    switch (frame.event) {
      case "text_delta":
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, text: m.text + frame.data.text } : m,
          ),
        );
        break;
      case "tool_call":
        activity.push({
          type: "tool_call",
          name: frame.data.name,
          input: frame.data.input,
          tool_use_id: frame.data.tool_use_id,
        });
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, tool_activity: [...activity] } : m,
          ),
        );
        break;
      case "tool_result":
        activity.push({
          type: "tool_result",
          tool_use_id: frame.data.tool_use_id,
          content: frame.data.content,
          is_error: frame.data.is_error,
        });
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, tool_activity: [...activity] } : m,
          ),
        );
        break;
      case "error":
        finalizeAssistantWithError(userId, assistantId, frame.data.message, activity);
        break;
      case "turn_complete":
        // Agent finished but we still wait for `turn_persisted` before
        // dropping the pending flag.
        break;
      case "turn_persisted":
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === assistantId) {
              return {
                ...m,
                id: frame.data.assistant_message_id || m.id,
                pending: false,
              };
            }
            if (m.id === userId) {
              return { ...m, pending: false };
            }
            return m;
          }),
        );
        break;
      case "session_initialized":
        // Backend bookkeeping; nothing for the UI to render here.
        break;
    }
  }

  function finalizeAssistantWithError(
    userId: string,
    assistantId: string,
    msg: string,
    activity: ToolActivity[],
  ) {
    setMessages((prev) =>
      prev.map((m) => {
        if (m.id === assistantId) {
          return {
            ...m,
            pending: false,
            error: msg,
            tool_activity: activity.slice(),
          };
        }
        if (m.id === userId) {
          return { ...m, pending: false };
        }
        return m;
      }),
    );
  }

  function stop() {
    abortRef.current?.abort();
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, minHeight: 200 }}>
      {error && (
        <div role="alert" style={errorBarStyle}>
          {error}
        </div>
      )}
      <Transcript messages={messages} />
      <InputBox
        disabled={streaming}
        streaming={streaming}
        onSend={send}
        onStop={stop}
        onEditCredentials={() => setShowCreds(true)}
      />
      <CredentialsModal
        provider={provider}
        open={showCreds}
        onClose={() => setShowCreds(false)}
        onSave={() => setError(null)}
      />
    </div>
  );
}

let _idCounter = 0;
function tempId(prefix: string): string {
  _idCounter += 1;
  return `${prefix}-tmp-${_idCounter}-${Date.now()}`;
}

const errorBarStyle: React.CSSProperties = {
  background: "rgba(255,107,107,0.1)",
  border: "1px solid rgba(255,107,107,0.4)",
  color: "#ff9a9a",
  borderRadius: 6,
  padding: "8px 12px",
  fontSize: "0.9rem",
};
