# Claude DevPod

A reproducible VS Code dev container running Red Hat UBI9 via Podman Desktop on Windows.

Pre-installed: Git, Node.js v20, Python 3 + uv, Podman, Claude Code.
Claude Code inherits your existing Windows session via a read-write bind mount of `~/.claude`.

## Prerequisites

1. **Podman Desktop** installed on Windows with a running WSL2-based Podman machine
   - Download: https://podman-desktop.io
   - After install, open Podman Desktop and start the default Podman machine

2. **VS Code** with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed

3. **Configure VS Code to use Podman** (one-time setup):
   - Open VS Code Settings (`Ctrl+,`)
   - Search for `dev.containers.dockerPath`
   - Set it to the path of your Podman executable, e.g.: `C:\Program Files\RedHat\Podman\podman.exe`

4. **An existing Claude Code session on Windows** — the container mounts your `%USERPROFILE%\.claude` directory directly, so no re-authentication is needed inside the container.

## Usage

### Open this repo as a dev container

1. Clone or open this repo in VS Code
2. When prompted "Reopen in Container", click it — or open the Command Palette (`Ctrl+Shift+P`) and run **Dev Containers: Reopen in Container**
3. VS Code builds the image and runs `postCreate.sh` (installs Claude Code, configures git and Podman)
4. Open a terminal inside the container and run `claude` to start

### Environment variables

A `.env.example` file at the repo root lists all available `DEVPOD_*` variables with their defaults.
On first devcontainer open VS Code automatically copies it to `.env` — no manual action required.

To customise (e.g., change the demo port or base image), edit `.env` before reopening the container.

> **Note:** `DEVPOD_BASE_IMAGE` is read from the **host shell environment** at build time (via `${localEnv:DEVPOD_BASE_IMAGE}` in devcontainer.json), not from `.env`. To override the base image, set `DEVPOD_BASE_IMAGE` in your shell before opening the devcontainer. All other `DEVPOD_*` variables are injected from `.env` at runtime.

| Variable | Default | Purpose |
|---|---|---|
| `DEVPOD_BASE_IMAGE` | `registry.access.redhat.com/ubi9/ubi:9.4` | Devcontainer base image (host env, build time) |
| `DEVPOD_PROJECT_NAME` | `claude-devpod` | Project name inside the container |
| `DEVPOD_PROJECT_PATH` | `/workspaces/claude-devpod` | Project path inside the container |
| `DEVPOD_DEMO_PORT` | `8080` | Host port forwarded to the demo-svc container |

### Opening the workspace

Open `claude-devpod.code-workspace` instead of the folder directly — this gives you a multi-folder
workspace with the parent repo and `demo-svc` as separate Explorer roots, plus pre-configured tasks.

**File → Open Workspace from File…** → select `claude-devpod.code-workspace`

To launch the demo service, use the VS Code task runner (`Ctrl+Shift+P` → **Tasks: Run Task**):

- **demo-svc: Run** — builds the image on first use (skips build if image exists), then starts the container
- **demo-svc: Rebuild & Run** — always rebuilds; use after changing `app.py`, templates, or the Dockerfile

The dashboard is available at `http://localhost:8080` (or the port set in `DEVPOD_DEMO_PORT`).

### Use as a template for another project

1. Copy the `.devcontainer/` folder into your project root
2. Open your project in VS Code and reopen in container

## Security

- `~/.claude` is bind-mounted at **runtime only** — it is never copied into the image or committed to git
- `.gitignore` explicitly blocks `.claude/` and `**/.claude/` from ever being staged
- The Dockerfile contains no secrets or hardcoded credentials
- The container runs with `--privileged` — required for Podman-in-Podman (nested container support via fuse-overlayfs); be aware of this when using the container in sensitive environments

## Verification

Inside the container terminal:

```bash
claude --version   # Claude Code is installed
podman info        # Podman-in-Podman is working
node --version     # Node.js v20
python3 --version  # Python 3
uv --version       # uv package manager
git --version      # Git
ls ~/.claude       # Windows session is mounted
```
