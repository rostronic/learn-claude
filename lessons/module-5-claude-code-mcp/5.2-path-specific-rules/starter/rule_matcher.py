"""A pure-logic model of Claude Code's .claude/rules/ path-scoped activation.

A rule file under .claude/rules/ may carry a `paths:` frontmatter list of globs.
Per the docs: a rule WITHOUT `paths` loads unconditionally; a rule WITH `paths`
activates only when Claude works with a file matching one of its globs. This
module models that activation decision. No Claude Code process, no API.

You implement two functions; the tests encode the contract (taken from the
documented glob table and loading rules).
"""


def glob_match(pattern, path):
    """Return True if `path` matches the glob `pattern` (gitignore-style).

    Semantics (this is exactly what the `paths:` field uses):
      - '/' separates path segments.
      - '*'  matches any run of characters WITHIN a single segment (never '/').
      - '**' matches zero or more whole segments (so 'a/**/b' matches 'a/b' and
        'a/x/y/b', and '**/*.ts' matches 'app.ts' and 'src/app.ts').
      - Any other character matches itself.
      - The whole path must match the whole pattern (anchored at both ends).

    Examples (from the documented pattern table):
      glob_match("**/*.ts", "app.ts")                 -> True
      glob_match("**/*.ts", "src/app.ts")             -> True
      glob_match("src/**/*", "src/api/handler.ts")    -> True
      glob_match("*.md", "README.md")                 -> True
      glob_match("*.md", "docs/README.md")            -> False
      glob_match("src/components/*.tsx", "src/components/Btn.tsx") -> True
      glob_match("src/components/*.tsx", "src/components/x/Btn.tsx") -> False

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement glob_match")


def active_rules(path, rules):
    """Return the names of the rules active when Claude works on `path`.

    Args:
        path: the file Claude is working with, e.g. "src/api/users.ts".
        rules: a list of dicts, each {"name": <str>, "paths": <list[str] or None>}.
            A rule with paths=None (or missing/empty) is UNCONDITIONAL — always
            active. A rule with a non-empty paths list is active iff ANY of its
            globs matches `path`.

    Return the names of active rules, preserving the input order.

    This models .claude/rules/ loading: unconditional rules plus the path-scoped
    rules whose globs match the file in play.

    TODO (exercise): implement this using glob_match.
    """
    raise NotImplementedError("implement active_rules")
