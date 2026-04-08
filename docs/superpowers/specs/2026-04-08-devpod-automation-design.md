# DevPod Automation Design Spec

**Date:** 2026-04-08
**Status:** Approved
**Topic:** Demo repo tracking exception, environment variable management, VS Code workspace + tasks

---

## Overview

Three related improvements to the claude-devpod top-level repo:

1. **Repository tracking exception** — `container_in_container/demo/` is committed to the top-level repo so users have a runnable example out of the box.
2. **Environment variable management** — a `.env.example` template with `DEVPOD_*` prefixed variables, auto-copied to `.env` by `initializeCommand`, loaded into the devcontainer at runtime and build time.
3. **VS Code workspace + tasks** — a multi-folder `.code-workspace` file with two tasks (Run with lazy build, Rebuild & Run) so users can launch the demo without touching the terminal.

---

## 1. Repository Tracking Exception

### `.gitignore`

Replace the current blanket exclusion:

```gitignore
# Sub-projects — kept out of top-level repo entirely
container_in_container/
```

With a pattern that excludes sub-project directories by default but explicitly allows the demo:

```gitignore
# Sub-projects — kept out of top-level repo, except demo
container_in_container/*/
!container_in_container/demo/
```

`container_in_container/*/` excludes any directory inside `container_in_container/` — future sub-projects stay out automatically. The negation carves out `demo/` as the single tracked exception.

`.env` must also be explicitly listed in `.gitignore` (currently `.env.*` is excluded but not bare `.env`):

```gitignore
.env
```

### `CLAUDE.md`

The sub-projects section gains a note documenting the exception:

> `container_in_container/demo/` is the one permanently-tracked sub-project — committed to the top-level repo so users have a runnable example out of the box. All other sub-projects remain excluded.

---

## 2. Environment Variable Management

### `.env.example`

New file at repo root, committed to git:

```bash
# Devcontainer base image (passed as a build arg at container build time)
DEVPOD_BASE_IMAGE=registry.access.redhat.com/ubi9/ubi:9.4

# Project metadata (available inside the devcontainer at runtime)
DEVPOD_PROJECT_NAME=claude-devpod
DEVPOD_PROJECT_PATH=/workspaces/claude-devpod

# Port the demo-svc inner container listens on (forwarded to the Windows host)
DEVPOD_DEMO_PORT=8080
```

`.env` is never committed — excluded by `.gitignore`. Users who need custom values edit their local `.env` after it is auto-created.

### `devcontainer.json` Changes

Three additions:

**`initializeCommand`** — runs on the Windows host before the container starts; auto-copies `.env.example` → `.env` if `.env` doesn't exist. VS Code runs `initializeCommand` via `cmd.exe` on Windows, so use a cross-platform form via a small script rather than a bash one-liner:

```json
"initializeCommand": ".devcontainer/scripts/init-env.sh"
```

A new script `.devcontainer/scripts/init-env.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi
```

VS Code actually invokes `initializeCommand` through Git Bash / WSL when available on Windows, and falls back to the system shell. Using a script file is more reliable than an inline one-liner across shell environments.

**`runArgs`** — add `--env-file` alongside the existing `--privileged`:

```json
"runArgs": ["--privileged", "--env-file", ".env"]
```

**`build`** — switch from a bare `"dockerfile"` string to a `build` object that passes `DEVPOD_BASE_IMAGE` as a build arg. `${localEnv:DEVPOD_BASE_IMAGE}` reads from the host shell environment at build time (VS Code resolves this before launching the container build):

```json
"build": {
  "dockerfile": "Dockerfile",
  "args": {
    "BASE_IMAGE": "${localEnv:DEVPOD_BASE_IMAGE}"
  }
}
```

### `.devcontainer/Dockerfile` Change

Add `ARG` before `FROM` so the base image is configurable with a safe default:

```dockerfile
ARG BASE_IMAGE=registry.access.redhat.com/ubi9/ubi:9.4
FROM ${BASE_IMAGE}
```

---

## 3. VS Code Workspace + Tasks

### `claude-devpod.code-workspace`

New file at repo root, committed to git. Multi-folder workspace with two folders and two tasks inline:

```json
{
  "folders": [
    { "name": "claude-devpod", "path": "." },
    { "name": "demo-svc", "path": "container_in_container/demo" }
  ],
  "tasks": {
    "version": "2.0.0",
    "tasks": [
      {
        "label": "demo-svc: Run",
        "type": "shell",
        "command": "podman image exists demo-svc || podman build -t demo-svc ${workspaceFolder:claude-devpod}/container_in_container/demo && podman run --rm -p ${env:DEVPOD_DEMO_PORT}:8080 demo-svc",
        "group": "build",
        "presentation": {
          "reveal": "always",
          "panel": "dedicated"
        }
      },
      {
        "label": "demo-svc: Rebuild & Run",
        "type": "shell",
        "command": "podman build -t demo-svc ${workspaceFolder:claude-devpod}/container_in_container/demo && podman run --rm -p ${env:DEVPOD_DEMO_PORT}:8080 demo-svc",
        "group": "build",
        "presentation": {
          "reveal": "always",
          "panel": "dedicated"
        }
      }
    ]
  }
}
```

**Task behaviour:**

| Task | Build behaviour | Use when |
|---|---|---|
| `demo-svc: Run` | Builds only if image absent | First launch or normal use |
| `demo-svc: Rebuild & Run` | Always rebuilds | After changing app code or Dockerfile |

Both tasks run inside the devcontainer where `podman` is on PATH. VS Code's devcontainer integration forwards task execution automatically. Each task opens in a dedicated terminal panel so output is not mixed.

`${env:DEVPOD_DEMO_PORT}` resolves from the environment injected by `--env-file .env`, so the port is controlled by a single value in `.env`.

---

## Data Flow

```
Windows host
  ├── devcontainer.json initializeCommand
  │     └── cp .env.example .env  (first run only)
  ├── VS Code resolves ${localEnv:DEVPOD_BASE_IMAGE} → build arg
  └── devcontainer starts with --env-file .env
        └── DEVPOD_* vars available inside devcontainer
              ├── VS Code tasks use ${env:DEVPOD_DEMO_PORT}
              └── podman run -p DEVPOD_DEMO_PORT:8080 demo-svc
```

---

## Out of Scope

- Additional `DEVPOD_*` variables beyond the four defined above
- Validation of `.env` values at container startup
- Multiple inner container services or orchestration
- A VS Code launch configuration (tasks are sufficient for this workflow)
