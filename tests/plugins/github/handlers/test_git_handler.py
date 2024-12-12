from unittest.mock import _Call, call

from pytest_mock import MockerFixture


async def test_checkout_branch(mocker: MockerFixture):
    from src.plugins.github.handlers.git import GitHandler

    mock_run_shell_command = mocker.patch(
        "src.plugins.github.handlers.git.run_shell_command"
    )

    git_handler = GitHandler()
    git_handler.checkout_branch("main")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "checkout", "main"]),
        ]
    )


async def test_checkout_remote_branch(mocker: MockerFixture):
    from src.plugins.github.handlers.git import GitHandler

    mock_run_shell_command = mocker.patch(
        "src.plugins.github.handlers.git.run_shell_command"
    )

    git_handler = GitHandler()
    git_handler.checkout_remote_branch("main")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "fetch", "origin", "main"]),
            call(["git", "checkout", "main"]),
        ]
    )


async def test_commit_and_push(mocker: MockerFixture):
    from src.plugins.github.handlers.git import GitHandler

    mock_run_shell_command = mocker.patch(
        "src.plugins.github.handlers.git.run_shell_command"
    )

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
            call(["git", "add", "-A"]),
            call(["git", "commit", "-m", "commit message"]),
            call(["git", "fetch", "origin"]),
            call(["git", "diff", "origin/main", "main"]),
            _Call(("().stdout.__bool__", (), {})),
            call(["git", "push", "origin", "main", "-f"]),
        ],
    )


async def test_delete_origin_branch(mocker: MockerFixture):
    from src.plugins.github.handlers.git import GitHandler

    mock_run_shell_command = mocker.patch(
        "src.plugins.github.handlers.git.run_shell_command"
    )

    git_handler = GitHandler()
    git_handler.delete_origin_branch("main")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "push", "origin", "--delete", "main"]),
        ]
    )


async def test_switch_branch(mocker: MockerFixture):
    from src.plugins.github.handlers.git import GitHandler

    mock_run_shell_command = mocker.patch(
        "src.plugins.github.handlers.git.run_shell_command"
    )

    git_handler = GitHandler()
    git_handler.switch_branch("main")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "switch", "-C", "main"]),
        ]
    )
