// Public entry point. The build produces a single ES module at
// `ui/app/static/chat/chat.js`; the Jinja session template loads it and
// calls `mountChat(rootEl, props)`.

import { createRoot } from "react-dom/client";
import { ChatApp, type ChatAppProps } from "./App";

// StrictMode deliberately double-invokes effects and (in dev) can double-
// render component trees to surface side-effect bugs. Our turn lifecycle
// (send message → open SSE stream → mutate an `activity: ToolActivity[]`
// closure) is not idempotent, so StrictMode causes duplicate in-flight
// turns that then compete for the same state slot. We skip it entirely
// for now; if we later make startTurn purely functional we can restore
// StrictMode safely.
export function mountChat(
  root: HTMLElement,
  props: ChatAppProps,
): { unmount: () => void } {
  const reactRoot = createRoot(root);
  reactRoot.render(<ChatApp {...props} />);
  return {
    unmount: () => reactRoot.unmount(),
  };
}

// Expose globally so a plain <script type="module"> in Jinja can call it
// without a separate bootstrap script. Consumers that prefer a tree-shakeable
// import path can use the named export directly.
declare global {
  interface Window {
    BERILChat?: {
      mount: typeof mountChat;
    };
  }
}

if (typeof window !== "undefined") {
  window.BERILChat = { mount: mountChat };
}

export type { ChatAppProps };
export { ChatApp };
