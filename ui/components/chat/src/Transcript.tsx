// Scrollable list of messages. Auto-scrolls to the bottom on new content,
// but only when the user is already near the bottom — otherwise the user's
// scroll-up to review history isn't yanked away.

import { useEffect, useRef } from "react";
import { MessageView } from "./MessageView";
import type { TranscriptMessage } from "./types";

interface Props {
  messages: TranscriptMessage[];
}

export function Transcript({ messages }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pinnedToBottomRef = useRef(true);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const handler = () => {
      const slack = 64;
      pinnedToBottomRef.current =
        el.scrollHeight - el.scrollTop - el.clientHeight < slack;
    };
    el.addEventListener("scroll", handler);
    return () => el.removeEventListener("scroll", handler);
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    if (pinnedToBottomRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      ref={containerRef}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        overflowY: "auto",
        padding: "4px 4px 12px",
      }}
    >
      {messages.length === 0 ? (
        <p style={{ color: "var(--color-text-muted, #9aa0a6)" }}>
          No messages yet — send one below to start.
        </p>
      ) : (
        messages.map((m) => <MessageView key={m.id} message={m} />)
      )}
    </div>
  );
}
