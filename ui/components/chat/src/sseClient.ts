// SSE consumer for chat turns.
//
// Native EventSource can't POST (needed to send the user's message + creds
// in the body), so we do the framing by hand over a fetch-returned
// ReadableStream. The format is the standard one (RFC: event:/data:\n\n).
//
// The caller registers handlers per `event:` kind. The returned AbortController
// lets the caller cancel mid-stream (e.g. if the user clicks "stop").

import type { SSEFrame } from "./types";

export interface SSEHandlers {
  onFrame: (frame: SSEFrame) => void;
  onHttpError?: (status: number, body: string) => void;
  onNetworkError?: (err: unknown) => void;
  onDone?: () => void;
}

export interface SSEOptions {
  url: string;
  body: unknown;
  signal?: AbortSignal;
}

export async function streamTurn(
  opts: SSEOptions,
  handlers: SSEHandlers,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(opts.url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(opts.body),
      signal: opts.signal,
    });
  } catch (err) {
    handlers.onNetworkError?.(err);
    return;
  }

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    handlers.onHttpError?.(response.status, text);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    handlers.onNetworkError?.(new Error("response has no body"));
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    // Each iteration reads a chunk, appends to the buffer, and drains any
    // complete frames (separated by \n\n, per SSE spec).
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE frames end with a blank line. sse-starlette emits CRLF
      // (\r\n\r\n) separators; other servers use \n\n. Normalize before
      // splitting so we don't miss frames.
      buffer = buffer.replace(/\r\n/g, "\n");

      let sep: number;
      while ((sep = buffer.indexOf("\n\n")) >= 0) {
        const rawFrame = buffer.slice(0, sep);
        buffer = buffer.slice(sep + 2);
        const parsed = parseFrame(rawFrame);
        if (parsed) handlers.onFrame(parsed);
      }
    }
    // Flush any trailing frame that didn't end with \n\n.
    const tail = buffer.trim();
    if (tail) {
      const parsed = parseFrame(tail);
      if (parsed) handlers.onFrame(parsed);
    }
  } catch (err) {
    if ((err as Error)?.name !== "AbortError") {
      handlers.onNetworkError?.(err);
    }
  } finally {
    handlers.onDone?.();
  }
}

function parseFrame(raw: string): SSEFrame | null {
  let event: string | null = null;
  const dataLines: string[] = [];
  for (const line of raw.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
    // Ignore other fields (id:, retry:, comments starting with `:`).
  }
  if (!event || dataLines.length === 0) return null;
  try {
    const data = JSON.parse(dataLines.join("\n"));
    return { event, data } as SSEFrame;
  } catch {
    return null;
  }
}
