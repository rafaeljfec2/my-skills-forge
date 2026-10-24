# Discover capabilities and scope

Read this reference only for workflow step 1.

## Discover before scanning

Inspect the tools available in this session. Record each relevant capability as one of:

- available and usable
- available, missing permission or configuration
- unavailable
- not verified

Look for capabilities that support source-code scanning, dependency analysis, finding details and locations, fix guidance, and a rescan after edits. Use only tool names and arguments confirmed in this environment.

If Snyk MCP is missing, say so before any fallback.

A Snyk CLI fallback is allowed only when the CLI is already installed, already authenticated, fits the task, and the environment permits it. Do not install, log in, or change integrations without authorization.

If no suitable Snyk scanner is available, stop with a capability-gap report: what was checked, what is missing, and what is needed to continue. Do not fabricate findings. Do not run a different scanner and label the result as Snyk.

## Choose scope

Identify the repository root, working tree, changed and untracked files, package manifests, lockfiles, and the test commands the repo already uses. Note project security rules that constrain fixes.

Prefer the smallest scope that answers the request. A post-change scan covers the changed and untracked files the verified tool can scan. A full audit uses the scope the user named; state that scope before scanning.

Record which targets the verified tool documents as supported. Do not scan a language or artifact that tool does not support. Do not treat a language list from memory as the tool's coverage.

## Environment limits

Use planning and approval only through a mechanism this session actually exposes. Do not claim that Cursor, Claude Code, or Codex changed mode. This skill does not grant permissions.

If the session cannot pause for approval, stay in scan mode and say that remediation was not started.
