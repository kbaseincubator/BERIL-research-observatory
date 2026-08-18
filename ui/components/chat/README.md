# BERIL Chat Component

Self-contained React/TypeScript chat UI for the BERIL Research Observatory.
Built with Vite, output as a single ES module to `ui/app/static/chat/chat.js`,
loaded by the Jinja session page.

## What it does

- Streams chat turns from the FastAPI backend over SSE (POST + `fetch` +
  `ReadableStream` — native `EventSource` can't POST).
- Renders transcript messages (SSR hydration + live-streamed).
- Persists user API keys in `localStorage`, never sends them for storage.
- Provider-agnostic — credential fields and models are driven by the
  backend's chat config (`ui/config/chat_providers.yaml`).

## Node / npm setup (macOS)

This project does not currently ship a Node toolchain, so you'll need one
locally. Any of these work — pick one:

### Option 1: Homebrew (simplest)

```bash
brew install node
node --version    # expect v20+ (Node 20 LTS or newer)
npm --version
```

### Option 2: `nvm` (if you juggle multiple Node versions)

```bash
# Install nvm itself
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# Restart your shell so nvm is on PATH, then:
nvm install --lts
nvm use --lts
```

### Option 3: `volta` (per-project pinning)

```bash
curl https://get.volta.sh | bash
volta install node@lts
```

### Minimum versions

- Node 20 or newer (Vite 6 requires it).
- npm 10 or newer (bundled with Node 20).

## Install deps & build

```bash
cd ui/components/chat
npm install             # one-time; also re-run after editing package.json
npm run build           # → writes ui/app/static/chat/chat.js
```

After the first build, the FastAPI app serves the component at
`/static/chat/chat.js`. The session page (`/chat/{session_id}`) picks it up
automatically on the next reload.

## Standalone dev preview (no FastAPI)

```bash
npm run dev
# open http://localhost:5173
```

This renders the component against a hardcoded fake provider catalog from
`index.html`. Useful for iterating on styles and layout. It does **not**
talk to the real backend — for that, build and reload the FastAPI page.

## Type-checking only

```bash
npm run typecheck
```

## Project structure

```
ui/components/chat/
  package.json
  tsconfig.json
  vite.config.ts
  index.html          # dev preview only
  src/
    main.tsx          # mount entry + window.BERILChat.mount
    App.tsx           # top-level state + turn lifecycle
    Transcript.tsx    # message list + autoscroll
    MessageView.tsx   # single message render
    InputBox.tsx      # textarea + send/stop
    CredentialsModal.tsx
    sseClient.ts      # POST + fetch + ReadableStream SSE reader
    credentialsStore.ts   # localStorage wrapper
    types.ts          # shared types (must match backend SSE frames)
```

## Backend contract

The component consumes the SSE frames emitted by
`ui/app/chat/sse.py:event_to_frame`. If you rename a field there, rename it
in `types.ts` — the TypeScript compiler won't catch that cross-boundary.
