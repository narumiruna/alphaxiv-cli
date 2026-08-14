from importlib.metadata import version

from typer.main import get_command
from typer.testing import CliRunner

from axiv.cli import app

runner = CliRunner()


def test_root_command_uses_axiv_name() -> None:
    assert get_command(app).name == "axiv"


def test_version_option_prints_installed_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout == f"axiv {version('axiv')}\n"
    assert result.stderr == ""


def test_root_help_lists_static_rest_command_groups() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "search" in result.stdout
    assert "researchers" in result.stdout
    assert "events" in result.stdout
    assert "feed" in result.stdout
    assert "paper" in result.stdout


def test_search_help_lists_fixed_commands() -> None:
    result = runner.invoke(app, ["search", "--help"])

    assert result.exit_code == 0
    assert "papers" in result.stdout
    assert "full-text" in result.stdout
    assert "topics" in result.stdout
    assert "organizations" in result.stdout


def test_paper_help_lists_fixed_commands() -> None:
    result = runner.invoke(app, ["paper", "--help"])

    assert result.exit_code == 0
    assert "show" in result.stdout
    assert "preview" in result.stdout
    assert "text" in result.stdout
    assert "overview" in result.stdout
    assert "related" in result.stdout


def test_unknown_command_exits_with_usage_error_on_stderr() -> None:
    result = runner.invoke(app, ["request", "GET", "https://example.com"])

    assert result.exit_code == 2
    assert "No such command" in result.stderr
    assert result.stdout == ""
