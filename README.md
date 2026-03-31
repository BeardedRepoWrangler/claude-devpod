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

### Use as a template for another project

1. Copy the `.devcontainer/` folder into your project root
2. Open your project in VS Code and reopen in container

## Security

- `~/.claude` is bind-mounted at **runtime only** — it is never copied into the image or committed to git
- `.gitignore` explicitly blocks `.claude/` and `**/.claude/` from ever being staged
- The Dockerfile contains no secrets or hardcoded credentials

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
