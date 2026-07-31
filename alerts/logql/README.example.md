# LogQL alert examples [LEGACY]

These queries target **Loki** (LogQL) and are kept for rollback only.

The default log store is now **VictoriaLogs** — use the LogsQL examples in
`alerts/logsql/` instead.

Quick LogQL → LogsQL mapping:

| LogQL | LogsQL |
|-------|--------|
| `{org="example-org"}` | `_stream:{instansi="example-org"}` |
| `\|~ "pattern"` | `~"pattern"` |
| `\|= "text"` | `"text"` |
| `[5m]` range vector | `_time:5m` prefix |
