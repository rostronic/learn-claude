# Integrating MCP servers — exercise

You're given a pure-logic model of two MCP-integration behaviors in
`starter/mcp_config.py`: resolving a server definition across scopes by precedence,
and expanding environment-variable placeholders in a `.mcp.json` value. No Claude
Code process, no network — you implement the documented rules; the tests encode the
contract.

## Setup

```bash
cd ~/learn-claude-work/5.5
pip install -r requirements.txt && pytest
```

All in-memory; only `pytest` is needed.

## Your task

Implement two functions in `starter/mcp_config.py`:

1. **`resolve_server(name, servers_by_scope)`** — return the config for `name` from
   the **highest-precedence** scope that defines it (`local` → `project` → `user`),
   **without merging** fields across scopes. Return `None` if undefined everywhere.

2. **`expand_env(value, env)`** — expand `${VAR}` (raise `KeyError` if missing) and
   `${VAR:-default}` (use the default when `VAR` is unset). Leave non-placeholder
   text unchanged. This is why secrets stay out of a shared `.mcp.json`: the file
   holds placeholders, the environment holds the values, and a missing required var
   fails loudly.

## What we check

See `rubric.yaml`: precedence is correct and fields are **not** merged across
scopes, env expansion handles `${VAR}` / `${VAR:-default}` and fails on a missing
required var, and the full suite passes.

## When you're done

Run `pytest` until green, then `/verify 5.5`.
