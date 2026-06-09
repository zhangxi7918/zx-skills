---
name: local-debug-logs
description: Use when debugging this ai_customer_mining project locally and the user describes a runtime issue, dev-server failure, client/server mismatch, Tauri desktop problem, chat/runtime bug, XHS tool issue, SSE/bridge issue, or asks to inspect client and server logs. Collect recent local client and server logs, process/port state, and relevant filtered log lines before diagnosing.
---

# Local Debug Logs

## Workflow

When the user reports a local debugging problem, gather evidence before proposing a fix.

1. Restate the reported symptom briefly, extracting useful keywords such as route paths, tool names, error codes, request IDs, session IDs, turn IDs, ports, and Chinese UI text.
2. Run the collector. It reads logs from the user's already-running local services; it must not start or restart client/server unless the user explicitly asks.

```bash
python3 .codex/skills/local-debug-logs/scripts/collect-local-debug-logs.py --query "<user problem summary>" --lines 200
```

3. Read the output in this order: summary, process/port state, errors/warnings, query matches, then recent client/server tails.
4. Correlate timestamps across client and server. Prefer exact identifiers over broad guesses.
5. If the collector shows missing logs or stale timestamps, inspect the running dev command/session when available. Users may run `pnpm dev` from the repository root or run client/server separately from `client/` and `server/`; both modes are valid. Tauri Rust logs are usually emitted to the terminal running `tauri dev`, not always to `.next/dev/logs`.
6. Diagnose from the logs and the user's symptom. Include concrete file references only after checking the relevant code path.

## Log Sources

Read `references/log-sources.md` when the diagnosis depends on where logs are written or why a source is missing.

Primary files:

- `client/.next/dev/logs/next-development.log`
- `server/.next/dev/logs/next-development.log`

Useful commands when deeper inspection is needed:

```bash
lsof -nP -iTCP:3000 -iTCP:8787
ps aux | rg 'pnpm|next dev|tauri dev|cargo|red-mine|redmine-server'
tail -n 200 client/.next/dev/logs/next-development.log
tail -n 200 server/.next/dev/logs/next-development.log
```

## Diagnosis Rules

- Treat heartbeat and cleanup logs as background noise unless the issue involves client bridge registration or connectivity.
- For chat/runtime issues, search for `RuntimeService`, `tool-runner`, `RuntimeHook`, `DrizzleRuntimeRepository`, `chat_`, `turnId`, and `sessionId`.
- For XHS issues, search for `xhs.`, `xhs_`, `ClientBridgeRuntime`, `client-bridge`, `BRIDGE_ACTION`, `login_required`, and browser action names.
- For UI issues, inspect client browser logs first, then map the component path from the message text or event names.
- For server API issues, inspect server logs first and then the matching route under `server/app/api`.
- If logs show only symptoms, inspect the code path before recommending changes.
- If evidence is inconclusive, say which log source is missing and give the next command to capture it.
