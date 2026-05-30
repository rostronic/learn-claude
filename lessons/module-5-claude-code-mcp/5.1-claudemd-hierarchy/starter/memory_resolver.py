"""Resolve which CLAUDE.md memory files load, in Claude Code's documented order.

This is a pure-logic model of Claude Code's memory discovery — no Claude Code
process, no API calls. You implement the load-order rules from the lesson; the
tests encode the contract (which is taken straight from the official memory docs).

Documented LOAD ORDER (the order files enter context), broadest scope first:
  1. managed policy   (a fixed system path)
  2. user memory      (~/.claude/CLAUDE.md)
  3. project memory   (the directory tree, ROOT-DOWN to cwd; within each dir,
                       CLAUDE.md then CLAUDE.local.md)

Because files are concatenated (not overridden) and "instructions closer to where
you launched Claude are read last," the project tree is emitted ROOT FIRST and the
cwd directory LAST. Subtree files BELOW cwd load lazily — modeled separately.
"""

# Stand-in for the OS-specific managed-policy path; the logic does not depend on it.
MANAGED_PATH = "/etc/claude-code/CLAUDE.md"


def resolve_memory(cwd, existing_files, *, managed=MANAGED_PATH,
                   user_home="/home/dev"):
    """Return the CLAUDE.md files that load at launch, in documented LOAD ORDER.

    Args:
        cwd: absolute path of the current working directory, e.g. "/repo/api".
        existing_files: a set/iterable of absolute paths that exist on disk.
        managed: absolute path to the managed-policy file (may not exist).
        user_home: the user's home dir; user memory is
            f"{user_home}/.claude/CLAUDE.md".

    Rules (implement these), emitting only paths present in existing_files:
      1. managed policy first, IF it exists.
      2. then user memory (f"{user_home}/.claude/CLAUDE.md"), IF it exists.
      3. then project memory: walk the directory tree from the filesystem root
         DOWN to cwd. For each directory on that path, in root->cwd order, emit
         "<dir>/CLAUDE.md" then "<dir>/CLAUDE.local.md" (each only if it exists).
         So the ROOT-most file comes first and the cwd file comes LAST.

    Note: CLAUDE.local.md is NOT ignored — it is the per-directory "Local
    instructions" file, appended right after that directory's CLAUDE.md.

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement resolve_memory")


def discover_subtree_memory(cwd, read_file_path, existing_files):
    """Return the subtree CLAUDE.md activated when read_file_path is read.

    Subtree memory is lazy: a CLAUDE.md in a directory *below* cwd is only
    included once Claude reads a file inside that subtree.

    Return "<dir>/CLAUDE.md" for every directory that is
    - strictly below cwd, AND
    - on the path from cwd down to the directory containing read_file_path, AND
    - has a CLAUDE.md present in existing_files.
    Order: nearest cwd first (top-down). If read_file_path is not under cwd, [].

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement discover_subtree_memory")
