"""Tests for the ailbibak scripts with bash and zsh.

Each test runs the scripts with both shells. The scripts back up to a
remote server over ssh, so tests/bin/ssh fakes ssh: it runs the remote
commands locally in a temporary folder. Tests which use the remote
server also run with both shells as its login shell.
"""

import os
import re
import subprocess
import time
from pathlib import Path
from textwrap import dedent

import pytest

BIN = Path(__file__).parent.parent / "bin"
FAKE_SSH_DIR = Path(__file__).parent / "bin"
SHELLS = ["bash", "zsh"]
SCRIPTS = ["ailbibak-push", "ailbibak-status", "ailbibak-diff"]


@pytest.fixture(params=SHELLS)
def shell(request):
    """The shell which runs the scripts."""
    return request.param


@pytest.fixture(params=SHELLS, ids=[f"remote-{shell}" for shell in SHELLS])
def remote_shell(request):
    """The login shell on the remote server."""
    return request.param


@pytest.fixture(autouse=True)
def environment(monkeypatch):
    monkeypatch.setenv("PATH", f"{FAKE_SSH_DIR}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("LC_ALL", "C")
    # without a remote server, the fake ssh fails
    monkeypatch.delenv("AILBIBAK_REMOTE_HOME", raising=False)


@pytest.fixture
def backup(tmp_path, monkeypatch, remote_shell):
    """The backup folder on the remote server."""
    home = tmp_path / "remote"
    home.mkdir()
    monkeypatch.setenv("AILBIBAK_REMOTE_HOME", str(home))
    monkeypatch.setenv("AILBIBAK_REMOTE_SHELL", remote_shell)
    return home / "backup"


@pytest.fixture
def folder(tmp_path):
    """A folder to back up, configured for the backup folder."""
    folder = tmp_path / "documents"
    (folder / ".ailbibak").mkdir(parents=True)
    (folder / ".ailbibak/ailbibak.conf").write_text(
        dedent(
            f"""\
            SOURCE={folder}/
            DESTINATION=backupserver:backup
            EXCLUDES={folder}/.ailbibak/excludes.txt
            MESSAGE_PATH={folder}/.ailbibak/message.txt
            """
        )
    )
    (folder / ".ailbibak/excludes.txt").write_text("- *~\n")
    (folder / "budget.txt").write_text("2009\n")
    (folder / "plan.txt").write_text("draft\n")
    (folder / "plan.txt~").write_text("first draft\n")
    (folder / "notes.txt").write_text("notes\n")
    return folder


def run(shell, script, *args, cwd, input="", status=0):
    """Run a script with the shell and check its exit status."""
    result = subprocess.run(
        [shell, BIN / script, *args],
        cwd=cwd,
        input=input,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == status, result.stdout + result.stderr
    return result


def remove_setting(folder, setting):
    config = folder / ".ailbibak/ailbibak.conf"
    text = re.sub(rf"^{setting}=.*\n", "", config.read_text(), flags=re.MULTILINE)
    config.write_text(text)


def change(folder):
    """Change, add and remove a file in the folder."""
    (folder / "plan.txt").write_text("final version\n")
    (folder / "todo.txt").write_text("buy paper\n")
    (folder / "notes.txt").unlink()


def revisions(backup):
    return sorted(path for path in backup.iterdir() if path.name != "current")


def files(path):
    return sorted(str(file.relative_to(path)) for file in path.rglob("*"))


@pytest.mark.parametrize("script", SCRIPTS)
@pytest.mark.parametrize("option", ["-h", "--help"])
def test_help(shell, script, option, tmp_path):
    result = run(shell, script, option, cwd=tmp_path, status=1)
    assert f"Usage: {script} [-h] [--help]" in result.stdout


@pytest.mark.parametrize("script", SCRIPTS)
@pytest.mark.parametrize(
    "args", [["-x"], ["one", "two"]], ids=["unknown-option", "extra-argument"]
)
def test_bad_arguments(shell, script, args, tmp_path):
    result = run(shell, script, *args, cwd=tmp_path, status=1)
    assert f"Usage: {script} [-h] [--help]" in result.stdout


@pytest.mark.parametrize("script", SCRIPTS)
@pytest.mark.parametrize("setting", ["SOURCE", "DESTINATION", "EXCLUDES"])
def test_missing_setting(shell, script, setting, folder):
    remove_setting(folder, setting)
    result = run(shell, script, cwd=folder, status=2)
    assert f'The setting "{setting}" is missing' in result.stdout + result.stderr


def test_push(shell, remote_shell, folder, backup):
    run(shell, "ailbibak-push", "-m", "Budget for 2009", cwd=folder)
    [revision] = revisions(backup)
    assert re.fullmatch(r"\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d", revision.name)
    assert (backup / "current").samefile(revision)
    assert files(revision) == [
        ".ailbibak",
        ".ailbibak/ailbibak.conf",
        ".ailbibak/excludes.txt",
        ".ailbibak/message.txt",
        "budget.txt",
        "notes.txt",
        "plan.txt",
    ]
    assert (revision / "plan.txt").read_text() == "draft\n"
    timestamp, message = (revision / ".ailbibak/message.txt").read_text().splitlines()
    assert re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", timestamp)
    assert message == "Budget for 2009"


def test_push_new_revision(shell, remote_shell, folder, backup):
    run(shell, "ailbibak-push", cwd=folder)
    time.sleep(1)  # revisions are named by the second
    change(folder)
    run(shell, "ailbibak-push", "--message", "Final plan", cwd=folder)
    old, new = revisions(backup)
    assert (backup / "current").samefile(new)
    assert (old / "plan.txt").read_text() == "draft\n"
    assert (new / "plan.txt").read_text() == "final version\n"
    assert not (old / "todo.txt").exists()
    assert (new / "todo.txt").exists()
    assert (old / "notes.txt").exists()
    assert not (new / "notes.txt").exists()
    # an unchanged file is a hard link to the previous revision
    assert (new / "budget.txt").samefile(old / "budget.txt")
    assert (new / ".ailbibak/message.txt").read_text().endswith("\nFinal plan\n")


@pytest.mark.parametrize(
    "argument",
    ["documents", "documents/.ailbibak/ailbibak.conf"],
    ids=["folder", "config-file"],
)
def test_push_argument(shell, remote_shell, folder, backup, argument):
    run(shell, "ailbibak-push", argument, cwd=folder.parent)
    [revision] = revisions(backup)
    assert (revision / "plan.txt").exists()


def test_push_message_needs_message_path(shell, folder):
    remove_setting(folder, "MESSAGE_PATH")
    result = run(shell, "ailbibak-push", "-m", "Budget", cwd=folder, status=2)
    assert 'The setting "MESSAGE_PATH" is missing' in result.stdout


def test_push_declines_to_create_config(shell, tmp_path):
    result = run(shell, "ailbibak-push", cwd=tmp_path, input="n\n")
    assert "ailbibak.conf was not found" in result.stdout
    assert not (tmp_path / ".ailbibak").exists()


def test_push_creates_sample_files(shell, tmp_path):
    result = run(shell, "ailbibak-push", cwd=tmp_path, input="y\ny\n")
    assert "run ailbibak-push again" in result.stdout
    config = (tmp_path / ".ailbibak/ailbibak.conf").read_text()
    assert f"\nSOURCE={tmp_path}/\n" in config
    assert "\nDESTINATION=localhost:backup\n" in config
    assert (tmp_path / ".ailbibak/excludes.txt").exists()


def test_push_with_sample_files(shell, remote_shell, tmp_path, backup):
    """The sample excludes file backs up only the configuration."""
    folder = tmp_path / "documents"
    folder.mkdir()
    (folder / "budget.txt").write_text("2009\n")
    run(shell, "ailbibak-push", cwd=folder, input="y\ny\n")
    run(shell, "ailbibak-push", cwd=folder)
    [revision] = revisions(backup)
    assert files(revision) == [
        ".ailbibak",
        ".ailbibak/ailbibak.conf",
        ".ailbibak/excludes.txt",
        ".ailbibak/message.txt",
    ]


def test_status(shell, remote_shell, folder, backup):
    run(shell, "ailbibak-push", cwd=folder)
    change(folder)
    result = run(shell, "ailbibak-status", cwd=folder)
    lines = result.stdout.splitlines()
    changes = {name: flags for flags, name in map(str.split, lines)}
    assert changes["plan.txt"].startswith("<f")
    assert changes["todo.txt"] == "<f+++++++++"
    assert changes["notes.txt"] == "*deleting"
    assert "budget.txt" not in changes
    assert "plan.txt~" not in changes
    [revision] = revisions(backup)
    assert (revision / "plan.txt").read_text() == "draft\n"


def test_diff(shell, remote_shell, folder, backup):
    run(shell, "ailbibak-push", cwd=folder)
    change(folder)
    result = run(shell, "ailbibak-diff", cwd=folder)
    assert "\n< draft\n---\n> final version\n" in result.stdout
    assert re.search(r"^Only in \S+: todo\.txt$", result.stdout, re.MULTILINE)
    assert "Only in backup/current: notes.txt" in result.stdout.splitlines()
    assert "budget.txt" not in result.stdout
    # the temporary directory is gone
    [revision] = revisions(backup)
    assert (revision / "plan.txt").read_text() == "draft\n"


def test_ailbibak_usage(shell, tmp_path):
    result = run(shell, "ailbibak", cwd=tmp_path)
    assert result.stdout == "Usage: ailbibak <config-file-path>\n"


def test_ailbibak_missing_config(shell, tmp_path):
    result = run(shell, "ailbibak", "pull.conf", cwd=tmp_path)
    assert result.stdout == "Configuration file pull.conf not found\n"


def test_ailbibak(shell, folder, tmp_path):
    (tmp_path / "pull.conf").write_text(
        dedent(
            f"""\
            SOURCE={folder}/
            EXCLUDES={folder}/.ailbibak/excludes.txt
            """
        )
    )
    backup = tmp_path / "pull"
    backup.mkdir()
    run(shell, "ailbibak", tmp_path / "pull.conf", cwd=backup)
    [revision] = revisions(backup)
    assert re.fullmatch(r"\d{4}-\d\d-\d\d_\d\d-\d\d", revision.name)
    assert (backup / "current").samefile(revision)
    assert (revision / "plan.txt").read_text() == "draft\n"
    assert not (revision / "plan.txt~").exists()
