# demo-svc

A minimal Python/Flask web service that runs as a Podman container inside the
claude-devpod devcontainer, demonstrating container-in-container.

Open `http://localhost:8080` in your browser to see a live dark-mode dashboard
showing the service's runtime environment — auto-refreshing every 2 seconds.

VS Code automatically forwards port 8080 from the devcontainer to your Windows
host — check the **Ports** panel if the browser can't connect.

## Prerequisites

- claude-devpod devcontainer running (provides Podman)

## Build and run

From inside the devcontainer terminal:

```bash
cd container_in_container/demo
podman build -t demo-svc .
podman run --rm -p 8080:8080 demo-svc
```

Then open http://localhost:8080 in your browser on the Windows host.

To run on a different port:

```bash
podman run --rm -p 9090:9090 -e PORT=9090 demo-svc
```

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Live dashboard (browser) |
| `GET /api/status` | JSON runtime snapshot |
| `GET /health` | Liveness check — returns `{"status":"ok"}` |

## Run tests

From inside the devcontainer terminal:

```bash
cd container_in_container/demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python3 -m pytest tests/ -v
```

## Stop

`Ctrl+C` in the terminal running `podman run`, or:

```bash
podman stop $(podman ps -q --filter ancestor=demo-svc)
```
