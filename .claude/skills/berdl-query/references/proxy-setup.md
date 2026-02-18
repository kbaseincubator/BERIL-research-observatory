# BERDL Proxy Setup

BERDL services (Spark Connect, MinIO) are not directly reachable from external networks.
All local access requires an SSH SOCKS tunnel and an HTTP proxy bridge.

## Architecture

```
Local machine                  LBNL bastion                  BERDL cluster
─────────────                  ────────────                  ─────────────
pproxy :8123 ──► SOCKS5 :1338 ──► ssh tunnel ──► metrics.berdl.kbase.us
                                                  minio.berdl.kbase.us
                                                  spark.berdl.kbase.us
```

## Step 1: SSH SOCKS Tunnels

Open two SOCKS5 tunnels to the LBNL bastion. These require your LBNL credentials (password or SSH key).

```bash
ssh -f -N -o ServerAliveInterval=60 -D 1338 ac.<username>@login1.berkeley.kbase.us
ssh -f -N -o ServerAliveInterval=60 -D 1337 ac.<username>@login1.berkeley.kbase.us
```

- `-f -N`: fork to background, no remote command
- `-D 1338`/`-D 1337`: SOCKS5 proxy on localhost
- `-o ServerAliveInterval=60`: keeps the tunnel alive during idle periods

**This step requires user interaction** (authentication). Claude cannot run these commands.

### Verifying tunnels are up

```bash
lsof -i :1337 -i :1338 | grep LISTEN
```

Both ports should show `ssh` processes listening.

### If a tunnel dies

Tunnels can drop due to network changes or idle timeouts. Re-run the `ssh` command for the dead port. The "Address already in use" error means that tunnel is still running.

## Step 2: HTTP Proxy Bridge (pproxy)

The `--berdl-proxy` flag on BERDL scripts sets `grpc_proxy` and `https_proxy` to `http://127.0.0.1:8123`. This requires an HTTP proxy that forwards to the SOCKS5 tunnel.

`pproxy` is installed in `.venv-berdl` and bridges HTTP ↔ SOCKS5:

```bash
source .venv-berdl/bin/activate
python -c "
import sys, asyncio
sys.argv = ['pproxy', '-l', 'http://:8123', '-r', 'socks5://127.0.0.1:1338', '-v']
asyncio.set_event_loop(asyncio.new_event_loop())
from pproxy.server import main
main()
"
```

This runs in the foreground. Use a separate terminal, or Claude can run it as a background process.

### Verifying the proxy is up

```bash
lsof -i :8123 | grep LISTEN
```

Should show a Python process listening.

## Step 3: Use `--berdl-proxy`

Once the SSH tunnels and pproxy are running, all BERDL scripts work with `--berdl-proxy`:

```bash
python scripts/run_sql.py --berdl-proxy --query "SHOW DATABASES"
python scripts/export_sql.py --berdl-proxy --query "SELECT ..." --path "s3a://..."
bash scripts/configure_mc.sh --berdl-proxy
```

For `mc` commands after alias setup, set the proxy in your shell:

```bash
export https_proxy=http://127.0.0.1:8123
export no_proxy=localhost,127.0.0.1
mc ls berdl-minio/cdm-lake/...
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `connection refused` on :8123 | pproxy not running | Start pproxy (step 2) |
| `Connect call failed ('127.0.0.1', 1338)` in pproxy output | SSH tunnel on 1338 is dead | Re-run SSH command for port 1338 |
| `Request to authentication service timed out` | SSH tunnel died mid-query | Check tunnels, restart dead ones, retry |
| `i/o timeout` on `spark.berdl.kbase.us:443` | Using direct mode instead of proxy | Add `--berdl-proxy` flag |
| `Address already in use` on SSH `-D` port | Tunnel already running on that port | That tunnel is fine, check the other one |

## Prerequisites Checklist

- [ ] LBNL account with SSH access to `login1.berkeley.kbase.us`
- [ ] `KBASE_AUTH_TOKEN` in `.env`
- [ ] `.venv-berdl` created via `scripts/bootstrap_client.sh`
- [ ] JupyterHub session active (log in at `https://hub.berdl.kbase.us`, open a notebook)
- [ ] SSH tunnels running on ports 1337 and 1338
- [ ] pproxy running on port 8123
