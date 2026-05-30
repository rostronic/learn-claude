from ci_invoke import is_secret_reference, build_headless_command


def test_secret_reference_accepted():
    assert is_secret_reference("${{ secrets.ANTHROPIC_API_KEY }}") is True
    assert is_secret_reference("${{secrets.TOKEN}}") is True


def test_hardcoded_key_rejected():
    assert is_secret_reference("sk-ant-abc123") is False


def test_non_secret_expression_rejected():
    assert is_secret_reference("${{ env.FOO }}") is False
    assert is_secret_reference("") is False


def test_minimal_command():
    assert build_headless_command("hello") == ["claude", "-p", "hello"]


def test_allowed_tools_appended():
    assert build_headless_command("x", allowed_tools=["Read", "Edit"]) == [
        "claude", "-p", "x", "--allowedTools", "Read,Edit"
    ]


def test_empty_allowed_tools_omitted():
    assert build_headless_command("x", allowed_tools=[]) == ["claude", "-p", "x"]


def test_text_output_format_omitted():
    assert build_headless_command("x", output_format="text") == ["claude", "-p", "x"]


def test_full_command_order():
    assert build_headless_command(
        "fix tests",
        allowed_tools=["Read", "Edit"],
        output_format="json",
        permission_mode="dontAsk",
    ) == [
        "claude", "-p", "fix tests",
        "--allowedTools", "Read,Edit",
        "--output-format", "json",
        "--permission-mode", "dontAsk",
    ]
