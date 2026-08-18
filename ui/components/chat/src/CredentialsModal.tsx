// Modal shown when the user tries to send a message and credentials are
// missing (or when they click "Edit credentials"). Data-driven by the
// provider's declared credential_fields — works unchanged when we add
// Bedrock-style multi-field credentials.

import { useEffect, useState } from "react";
import type { ProviderConfig } from "./types";
import { getCredentialsFor, setCredentialsFor } from "./credentialsStore";

interface Props {
  provider: ProviderConfig;
  open: boolean;
  onClose: () => void;
  /** Called after a successful save with the saved values. */
  onSave: (values: Record<string, string>) => void;
}

export function CredentialsModal({ provider, open, onClose, onSave }: Props) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setValues(getCredentialsFor(provider.id));
      setError(null);
    }
  }, [open, provider.id]);

  if (!open) return null;

  function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    const missing = provider.credential_fields.filter(
      (f) => !values[f.id] || values[f.id].length === 0,
    );
    if (missing.length > 0) {
      setError(`Missing: ${missing.map((f) => f.display_name).join(", ")}`);
      return;
    }
    setCredentialsFor(provider.id, values);
    onSave(values);
    onClose();
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="chat-cred-title"
      style={overlayStyle}
      onClick={onClose}
    >
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        <h2 id="chat-cred-title" style={{ marginTop: 0 }}>
          Credentials for {provider.display_name}
        </h2>
        <p style={subtleText}>
          Stored in your browser only. Never sent to any BERIL server for
          persistence — only forwarded per-turn to the LLM provider.
        </p>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {provider.credential_fields.map((f) => (
            <label key={f.id} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span>{f.display_name}</span>
              <input
                type={f.secret ? "password" : "text"}
                value={values[f.id] ?? ""}
                onChange={(e) =>
                  setValues((prev) => ({ ...prev, [f.id]: e.target.value }))
                }
                autoComplete={f.secret ? "new-password" : "on"}
                spellCheck={false}
                style={inputStyle}
                required
              />
            </label>
          ))}
          {error && <p style={errorStyle}>{error}</p>}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button type="button" onClick={onClose} style={btnOutline}>
              Cancel
            </button>
            <button type="submit" style={btnPrimary}>
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const overlayStyle: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.6)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 1000,
};

const modalStyle: React.CSSProperties = {
  background: "var(--color-bg-elevated, #1a1a1f)",
  color: "var(--color-text, #e6e6e6)",
  border: "1px solid rgba(255,255,255,0.15)",
  borderRadius: 12,
  padding: 24,
  maxWidth: 480,
  width: "90%",
};

const subtleText: React.CSSProperties = {
  color: "var(--color-text-muted, #9aa0a6)",
  fontSize: "0.9rem",
  marginTop: 0,
};

const inputStyle: React.CSSProperties = {
  background: "rgba(0,0,0,0.3)",
  border: "1px solid rgba(255,255,255,0.15)",
  color: "inherit",
  borderRadius: 6,
  padding: "8px 10px",
  fontFamily: "inherit",
};

const errorStyle: React.CSSProperties = {
  color: "#ff6b6b",
  fontSize: "0.9rem",
  margin: 0,
};

const btnOutline: React.CSSProperties = {
  background: "transparent",
  color: "inherit",
  border: "1px solid rgba(255,255,255,0.25)",
  borderRadius: 6,
  padding: "8px 14px",
  cursor: "pointer",
};

const btnPrimary: React.CSSProperties = {
  background: "#39d4e6",
  color: "#0a0a0a",
  border: "none",
  borderRadius: 6,
  padding: "8px 14px",
  cursor: "pointer",
  fontWeight: 600,
};
