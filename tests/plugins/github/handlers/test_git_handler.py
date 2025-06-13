from unittest.mock import _Call, call

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_run_shell_command(mocker: MockerFixture):
    return mocker.patch("src.plugins.github.handlers.git.run_shell_command")


async def test_checkout_branch(mock_run_shell_command):
    from src.plugins.github.handlers.git import GitHandler

    git_handler = GitHandler()
    git_handler.checkout_branch("main")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "checkout", "main"]),
        ]
    )


async def test_checkout_branch_with_update(mock_run_shell_command):
    from src.plugins.github.handlers.git import GitHandler

    git_handler = GitHandler()
    git_handler.checkout_branch("main", update=True)

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "checkout", "main"]),
            call(["git", "pull"]),
        ]
    )


async def test_checkout_remote_branch(mock_run_shell_command):
    from src.plugins.github.handlers.git import GitHandler

    git_handler = GitHandler()
    git_handler.checkout_remote_branch("main")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "fetch", "origin", "main"]),
            call(["git", "checkout", "main"]),
        ]
    )


async def test_add_file(mock_run_shell_command):
    from src.plugins.github.handlers.git import GitHandler

    git_handler = GitHandler()
    git_handler.add_file("test.txt")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "add", "test.txt"]),
        ]
    )


async def test_add_all_files(mock_run_shell_command):
    from src.plugins.github.handlers.git import GitHandler

    git_handler = GitHandler()
    git_handler.add_all_files()

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "add", "-A"]),
        ]
    )


async def test_commit_and_push(mock_run_shell_command):
    from src.plugins.github.handlers.git import GitHandler

    git_handler = GitHandler()
    git_handler.commit_and_push("commit message", "main", "author")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "config", "--global", "user.name", "author"]),
            call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "author@users.noreply.github.com",
                ]
            ),
            call(["git", "commit", "-m", "commit message"]),
            call(["git", "fetch", "origin"]),
            call(["git", "diff", "origin/main", "main"]),
            _Call(("().stdout.__bool__", (), {})),
            call(["git", "push", "origin", "main", "-f"]),
        ],
    )


async def test_commit_and_push_diff_no_change(mock_run_shell_command):
    """本地分支与远程分支一致，跳过推送的情况"""
    from src.plugins.github.handlers.git import GitHandler

    # 本地分支与远程分支一致时 git diff 应该返回空字符串
    mock_run_shell_command.return_value.stdout = ""

    git_handler = GitHandler()
    git_handler.commit_and_push("commit message", "main", "author")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "config", "--global", "user.name", "author"]),
            call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "author@users.noreply.github.com",
                ]
            ),
            call(["git", "commit", "-m", "commit message"]),
            call(["git", "fetch", "origin"]),
            call(["git", "diff", "origin/main", "main"]),
        ],
    )


async def test_delete_origin_branch(mock_run_shell_command):
    from src.plugins.github.handlers.git import GitHandler

    git_handler = GitHandler()
    git_handler.delete_remote_branch("main")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "push", "origin", "--delete", "main"]),
        ]
    )


async def test_switch_branch(mock_run_shell_command):
    from src.plugins.github.handlers.git import GitHandler

    git_handler = GitHandler()
    git_handler.switch_branch("main")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "switch", "-C", "main"]),
        ]
    )
