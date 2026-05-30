"""Pure-logic model of MCP scope precedence and .mcp.json env-var expansion.

No Claude Code process, no API, no network. You implement two documented behaviors:
resolving a server definition across scopes by precedence, and expanding
environment-variable placeholders in a config value. The tests encode the contract.
"""


def resolve_server(name, servers_by_scope):
    """Return the winning config for `name`, by documented scope precedence.

    Precedence order (highest first): "local", "project", "user".
    "Claude Code connects to it once, using the definition from the
    highest-precedence source; fields are not merged across scopes."

    Args:
        name: server name to resolve.
        servers_by_scope: dict mapping scope -> {server_name: config_dict}.
            Some scopes may be missing or not define `name`.

    Return the config dict from the highest-precedence scope that defines `name`,
    WITHOUT merging fields from lower scopes. Return None if no scope defines it.

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement resolve_server")


def expand_env(value, env):
    """Expand ${VAR} and ${VAR:-default} placeholders in a string `value`.

    Rules (per the .mcp.json docs):
      - "${VAR}" -> env[VAR]. If VAR is not in env, raise KeyError (the docs say
        Claude Code fails to parse a required var with no default).
      - "${VAR:-default}" -> env[VAR] if set, else the literal "default".
      - Text outside placeholders is left unchanged. Multiple placeholders in one
        string are all expanded.

    Variable names match [A-Za-z_][A-Za-z0-9_]*.

    Examples:
      expand_env("${A}/mcp", {"A": "x"})            -> "x/mcp"
      expand_env("${A:-def}", {})                    -> "def"
      expand_env("Bearer ${TOK}", {"TOK": "t"})      -> "Bearer t"
      expand_env("${MISSING}", {})                    -> raises KeyError

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement expand_env")
