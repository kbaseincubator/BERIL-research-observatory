// Textarea + send button + stop button.
// Submits on Enter (Shift+Enter for newline), disabled while a turn is in flight.

import { useEffect, useRef, useState } from "react";

interface Props {
  disabled: boolean;
  streaming: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
  onEditCredentials: () => void;
}

export function InputBox({
  disabled,
  streaming,
  onSend,
  onStop,
  onEditCredentials,
}: Props) {
  const [text, setText] = useState("");
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // Auto-grow the textarea up to a cap.
    const el = taRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 240)}px`;
  }, [text]);

  function send() {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  }

  function handleKey(ev: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      send();
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <textarea
        ref={taRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKey}
        placeholder="Ask something, or describe what you want to build…"
        rows={2}
        disabled={disabled && !streaming}
        style={textareaStyle}
      />
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
        <button type="button" onClick={onEditCredentials} style={btnOutline}>
          Edit credentials
        </button>
        {streaming ? (
          <button type="button" onClick={onStop} style={btnDanger}>
            Stop
          </button>
        ) : (
          <button
            type="button"
            onClick={send}
            disabled={disabled || text.trim().length === 0}
            style={btnPrimary}
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}

const textareaStyle: React.CSSProperties = {
  width: "100%",
  minHeight: 48,
  maxHeight: 240,
  resize: "none",
  background: "rgba(0,0,0,0.3)",
  color: "inherit",
  border: "1px solid rgba(255,255,255,0.15)",
  borderRadius: 8,
  padding: "10px 12px",
  fontFamily: "inherit",
  fontSize: "0.95rem",
  lineHeight: 1.4,
};

const btnBase: React.CSSProperties = {
  borderRadius: 6,
  padding: "8px 14px",
  cursor: "pointer",
  fontWeight: 500,
  border: "none",
};

const btnPrimary: React.CSSProperties = {
  ...btnBase,
  background: "#39d4e6",
  color: "#0a0a0a",
};

const btnOutline: React.CSSProperties = {
  ...btnBase,
  background: "transparent",
  color: "inherit",
  border: "1px solid rgba(255,255,255,0.25)",
};

const btnDanger: React.CSSProperties = {
  ...btnBase,
  background: "#ff6b6b",
  color: "#0a0a0a",
};
