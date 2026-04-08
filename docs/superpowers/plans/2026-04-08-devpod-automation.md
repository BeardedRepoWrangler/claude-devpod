# DevPod Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Track the demo sub-project in the top-level repo, manage devcontainer configuration via `DEVPOD_*` environment variables, and add a VS Code multi-folder workspace with lazy-build Run and Rebuild & Run tasks.

**Architecture:** Configuration-only changes — no new application logic. Files are created or edited across `.gitignore`, `CLAUDE.md`, `.devcontainer/`, and repo root. Changes are independent and can be committed task-by-task.

**Tech Stack:** bash, JSON (devcontainer.json, .code-workspace), Dockerfile ARG, git

---

## File Map

| Action | File | Purpose |
|--------|------|---------|
| Modify | `.gitignore` | Replace blanket `container_in_container/` exclusion with per-dir pattern + demo exception |
| Modify | `CLAUDE.md` | Document demo tracking exception in Repository Structure section |
| Create | `.env.example` | Template with `DEVPOD_*` vars; committed to git |
| Create | `.devcontainer/scripts/init-env.sh` | Auto-copies `.env.example` → `.env` on first devcontainer open |
| Modify | `.devcontainer/devcontainer.json` | Add `initializeCommand`, `--env-file`, and `build.args` |
| Modify | `.devcontainer/Dockerfile` | Add `ARG BASE_IMAGE` before `FROM`; pin tag to `9.4` |
| Create | `claude-devpod.code-workspace` | Multi-folder workspace with Run + Rebuild & Run tasks |

---

## Task 1: Fix .gitignore to track demo

**Files:**
- Modify: `.gitignore`

The current rule `container_in_container/` excludes the entire directory. Replace it with a per-directory glob and a negation for the demo.

- [ ] **Step 1: Open `.gitignore` and locate the sub-projects section**

Find this block (around line 21):
```
# Sub-projects — kept out of top-level repo entirely
container_in_container/
```

- [ ] **Step 2: Replace the sub-projects block**

Replace it with:
```gitignore
# Sub-projects — kept out of top-level repo, except demo
container_in_container/*/
!container_in_container/demo/
```

`container_in_container/*/` matches any immediate subdirectory (future sub-projects). The negation then carves out `demo/` as the single tracked exception. Git processes negations in order, so this is correct.

- [ ] **Step 3: Verify demo is now tracked**

```bash
git check-ignore -v container_in_container/demo/app.py
```

Expected: **no output** (file is not ignored).

```bash
git check-ignore -v container_in_container/other-project/file.txt
```

Expected: `.gitignore:21:container_in_container/*/   container_in_container/other-project/file.txt` (ignored).

- [ ] **Step 4: Verify demo files appear in git status**

```bash
git status --short
```

Expected: `container_in_container/demo/` files appear as untracked (ready to stage). They should NOT appear as ignored.

- [ ] **Step 5: Commit**

```bash
git add .gitignore
git commit -m "chore: un-ignore container_in_container/demo in .gitignore"
```

---

## Task 2: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Open `CLAUDE.md` and locate the Repository Structure section**

Find these two lines in the Repository Structure section:
```
- **Sub-projects** go in `container_in_container/<sub-project>/`. Each sub-project is a standalone git repo managed independently.
- Sub-project names and details must **never** be committed to the top-level repo.
```

- [ ] **Step 2: Update the second bullet to document the exception**

Replace the two bullets with:
```markdown
- **Sub-projects** go in `container_in_container/<sub-project>/`. Each sub-project is a standalone git repo managed independently.
- Sub-project names and details must **never** be committed to the top-level repo, with one exception: `container_in_container/demo/` is permanently tracked so users have a runnable example out of the box.
```

- [ ] **Step 3: Verify the file looks correct**

```bash
grep -A3 "Sub-projects" CLAUDE.md
```

Expected output includes both bullet points with the exception clause.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: document container_in_container/demo tracking exception in CLAUDE.md"
```

---

## Task 3: Create .env.example

**Files:**
- Create: `.env.example`

`.env.example` is already negated in `.gitignore` (the line `!.env.example` is present), so it will be tracked by git automatically.

- [ ] **Step 1: Create `.env.example` at the repo root**

```bash
# .env.example
# Copy this file to .env and customise as needed.
# .env is never committed — it is auto-created by initializeCommand on first devcontainer open.

# Devcontainer base image (passed as a build arg at container build time)
DEVPOD_BASE_IMAGE=registry.access.redhat.com/ubi9/ubi:9.4

# Project metadata (available inside the devcontainer at runtime)
DEVPOD_PROJECT_NAME=claude-devpod
DEVPOD_PROJECT_PATH=/workspaces/claude-devpod

# Port the demo-svc inner container listens on (forwarded to the Windows host)
DEVPOD_DEMO_PORT=8080
```

- [ ] **Step 2: Verify git tracks it and .env is still excluded**

```bash
git check-ignore -v .env.example
```

Expected: **no output** (not ignored — will be tracked).

```bash
git check-ignore -v .env
```

Expected: `.gitignore:4:.env   .env` (ignored).

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "chore: add .env.example with DEVPOD_* variable template"
```

---

## Task 4: Create init-env.sh

**Files:**
- Create: `.devcontainer/scripts/init-env.sh`

This script is run by `initializeCommand` on the Windows host before the devcontainer starts. It auto-copies `.env.example` to `.env` on first use.

- [ ] **Step 1: Create the script**

```bash
#!/usr/bin/env bash
set -euo pipefail
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi
```

Save to `.devcontainer/scripts/init-env.sh`.

- [ ] **Step 2: Make it executable**

```bash
chmod +x .devcontainer/scripts/init-env.sh
```

- [ ] **Step 3: Verify bash syntax**

```bash
bash -n .devcontainer/scripts/init-env.sh
```

Expected: no output (syntax is valid).

- [ ] **Step 4: Verify behaviour — creates .env when absent**

```bash
# Run from repo root in a temp location to avoid overwriting your real .env
tmpdir=$(mktemp -d)
cp .env.example "$tmpdir/.env.example"
cp .devcontainer/scripts/init-env.sh "$tmpdir/init-env.sh"
chmod +x "$tmpdir/init-env.sh"
(cd "$tmpdir" && bash init-env.sh)
```

Expected output: `Created .env from .env.example`

```bash
diff "$tmpdir/.env" "$tmpdir/.env.example"
```

Expected: no diff (files are identical).

- [ ] **Step 5: Verify behaviour — does NOT overwrite existing .env**

```bash
echo "CUSTOM=1" > "$tmpdir/.env"
(cd "$tmpdir" && bash init-env.sh)
cat "$tmpdir/.env"
```

Expected: only `CUSTOM=1` — script printed nothing and did not overwrite.

```bash
rm -rf "$tmpdir"
```

- [ ] **Step 6: Commit**

```bash
git add .devcontainer/scripts/init-env.sh
git commit -m "feat: add init-env.sh — auto-create .env from .env.example on first open"
```

---

## Task 5: Update devcontainer.json

**Files:**
- Modify: `.devcontainer/devcontainer.json`

Three changes: add `initializeCommand`, add `--env-file .env` to `runArgs`, update `build` to pass `BASE_IMAGE` as a build arg.

- [ ] **Step 1: Open `.devcontainer/devcontainer.json`**

Current content:
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

- [ ] **Step 2: Apply all three changes**

Replace the entire file with:
```json
{
  "name": "Claude DevPod (UBI9)",
  "initializeCommand": ".devcontainer/scripts/init-env.sh",
  "build": {
    "dockerfile": "Dockerfile",
    "context": "..",
    "args": {
      "BASE_IMAGE": "${localEnv:DEVPOD_BASE_IMAGE}"
    }
  },
  "runArgs": [
    "--privileged",
    "--env-file",
    ".env"
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

**Notes:**
- `initializeCommand` runs on the Windows host before container start — uses the path relative to the repo root.
- `${localEnv:DEVPOD_BASE_IMAGE}` is resolved by VS Code from the host shell environment. If unset, the Dockerfile ARG default is used (added in Task 6).
- `--env-file` and `.env` are separate array entries (Podman/Docker syntax requires the value as the next argument).

- [ ] **Step 3: Validate JSON**

```bash
python3 -m json.tool .devcontainer/devcontainer.json > /dev/null && echo "JSON valid"
```

Expected: `JSON valid`

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/devcontainer.json
git commit -m "feat: add initializeCommand, --env-file, and BASE_IMAGE build arg to devcontainer.json"
```

---

## Task 6: Update Dockerfile

**Files:**
- Modify: `.devcontainer/Dockerfile`

Add `ARG BASE_IMAGE` before `FROM` so the base image is configurable. Also pin the default tag from `latest` to `9.4` for reproducibility.

- [ ] **Step 1: Open `.devcontainer/Dockerfile`**

Current first line:
```dockerfile
FROM registry.access.redhat.com/ubi9/ubi:latest
```

- [ ] **Step 2: Replace the first line**

```dockerfile
ARG BASE_IMAGE=registry.access.redhat.com/ubi9/ubi:9.4
FROM ${BASE_IMAGE}
```

The rest of the Dockerfile is unchanged.

- [ ] **Step 3: Verify the file starts correctly**

```bash
head -3 .devcontainer/Dockerfile
```

Expected:
```
ARG BASE_IMAGE=registry.access.redhat.com/ubi9/ubi:9.4
FROM ${BASE_IMAGE}

```

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/Dockerfile
git commit -m "feat: add ARG BASE_IMAGE to Dockerfile; pin default tag to ubi9:9.4"
```

---

## Task 7: Create VS Code workspace file

**Files:**
- Create: `claude-devpod.code-workspace`

Multi-folder workspace at the repo root with two folders (parent repo + demo) and two inline tasks.

- [ ] **Step 1: Create `claude-devpod.code-workspace` at the repo root**

```json
{
  "folders": [
    {
      "name": "claude-devpod",
      "path": "."
    },
    {
      "name": "demo-svc",
      "path": "container_in_container/demo"
    }
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
- `demo-svc: Run` — `podman image exists demo-svc` exits 0 if the image exists, skipping the build. If the image is absent it builds first, then runs.
- `demo-svc: Rebuild & Run` — always rebuilds before running. Use this after changing `app.py`, `templates/`, or `Dockerfile`.
- `${env:DEVPOD_DEMO_PORT}` resolves from the `--env-file .env` injection, so the port is controlled by a single value.
- Both tasks run inside the devcontainer where `podman` is on PATH.

- [ ] **Step 2: Validate JSON**

```bash
python3 -m json.tool claude-devpod.code-workspace > /dev/null && echo "JSON valid"
```

Expected: `JSON valid`

- [ ] **Step 3: Commit**

```bash
git add claude-devpod.code-workspace
git commit -m "feat: add multi-folder VS Code workspace with Run and Rebuild & Run tasks"
```

---

## Task 8: Stage and commit the demo sub-project

**Files:**
- Stage: `container_in_container/demo/` (all files)

Now that `.gitignore` allows the demo, add all its files to the top-level repo in one commit.

- [ ] **Step 1: Verify what will be staged**

```bash
git status --short container_in_container/
```

Expected: all demo files listed as `??` (untracked), no files from other sub-projects.

- [ ] **Step 2: Stage the demo directory**

```bash
git add container_in_container/demo/
```

- [ ] **Step 3: Review what was staged**

```bash
git status --short container_in_container/
```

Expected: all demo files now listed as `A ` (added). Confirm no unexpected files.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: add container_in_container/demo — runnable container-in-container example"
```

---

## Task 9: Update README.md

**Files:**
- Modify: `README.md`

Add environment variable and workspace instructions to the Usage section. The current README has a "Usage" section at line 23 with two subsections: "Open this repo as a dev container" (lines 25–30) and "Use as a template for another project" (lines 32–35). Insert the new content between them.

- [ ] **Step 1: Open `README.md` and find the insertion point**

Locate line 32 — the start of `### Use as a template for another project`.

- [ ] **Step 2: Insert two new subsections before line 32**

Insert the following block between the "Open this repo as a dev container" subsection and the "Use as a template" subsection:

```
### Environment variables

A `.env.example` file at the repo root contains all available `DEVPOD_*` variables with their defaults.
On first devcontainer open VS Code automatically copies it to `.env` — no manual action required.

To customise (e.g., change the demo port or base image), edit `.env` before reopening the container.
Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `DEVPOD_BASE_IMAGE` | `registry.access.redhat.com/ubi9/ubi:9.4` | Devcontainer base image |
| `DEVPOD_PROJECT_NAME` | `claude-devpod` | Project name inside the container |
| `DEVPOD_PROJECT_PATH` | `/workspaces/claude-devpod` | Project path inside the container |
| `DEVPOD_DEMO_PORT` | `8080` | Host port forwarded to the demo-svc container |

### Opening the workspace

Open `claude-devpod.code-workspace` instead of the folder directly — this gives you a multi-folder
workspace with the parent repo and `demo-svc` as separate Explorer roots, plus pre-configured tasks.

**File → Open Workspace from File…** → select `claude-devpod.code-workspace`

To launch the demo service use the VS Code task runner (`Ctrl+Shift+P` → **Tasks: Run Task**):
- **demo-svc: Run** — builds the image on first use (skips build if image exists), then starts the container
- **demo-svc: Rebuild & Run** — always rebuilds; use after changing `app.py`, templates, or the Dockerfile

The dashboard is available at `http://localhost:8080` (or the port set in `DEVPOD_DEMO_PORT`).

```

- [ ] **Step 3: Verify the README renders correctly**

Check that the table has correct pipe alignment and the section headers are `###` (not `##`):

```bash
grep -n "###" README.md
```

Expected output should include:
```
25:### Open this repo as a dev container
32:### Environment variables
50:### Opening the workspace
61:### Use as a template for another project
```

(Line numbers will shift after insertion — the key is that the four subsections are all present under `## Usage`.)

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add env setup and workspace instructions to README"
```
