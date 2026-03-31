# Claude DevPod Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a reproducible VS Code dev container configuration using Red Hat UBI9 on Windows with Podman Desktop, with Claude Code installed at startup and the Windows `~/.claude` session mounted read-write.

**Architecture:** A single `Dockerfile` layers tooling (system packages → Node.js v20 → Python + uv → Podman-in-Podman → vscode user) on `ubi9/ubi:latest`. `devcontainer.json` wires runtime config including the `~/.claude` bind mount and `--privileged` flag. `postCreate.sh` installs Claude Code fresh via the official install script on every container creation.

**Tech Stack:** Red Hat UBI9 (`registry.access.redhat.com/ubi9/ubi:latest`), Podman Desktop (WSL2), VS Code Dev Containers extension, Node.js v20 (NodeSource RPM), Python 3 + pip + uv, podman + fuse-overlayfs + slirp4netns, Claude Code (official `curl | bash` install script)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `.gitignore` | Create | Prevent credentials and secrets from being committed |
| `.devcontainer/Dockerfile` | Create | UBI9 image with all tooling layers |
| `.devcontainer/devcontainer.json` | Create | VS Code dev container config, mounts, extensions |
| `.devcontainer/scripts/postCreate.sh` | Create | Claude Code install + git + Podman storage setup |
| `README.md` | Create | Setup prerequisites and usage instructions |

---

## Task 1: Repo Scaffolding — `.gitignore`

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Create `.gitignore`**

```
# Claude credentials & session state — NEVER commit
.claude/
**/.claude/

# Environment / secrets
.env
.env.*
!.env.example

# Container artifacts
*.tar
*.oci

# OS / editor noise
.DS_Store
Thumbs.db
.vscode/settings.json
```

- [ ] **Step 2: Verify `.devcontainer/` is NOT listed in `.gitignore`**

Run: `grep devcontainer .gitignore`
Expected: no output (`.devcontainer/` must not be ignored — it is the purpose of this repo)

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore with credential and secret safeguards"
```

---

## Task 2: Dockerfile — Base Image + System Packages

**Files:**
- Create: `.devcontainer/Dockerfile`

- [ ] **Step 1: Create `.devcontainer/Dockerfile` with base image and system packages**

```dockerfile
FROM registry.access.redhat.com/ubi9/ubi:latest

# System packages
RUN dnf install -y \
    git \
    curl \
    wget \
    jq \
    vim \
    nano \
    tar \
    unzip \
    shadow-utils \
    sudo \
    procps-ng \
    && dnf clean all
```

- [ ] **Step 2: Build to verify the base layer**

Run: `podman build -f .devcontainer/Dockerfile -t claude-devpod:test .`
Expected: `Successfully tagged localhost/claude-devpod:test`

- [ ] **Step 3: Verify system packages are installed**

Run: `podman run --rm claude-devpod:test bash -c "git --version && curl --version | head -1 && jq --version"`
Expected output (versions may differ):
```
git version 2.43.5
curl 8.x.x ...
jq-1.6
```

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/Dockerfile
git commit -m "feat: add UBI9 Dockerfile base with system packages"
```

---

## Task 3: Dockerfile — Node.js v20

**Files:**
- Modify: `.devcontainer/Dockerfile`

- [ ] **Step 1: Append Node.js v20 layer to Dockerfile**

Add after the system packages `RUN` block:

```dockerfile
# Node.js v20 via NodeSource RPM
RUN curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - && \
    dnf install -y nodejs && \
    dnf clean all
```

- [ ] **Step 2: Build to verify**

Run: `podman build -f .devcontainer/Dockerfile -t claude-devpod:test .`
Expected: `Successfully tagged localhost/claude-devpod:test`

- [ ] **Step 3: Verify Node.js and npm are installed**

Run: `podman run --rm claude-devpod:test bash -c "node --version && npm --version"`
Expected output:
```
v20.x.x
10.x.x
```

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/Dockerfile
git commit -m "feat: add Node.js v20 layer via NodeSource"
```

---

## Task 4: Dockerfile — Python + uv

**Files:**
- Modify: `.devcontainer/Dockerfile`

- [ ] **Step 1: Append Python + uv layer to Dockerfile**

Add after the Node.js `RUN` block:

```dockerfile
# Python 3 + pip + uv
RUN dnf install -y python3 python3-pip && \
    dnf clean all && \
    pip3 install --no-cache-dir uv
```

- [ ] **Step 2: Build to verify**

Run: `podman build -f .devcontainer/Dockerfile -t claude-devpod:test .`
Expected: `Successfully tagged localhost/claude-devpod:test`

- [ ] **Step 3: Verify Python, pip, and uv are installed**

Run: `podman run --rm claude-devpod:test bash -c "python3 --version && pip3 --version && uv --version"`
Expected output:
```
Python 3.x.x
pip 21.x.x ...
uv 0.x.x
```

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/Dockerfile
git commit -m "feat: add Python 3 + pip + uv layer"
```

---

## Task 5: Dockerfile — Podman-in-Podman + `vscode` User

**Files:**
- Modify: `.devcontainer/Dockerfile`

- [ ] **Step 1: Append Podman + storage config + vscode user to Dockerfile**

Add after the Python `RUN` block:

```dockerfile
# Podman-in-Podman dependencies
RUN dnf install -y podman fuse-overlayfs slirp4netns && \
    dnf clean all

# System-level container storage config for fuse-overlayfs
RUN mkdir -p /etc/containers && \
    printf '[storage]\ndriver = "overlay"\n\n[storage.options.overlay]\nmount_program = "/usr/bin/fuse-overlayfs"\n' \
    > /etc/containers/storage.conf

# Create non-root vscode user with sudo and Podman subuid/subgid ranges
RUN useradd -m -s /bin/bash vscode && \
    usermod -aG wheel vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/vscode && \
    chmod 0440 /etc/sudoers.d/vscode && \
    echo "vscode:100000:65536" >> /etc/subuid && \
    echo "vscode:100000:65536" >> /etc/subgid

USER vscode
WORKDIR /home/vscode
```

- [ ] **Step 2: Build to verify**

Run: `podman build -f .devcontainer/Dockerfile -t claude-devpod:test .`
Expected: `Successfully tagged localhost/claude-devpod:test`

- [ ] **Step 3: Verify Podman is available and user is correct**

Run: `podman run --privileged --rm claude-devpod:test bash -c "whoami && podman --version && cat /etc/containers/storage.conf"`
Expected output:
```
vscode
podman version 4.x.x
[storage]
driver = "overlay"

[storage.options.overlay]
mount_program = "/usr/bin/fuse-overlayfs"
```

- [ ] **Step 4: Verify subuid/subgid entries exist**

Run: `podman run --rm claude-devpod:test bash -c "grep vscode /etc/subuid && grep vscode /etc/subgid"`
Expected output:
```
vscode:100000:65536
vscode:100000:65536
```

- [ ] **Step 5: Commit**

```bash
git add .devcontainer/Dockerfile
git commit -m "feat: add Podman-in-Podman layer and vscode user"
```

---

## Task 6: `postCreate.sh`

**Files:**
- Create: `.devcontainer/scripts/postCreate.sh`

- [ ] **Step 1: Create scripts directory and `postCreate.sh`**

```bash
mkdir -p .devcontainer/scripts
```

Create `.devcontainer/scripts/postCreate.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Claude DevPod: Post-create setup ==="

# Step 1: Install Claude Code via official install script
echo "--- [1/4] Installing Claude Code..."
curl -fsSL https://claude.ai/install.sh | bash

# Step 2: Verify Claude Code installed successfully
echo "--- [2/4] Verifying Claude Code..."
claude --version

# Step 3: Configure git safe.directory (required for bind-mounted Windows paths)
echo "--- [3/4] Configuring git safe.directory..."
git config --global --add safe.directory '*'

# Step 4: Configure user-level Podman storage (skip if already configured)
echo "--- [4/4] Configuring Podman user storage..."
if [ ! -f "${HOME}/.config/containers/storage.conf" ]; then
    mkdir -p "${HOME}/.config/containers"
    cat > "${HOME}/.config/containers/storage.conf" << 'EOF'
[storage]
driver = "overlay"

[storage.options.overlay]
mount_program = "/usr/bin/fuse-overlayfs"
EOF
    echo "    Podman user storage configured."
else
    echo "    Podman user storage already configured, skipping."
fi

echo ""
echo "=== Claude DevPod ready! ==="
echo "  claude: $(claude --version)"
echo "  node:   $(node --version)"
echo "  python: $(python3 --version)"
echo "  podman: $(podman --version)"
echo "  git:    $(git --version)"
```

- [ ] **Step 2: Make the script executable**

```bash
chmod +x .devcontainer/scripts/postCreate.sh
```

- [ ] **Step 3: Verify the script has no syntax errors**

Run: `bash -n .devcontainer/scripts/postCreate.sh`
Expected: no output (exit code 0)

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/scripts/postCreate.sh
git commit -m "feat: add postCreate.sh — Claude Code install and environment setup"
```

---

## Task 7: `devcontainer.json`

**Files:**
- Create: `.devcontainer/devcontainer.json`

- [ ] **Step 1: Create `.devcontainer/devcontainer.json`**

```json
{
  "name": "Claude DevPod (UBI9)",
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".."
  },
  "runArgs": [
    "--privileged"
  ],
  "mounts": [
    "source=${localEnv:USERPROFILE}/.claude,target=/home/vscode/.claude,type=bind,consistency=cached"
  ],
  "remoteUser": "vscode",
  "postCreateCommand": "bash .devcontainer/scripts/postCreate.sh",
  "customizations": {
    "vscode": {
      "extensions": [
        "timonwong.shellcheck",
        "redhat.vscode-yaml",
        "ms-azuretools.vscode-docker",
        "ms-python.python",
        "dbaeumer.vscode-eslint"
      ]
    }
  }
}
```

> **Security note:** The `mounts` entry bind-mounts `%USERPROFILE%\.claude` from Windows into the container. This directory contains auth credentials. It must never be committed. It is protected by `.gitignore`.

> **Path separator note:** `${localEnv:USERPROFILE}` resolves to `C:\Users\<name>` on Windows. VS Code Dev Containers normalizes path separators when passing the mount to Podman. If the container fails to start with a mount error, try replacing `/.claude` with `\.claude` in the source path and rebuild.

- [ ] **Step 2: Validate JSON is well-formed**

Run: `python3 -c "import json; json.load(open('.devcontainer/devcontainer.json')); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add .devcontainer/devcontainer.json
git commit -m "feat: add devcontainer.json with Podman mounts and extensions"
```

---

## Task 8: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with prerequisites and usage instructions"
```

---

## Task 9: End-to-End Smoke Test

This task is a manual verification checklist. No code changes.

- [ ] **Step 1: Open repo in VS Code**

In VS Code: `File > Open Folder` → select the `claude-devpod` repo root.

- [ ] **Step 2: Reopen in Container**

Command Palette (`Ctrl+Shift+P`) → `Dev Containers: Reopen in Container`

Watch the build log in the VS Code terminal panel. Expected: no errors during image build or postCreate.sh execution.

- [ ] **Step 3: Run verification commands in the container terminal**

```bash
claude --version
```
Expected: prints Claude Code version string

```bash
podman info
```
Expected: prints Podman system info (no errors)

```bash
node --version && python3 --version && uv --version && git --version
```
Expected: all four print version strings

```bash
ls ~/.claude
```
Expected: lists files from your Windows `%USERPROFILE%\.claude` directory (e.g., `settings.json`, `CLAUDE.md`, `projects/`)

- [ ] **Step 4: Verify Podman-in-Podman actually works**

```bash
podman pull hello-world
podman run --rm hello-world
```
Expected: `Hello from Docker!` (or similar Podman hello-world output)

- [ ] **Step 5: Verify Claude Code can authenticate**

```bash
claude --version
```
Expected: no auth prompts — should just work because `~/.claude` is mounted from Windows with your existing session.

- [ ] **Step 6: Tag the verified image (optional)**

If all checks pass, the setup is complete. The image can be rebuilt anytime with:

```bash
# From VS Code Command Palette:
Dev Containers: Rebuild Container
```
