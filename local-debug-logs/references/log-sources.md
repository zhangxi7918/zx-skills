# Local Log Sources

This project runs local development from the workspace root with:

```bash
pnpm dev
```

Root `pnpm dev` starts both workspaces:

- client package `red-mine`: `tauri dev`
- server package `redmine-server`: `next dev -p ${LICENSE_SERVER_PORT:-8787}`

Users may also run services separately:

```bash
cd client && pnpm dev
cd server && pnpm dev
```

The collector should read the same project log files in either mode. Do not start, stop, or restart these services unless the user explicitly requests it.

## Client Logs

Primary file:

```text
client/.next/dev/logs/next-development.log
```

This file captures Next dev and browser console lines. Client console output is normalized by `client/lib/logging/console-line.ts` into lines like:

```text
[YYYY-MM-DD HH:mm:ss.SSS] [INFO] ...
```

Tauri/Rust logs use `tracing` initialized in `client/src-tauri/src/logging.rs`. They are generally emitted to the terminal running `tauri dev`; do not assume they are persisted in the Next log file.

## Server Logs

Primary file:

```text
server/.next/dev/logs/next-development.log
```

Server console output is normalized by `server/instrumentation.js` and `server/src/shared/infrastructure/console-log.js`.

The local server default is:

```text
http://127.0.0.1:8787
```

## Ports

Common local ports:

- `3000`: client Next frontend served for Tauri dev
- `8787`: server Next API

Use `lsof -nP -iTCP:3000 -iTCP:8787` to confirm ownership.

## High-Signal Search Terms

Chat/runtime:

- `RuntimeService`
- `tool-runner`
- `RuntimeHook`
- `DrizzleRuntimeRepository`
- `chat_`
- `turnId`
- `sessionId`

Client bridge and XHS:

- `ClientBridgeRuntime`
- `client-bridge`
- `BRIDGE_ACTION`
- `xhs.`
- `xhs_`
- `login_required`
- `heartbeat`

UI/client:

- `桌面 Bridge 调用`
- `桌面运行时适配器`
- `Fast Refresh`
- route path or visible UI text from the user's report
