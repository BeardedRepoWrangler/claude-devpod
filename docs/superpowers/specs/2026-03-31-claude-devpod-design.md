# Claude DevPod Design Spec

**Date:** 2026-03-31
**Status:** Approved
**Topic:** Reproducible VS Code Dev Container on UBI9 with Podman + Claude Code

---

## Overview

A standalone `.devcontainer` configuration that provides a reproducible Red Hat UBI 9 development environment on Windows using Podman Desktop. The container has Claude Code pre-installed (at startup) and inherits the user's existing Windows Claude session via a read-write bind mount of `~/.claude`. The setup supports both Windows-hosted and container-hosted project files.

---

## Architecture

### Repository Structure

```
claude-devpod/
├── .devcontainer/
│   ├── devcontainer.json       # VS Code dev container configuration
│   ├── Dockerfile              # UBI9 image with all tooling
│   └── scripts/
│       └── postCreate.sh       # Claude Code install + post-create setup
├── docs/
│   └── superpowers/specs/
│       └── 2026-03-31-claude-devpod-design.md
├── .gitignore
└── README.md
```

### Approach

Single custom `Dockerfile` based on `ubi9/ubi:latest` with all tooling baked in at build time. `devcontainer.json` wires the mount, runtime args, and post-create hook. Claude Code is installed fresh at container creation via the official install script (not baked into the image, so it always gets the latest version).

---

## Components

### Base Image

```
registry.access.redhat.com/ubi9/ubi:latest
```

Always tracks the latest UBI 9 release (RHEL 9 compatible). Uses `dnf` for package management.

### Dockerfile Layers

Build steps in order:

1. **System packages** via `dnf`:
   `git`, `curl`, `wget`, `jq`, `vim`, `nano`, `bash`, `tar`, `unzip`, `shadow-utils`, `sudo`

2. **Node.js LTS** via NodeSource RPM repository (v20):
   Provides `node` and `npm`.

3. **Python** via UBI 9 packages + pip + `uv`:
   `python3`, `python3-pip`, then `uv` via pip.

4. **Podman-in-Podman**:
   Install `podman`, `fuse-overlayfs`, `slirp4netns`.
   Configure `/etc/containers/storage.conf` for overlay + fuse-overlayfs.
   Set `/etc/subuid` and `/etc/subgid` entries for the `vscode` user.

5. **Non-root `vscode` user**:
   Created to match VS Code Dev Container conventions.
   Added to `wheel` group for sudo access.
   Set as the default container user.

### `devcontainer.json`

Key settings:

| Setting | Value |
|---|---|
| `build.dockerfile` | `Dockerfile` |
| `runArgs` | `["--privileged"]` |
| `remoteUser` | `vscode` |
| `postCreateCommand` | `bash .devcontainer/scripts/postCreate.sh` |
| `~/.claude` mount | `source=${localEnv:USERPROFILE}\.claude,target=/home/vscode/.claude,type=bind,consistency=cached` |

**Why `--privileged`:** Required for rootless Podman-in-Podman with fuse-overlayfs. The outer container runs privileged within the Podman WSL2 VM, not on bare Windows metal.

**Why `${localEnv:USERPROFILE}`:** Resolves to the Windows user home directory (e.g., `C:\Users\micha`) at runtime without hardcoding any user-specific path in the repo. Note: the mount `source` path must use forward slashes or escaped backslashes — verify separator behavior during implementation with Podman Desktop on Windows.

VS Code extensions included:

| Extension | Purpose |
|---|---|
| `timonwong.shellcheck` | Shell script linting |
| `redhat.vscode-yaml` | YAML/JSON schema validation |
| `ms-azuretools.vscode-docker` | Container/image browser (Podman-compatible) |
| `ms-python.python` | Python IntelliSense and debugging |
| `dbaeumer.vscode-eslint` | ESLint for Node/JS |

### `postCreate.sh`

Runs once after container creation as the `vscode` user. Steps:

1. Install Claude Code via official install script:
   `curl -fsSL https://claude.ai/install.sh | bash`
2. Verify install: `claude --version`
3. Configure git safe.directory: `git config --global --add safe.directory '*'`
4. Configure Podman storage if `~/.config/containers/storage.conf` does not already exist
5. Print a welcome message confirming readiness

**Error handling:** `set -euo pipefail` — any unhandled error exits immediately with a descriptive message indicating which step failed.

**Idempotency:**
- Claude Code install script is safe to re-run (upstream handles it)
- `git config --add` is additive and safe to repeat
- Podman storage config is only written if the file does not already exist

---

## Data Flow

```
Windows Host
  └── Podman Desktop (WSL2 VM)
        └── Dev Container (UBI9, --privileged)
              ├── /home/vscode/.claude  ←→  %USERPROFILE%\.claude (bind mount, rw)
              ├── /workspaces/<project> ←→  Windows project dir (optional bind mount)
              └── Claude Code reads ~/.claude for session auth on first run
```

---

## Security Safeguards

- `devcontainer.json` uses `${localEnv:USERPROFILE}` — no hardcoded user paths in the repo
- `postCreate.sh` does not reference, echo, or log any credential paths
- The Dockerfile contains no secrets, tokens, or hardcoded usernames
- `~/.claude` is bind-mounted at runtime only — never copied into the image
- A warning comment in `devcontainer.json` notes that `~/.claude` contains auth credentials and must never be committed

---

## `.gitignore`

```gitignore
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

Note: `.devcontainer/` is intentionally tracked — it is the purpose of this repo.

---

## Error Handling

- Container build failures surface via Docker/Podman build output in VS Code
- `postCreate.sh` uses `set -euo pipefail`; VS Code surfaces script failures in the dev container creation log
- If `claude --version` fails post-install, the script exits non-zero and the user sees a clear failure in the creation log

---

## Testing / Verification

To verify the setup works:

1. Open repo in VS Code → "Reopen in Container"
2. Confirm container builds without errors
3. Inside container terminal: `claude --version` — should print installed version
4. Inside container terminal: `podman info` — should succeed
5. Confirm `~/.claude` is accessible: `ls ~/.claude`
6. Confirm Node, Python, uv, git are all on PATH

---

## Out of Scope

- Language-specific toolchains beyond Node.js and Python (Go, Rust, Java, .NET)
- Sidecar services (databases, message queues) — can be added via Compose later
- CI/CD pipeline configuration
- Podman machine setup on Windows (assumed: Podman Desktop with WSL2 already configured)
