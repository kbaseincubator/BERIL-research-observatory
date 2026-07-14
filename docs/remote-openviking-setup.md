# Remote OpenViking — New User Setup

The BERIL knowledge context layer (project reports + central docs, searchable
with `knowledge_query.py`) runs on a shared **remote OpenViking server**. This
is a one-time setup: you exchange your BERIL login for an OpenViking API key,
put it in `.env`, and then query freely — you don't need to run a local server.

> ⚠️ **The server currently runs on the dev host `https://beril-dev.kbase.us`.**
> This is temporary. When OpenViking moves to production, substitute the new
> base URL everywhere below (or pass `--server <url>` to the helper). Every
> example uses a single `SERVER=` line so there's exactly one place to change.

```bash
SERVER=https://beril-dev.kbase.us     # ← the only host-specific value
```

## Prerequisites

- The repo cloned, with `uv` installed.
- A `.env` file: `cp .env.example .env` if you don't have one.
- An ORCiD you can log in with.

## Step 1 — Log in

Open **`https://beril-dev.kbase.us`** in your browser and log in with your
ORCiD. Logging in sets a session cookie named **`beril_session`**.

## Step 2 — Copy your `beril_session` cookie

The server identifies you by that cookie. It's `HttpOnly` (not readable from
JavaScript), but you can copy it from your browser's dev tools:

- **Chrome/Edge:** DevTools (`F12` / `Cmd-Opt-I`) → **Application** tab →
  **Storage → Cookies → `https://beril-dev.kbase.us`** → click `beril_session`
  → copy its **Value**.
- **Firefox:** DevTools → **Storage** tab → **Cookies** → select the site →
  copy the `beril_session` value.

The value is a long opaque string — copy the whole thing.

## Step 3 — Get your API key

### Option A — helper script (recommended)

```bash
uv run knowledge/scripts/setup_remote_ov.py --cookie '<paste beril_session value>'
```

It creates your OpenViking account (idempotent), fetches your key, writes
`OPENVIKING_URL` and `OPENVIKING_API_KEY` into `.env`, and verifies the
connection. Useful flags:

- `--server "$SERVER"` — point at a different host (default is beril-dev).
- `--regenerate` — mint a fresh key, invalidating the old one (rotation, or the
  recovery path if you hit the 409 case below).
- `--print-only` — print the two env lines instead of writing `.env`.
- The cookie can also come from `$BERIL_SESSION` or an interactive prompt.

### Option B — manual (curl)

The key comes from **two** calls: create the account, then read the credential.

```bash
COOKIE='<paste beril_session value>'

# 1. Create your OpenViking account (idempotent — safe to re-run).
curl -X POST "$SERVER/api/ov/user" -H "Cookie: beril_session=$COOKIE"

# 2. Read your key (note: GET, not POST).
curl "$SERVER/api/ov/credentials" -H "Cookie: beril_session=$COOKIE" \
  | jq -r .user_key
```

> The key is **not** returned by `POST /api/ov/user` (that returns
> `{"created": true}`). You always retrieve it with **`GET /api/ov/credentials`**.

Then put both values in `.env` (note the `/ov` suffix on the URL):

```bash
OPENVIKING_URL=https://beril-dev.kbase.us/ov
OPENVIKING_API_KEY=<the user_key from step 2>
```

## Step 4 — Verify

```bash
# Reachability + auth check — tells server-down apart from a bad key.
uv run --env-file .env knowledge/scripts/knowledge_query.py doctor

# A real query.
uv run --env-file .env knowledge/scripts/knowledge_query.py find "metal resistance"
```

A healthy `doctor` prints `OpenViking: OK`. After this, you never need the cookie
again — queries talk directly to the server with your API key, which is
long-lived until you regenerate it.

## Recovery & rotation

- **Lost your key?** Re-run the helper (or `GET /api/ov/credentials`) — it
  returns the same stored key; nothing is invalidated.
- **Rotate / force a fresh key?** `setup_remote_ov.py --cookie '...' --regenerate`
  (this invalidates the old key everywhere it's in use).

## Troubleshooting

Run `knowledge_query.py doctor` first — its verdict tells you what's wrong:

| Verdict | Meaning | Fix |
|---|---|---|
| `OK` | Reachable, key valid | — |
| `UNREACHABLE` | Server down or wrong URL | Check `OPENVIKING_URL` ends in `/ov`; confirm `$SERVER/ov/health` responds in a browser; check network/VPN |
| `NO API KEY` | Reachable, but `OPENVIKING_API_KEY` unset | Run the setup helper (Step 3) |
| `AUTH FAILED` | Reachable, but your key was rejected | Key expired/invalid → `setup_remote_ov.py --regenerate` |
| `UNHEALTHY` | Reachable, but the server reports itself unhealthy | Server-side — flag a maintainer / check the OV deployment |
| `ERROR` | Reachable, but an authenticated call failed unexpectedly | Retry; if it persists, check the OV server logs |

Other cases:

- **`HTTP 401` from a curl/helper call** — your `beril_session` cookie is
  missing or expired. Log in again (Step 1) and re-copy it (Step 2).
- **`HTTP 409` on `POST /api/ov/user`** — OpenViking already has a user for your
  ORCiD but BERIL holds no key for it. Run `setup_remote_ov.py --regenerate` (or
  `POST /api/ov/user/regenerate` then `GET /api/ov/credentials`).
- **Quick server liveness, no auth needed:** `curl "$SERVER/ov/health"` should
  return `{"status":"ok","healthy":true,...}`.

## Security

`OPENVIKING_API_KEY` is a secret. `.env` and `*.env` are gitignored — keep the
key there, never commit it, and **never paste it into a chat**. If it leaks,
rotate it with `--regenerate`.

## See also

- `docs/openviking.md` — full query/ingest reference and local-server setup.
- The `knowledge-context` skill — how agents use the query toolkit.
