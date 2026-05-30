from memory_resolver import resolve_memory, discover_subtree_memory


def test_project_tree_is_root_down():
    files = {
        "/repo/CLAUDE.md",
        "/repo/services/CLAUDE.md",
        "/repo/services/api/CLAUDE.md",
    }
    result = resolve_memory("/repo/services/api", files,
                            managed="/none", user_home="/home/dev")
    # root first, cwd last (nearest is read LAST)
    assert result == [
        "/repo/CLAUDE.md",
        "/repo/services/CLAUDE.md",
        "/repo/services/api/CLAUDE.md",
    ]


def test_root_and_subdir_both_apply():
    files = {"/repo/CLAUDE.md", "/repo/frontend/CLAUDE.md"}
    result = resolve_memory("/repo/frontend", files,
                            managed="/none", user_home="/home/dev")
    assert "/repo/CLAUDE.md" in result
    assert "/repo/frontend/CLAUDE.md" in result
    # composition, not override: both present
    assert len(result) == 2


def test_load_order_managed_then_user_then_project():
    files = {
        "/etc/claude-code/CLAUDE.md",
        "/home/dev/.claude/CLAUDE.md",
        "/repo/CLAUDE.md",
    }
    result = resolve_memory("/repo", files,
                            managed="/etc/claude-code/CLAUDE.md",
                            user_home="/home/dev")
    assert result == [
        "/etc/claude-code/CLAUDE.md",
        "/home/dev/.claude/CLAUDE.md",
        "/repo/CLAUDE.md",
    ]


def test_local_md_appended_after_claude_md_in_same_dir():
    files = {"/repo/CLAUDE.md", "/repo/CLAUDE.local.md"}
    result = resolve_memory("/repo", files,
                            managed="/none", user_home="/home/dev")
    assert result == ["/repo/CLAUDE.md", "/repo/CLAUDE.local.md"]


def test_missing_files_are_skipped():
    files = {"/repo/CLAUDE.md"}  # no managed, no user file present
    result = resolve_memory("/repo/api", files,
                            managed="/etc/claude-code/CLAUDE.md",
                            user_home="/home/dev")
    assert result == ["/repo/CLAUDE.md"]


def test_subtree_memory_is_lazy():
    files = {"/repo/CLAUDE.md", "/repo/frontend/CLAUDE.md"}
    # Launched at /repo, nothing under frontend/ touched yet:
    assert discover_subtree_memory("/repo", "/repo/README.md", files) == []
    # Now Claude reads a file under frontend/ -> its CLAUDE.md activates:
    got = discover_subtree_memory("/repo", "/repo/frontend/app.tsx", files)
    assert got == ["/repo/frontend/CLAUDE.md"]


def test_subtree_memory_top_down_order():
    files = {"/repo/a/CLAUDE.md", "/repo/a/b/CLAUDE.md"}
    got = discover_subtree_memory("/repo", "/repo/a/b/c/x.py", files)
    assert got == ["/repo/a/CLAUDE.md", "/repo/a/b/CLAUDE.md"]
