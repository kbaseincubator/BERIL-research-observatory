// Single-message renderer. Used for both persisted messages (from SSR) and
// in-flight streaming messages.

import type { TranscriptMessage } from "./types";

interface Props {
  message: TranscriptMessage;
}

export function MessageView({ message }: Props) {
  const isError = Boolean(message.error);
  return (
    <article style={cardStyle} data-role={message.role}>
      <header style={headerStyle}>
        <span style={{ fontWeight: 600, textTransform: "capitalize" }}>
          {message.role}
        </span>
        {message.pending && <span style={pendingBadge}>streaming…</span>}
        {message.created_at && !message.pending && (
          <span style={timestampStyle}>
            {new Date(message.created_at).toLocaleString()}
          </span>
        )}
      </header>

      {message.text && <p style={textStyle}>{message.text}</p>}

      {isError && <p style={errorStyle}>Error: {message.error}</p>}

      {message.tool_activity && message.tool_activity.length > 0 && (
        <details style={{ marginTop: 8 }}>
          <summary style={summaryStyle}>
            Tool activity ({message.tool_activity.length})
          </summary>
          <pre style={preStyle}>
            {JSON.stringify(message.tool_activity, null, 2)}
          </pre>
        </details>
      )}
    </article>
  );
}

const cardStyle: React.CSSProperties = {
  background: "var(--color-bg-elevated, #1a1a1f)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 8,
  padding: 16,
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "baseline",
  justifyContent: "space-between",
  gap: 8,
  marginBottom: 8,
};

const timestampStyle: React.CSSProperties = {
  color: "var(--color-text-muted, #9aa0a6)",
  fontSize: "0.8rem",
};

const pendingBadge: React.CSSProperties = {
  color: "#39d4e6",
  fontSize: "0.75rem",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
};

const textStyle: React.CSSProperties = {
  margin: 0,
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
};

const errorStyle: React.CSSProperties = {
  color: "#ff6b6b",
  fontSize: "0.85rem",
  marginTop: 8,
};

const summaryStyle: React.CSSProperties = {
  color: "var(--color-text-muted, #9aa0a6)",
  cursor: "pointer",
  fontSize: "0.85rem",
};

const preStyle: React.CSSProperties = {
  fontSize: "0.8rem",
  overflowX: "auto",
  background: "rgba(0,0,0,0.3)",
  padding: 10,
  borderRadius: 6,
  marginTop: 6,
};
