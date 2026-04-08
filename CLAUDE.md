# CLAUDE.md — Project Ruleset

This is a living document. Update it whenever major architectural or process decisions are made.

---

## Repository Structure

- **Parent repo** lives at `/workspaces/<project-name>/`. Do not store sub-project code, configs, or documentation here.
- **Sub-projects** go in `container_in_container/<sub-project>/`. Each sub-project is a standalone git repo managed independently.
- Sub-project names and details must **never** be committed to the top-level repo, with one exception: `container_in_container/demo/` is permanently tracked so users have a runnable example out of the box.

---

## Git Workflow

- **Never commit directly to `main`.** All changes must go through a pull request on a relevantly named branch.
- Use **git worktrees** for isolated development branches.
- After merging a PR: delete the remote branch, reset local `main` and `origin/main`.
- Never force-push to `main` or bypass safety checks as a shortcut.

---

## Documentation

- Keep documentation current whenever changes are made.
- **CLAUDE.md is a living document** — update it whenever major decisions are made.
- Ensure `.gitignore` stays current; never leak secrets, sub-project names, or sensitive paths.

---

## Security

- Keep security best practices in mind at all times.
- If a dependency has a known CVE, flag it and recommend remediation before proceeding.
- Never commit secrets, credentials, tokens, or environment files.

---

## Debugging & Problem Solving

- When something is broken or unclear, **read the error carefully and investigate root cause** before changing anything.
- Prefer targeted, reversible fixes over broad rewrites unless a rewrite is clearly warranted.
- If a fix attempt fails, diagnose why before trying a different approach.
- Escalate to the user only after investigation — not as a first response to friction.

---

## Tooling

- Always use plugins, MCP servers, and skills where and when appropriate.
