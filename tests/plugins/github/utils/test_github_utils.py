"""测试 plugins/github/utils.py"""

import re
import subprocess
from re import Pattern
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture


def test_run_shell_command_success(mocker: MockerFixture):
    """测试 run_shell_command 命令执行成功的情况"""
    from src.plugins.github.utils import run_shell_command

    mock_result = MagicMock()
    mock_result.stdout.decode.return_value = "command output"

    mock_run = mocker.patch("subprocess.run", return_value=mock_result)

    result = run_shell_command(["git", "status"])

    mock_run.assert_called_once_with(["git", "status"], check=True, capture_output=True)
    assert result == mock_result


def test_run_shell_command_failure(mocker: MockerFixture):
    """测试 run_shell_command 命令执行失败时抛出异常"""
    from src.plugins.github.utils import run_shell_command

    # 创建一个模拟的 CalledProcessError
    error = subprocess.CalledProcessError(1, ["git", "status"])
    error.stdout = b"standard output"
    error.stderr = b"error output"

    mock_run = mocker.patch("subprocess.run", side_effect=error)

    with pytest.raises(subprocess.CalledProcessError):
        run_shell_command(["git", "status"])

    mock_run.assert_called_once_with(["git", "status"], check=True, capture_output=True)


def test_commit_message():
    """测试 commit_message 函数"""
    from src.plugins.github.utils import commit_message

    result = commit_message(":sparkles:", "add feature", 123)
    assert result == ":sparkles: add feature (#123)"


def test_extract_issue_info_from_issue_single_pattern():
    """测试 extract_issue_info_from_issue 使用单个正则表达式"""
    from src.plugins.github.utils import extract_issue_info_from_issue

    patterns: dict[str, Pattern[str] | list[Pattern[str]]] = {
        "name": re.compile(r"Name: (\w+)"),
        "version": re.compile(r"Version: ([\d.]+)"),
    }
    body = "Name: TestPlugin\nVersion: 1.0.0\n"

    result = extract_issue_info_from_issue(patterns, body)

    assert result == {"name": "TestPlugin", "version": "1.0.0"}


def test_extract_issue_info_from_issue_list_pattern():
    """测试 extract_issue_info_from_issue 使用正则表达式列表"""
    from src.plugins.github.utils import extract_issue_info_from_issue

    patterns: dict[str, Pattern[str] | list[Pattern[str]]] = {
        "module": [
            re.compile(r"Module Name: (\w+)"),
            re.compile(r"Import Name: (\w+)"),
        ],
    }
    body = "Import Name: test_module\n"

    result = extract_issue_info_from_issue(patterns, body)

    assert result == {"module": "test_module"}


def test_extract_issue_info_from_issue_no_match():
    """测试 extract_issue_info_from_issue 未匹配时返回空字典"""
    from src.plugins.github.utils import extract_issue_info_from_issue

    patterns: dict[str, Pattern[str] | list[Pattern[str]]] = {
        "name": re.compile(r"Name: (\w+)"),
    }
    body = "No matching content here"

    result = extract_issue_info_from_issue(patterns, body)

    assert result == {}


def test_extract_issue_info_from_issue_partial_match():
    """测试 extract_issue_info_from_issue 部分匹配"""
    from src.plugins.github.utils import extract_issue_info_from_issue

    patterns: dict[str, Pattern[str] | list[Pattern[str]]] = {
        "name": re.compile(r"Name: (\w+)"),
        "version": re.compile(r"Version: ([\d.]+)"),
    }
    body = "Name: TestPlugin\n"

    result = extract_issue_info_from_issue(patterns, body)

    # 只返回匹配到的项
    assert result == {"name": "TestPlugin"}
    assert "version" not in result
