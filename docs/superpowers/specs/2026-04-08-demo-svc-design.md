# demo-svc Design Spec

**Date:** 2026-04-08
**Status:** Approved
**Topic:** Container-in-container demo — live Python dashboard

---

## Overview

A minimal Python web service that runs as a Podman container *inside* the claude-devpod devcontainer, demonstrating the container-in-container capability. It serves a dark-mode browser dashboard showing live runtime information about itself and its hosting environment, auto-refreshing every 2 seconds via JSON polling.

---

## Repository Structure

This sub-project lives at `container_in_container/demo/` within the top-level repo and is managed as its own standalone git repository.

```
container_in_container/demo/
├── app.py                  # Flask application — routes, request logging, status collection
├── templates/
│   └── index.html          # Dashboard page — HTML, inline CSS, inline JS polling loop
├── Dockerfile              # Inner container image (UBI9 + Python + Flask)
├── requirements.txt        # flask (only dependency)
└── README.md               # Build and run instructions
```

---

## Architecture

### Server (app.py)

Flask application with three routes:

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the dashboard HTML page |
| `/api/status` | GET | Returns JSON snapshot of runtime info |
| `/health` | GET | Returns `{"status":"ok"}` — liveness check |

A Flask `after_request` hook records each request (method, path, status code, duration in ms) into an in-memory circular buffer capped at 20 entries. This feeds the request log panel on the dashboard.

The app records its start time at startup. Uptime is calculated as `now - start_time` on each `/api/status` call.

### `/api/status` Response Shape

```json
{
  "hostname": "a3f9d12c",
  "python_version": "3.11.9",
  "flask_version": "3.0.3",
  "podman_version": "5.3.1",
  "os": "Red Hat Enterprise Linux 9.4",
  "port": 8080,
  "uptime_seconds": 724,
  "recent_requests": [
    { "method": "GET", "path": "/", "status": 200, "duration_ms": 2 }
  ]
}
```

- `podman_version`: obtained by shelling out to `podman --version` at startup and caching the result. If Podman is unavailable, returns `"unavailable"`.
- `os`: read from `/etc/os-release` (`PRETTY_NAME` field).
- `recent_requests`: last 20 entries, newest first.

### Dashboard (index.html)

Single self-contained HTML file — no build step, no CDN dependencies, no JavaScript framework.

**Layout sections (top to bottom):**
1. **Header** — service name (`demo-svc`), monospace path (`container_in_container/demo`), animated green "Running" status pill
2. **Runtime panel** (red accent) — Python version, Flask version, listening address; badge-style version chips
3. **Host panel** (muted) — hostname, OS, Podman version
4. **Uptime + nesting breadcrumb row** — uptime in teal monospace; breadcrumb: `devcontainer › podman run › demo-svc`
5. **Request log** — last 10 requests shown, method / path / status / duration, newest at top

**Live update behaviour:**
- On page load: immediately fetch `/api/status` and render all panels
- `setInterval` at 2000ms: re-fetch and update changed DOM nodes (no full re-render, no flicker)
- On fetch failure: status pill switches to amber "Reconnecting…" and retries on next interval

**Visual design:**
- Background: `linear-gradient(160deg, #1a1a2e, #16213e, #0f3460)`
- Accent (Runtime panel, version badges): `#e94560`
- Status / uptime: `#34d399`
- Muted text / Host panel: `#a8b2d8`
- Panel backgrounds: `rgba(255,255,255,0.04)` with `1px` borders
- Font: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` — no external font dependency
- Monospace values: system monospace stack

---

## Container Setup

### Dockerfile

```dockerfile
FROM registry.access.redhat.com/ubi9/ubi:latest
RUN dnf install -y python3 python3-pip && dnf clean all
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python3", "app.py"]
```

Uses the same UBI9 base as the outer devcontainer for consistency. Only adds Python, pip, and Flask.

### Build and Run

From inside the devcontainer:

```bash
cd container_in_container/demo
podman build -t demo-svc .
podman run --rm -p 8080:8080 demo-svc
```

Open `http://localhost:8080` in the browser on the Windows host. VS Code / Podman Desktop forwards the port automatically through the container layers.

---

## Data Flow

```
Windows host browser
  └── http://localhost:8080
        └── Port-forwarded through devcontainer
              └── Inner container (demo-svc, Podman)
                    ├── GET /          → index.html (dashboard)
                    └── GET /api/status → JSON (polled every 2s)
```

The `podman_version` field in `/api/status` is obtained by shelling out to `podman --version` from inside the inner container. This works because the devcontainer runs `--privileged` and Podman is on the PATH, and explicitly demonstrates the container-in-container capability on the dashboard itself.

---

## Error Handling

- `podman --version` shell-out wrapped in try/except; returns `"unavailable"` on failure without crashing the app
- `/etc/os-release` read wrapped in try/except; returns `"unknown"` on failure
- Flask runs with `debug=False` in the container; errors return JSON `{"error": "..."}` with appropriate HTTP status
- Frontend fetch errors: status pill turns amber, retries on next interval tick — no user-visible crash

---

## Security

- Flask binds to `0.0.0.0:8080` inside the container; exposure is controlled at `podman run -p` time
- No secrets, credentials, or environment variables required
- No user input accepted — all endpoints are read-only GET requests
- `debug=False` ensures the Werkzeug debugger is never exposed

---

## Out of Scope

- Authentication / access control
- Persistent request log (in-memory only, cleared on container restart)
- Metrics history / charting
- Multiple service instances
- Docker Compose or multi-container orchestration
