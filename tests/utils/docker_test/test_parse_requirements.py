def test_parse_requirements():
    """解析 poetry export --without-hashes 的输出"""
    from src.providers.docker_test.plugin_test import parse_requirements

    output = """
anyio==4.6.2.post1 ; python_version >= "3.9" and python_version < "4.0"
nonebot2[httpx]==2.4.0 ; python_version >= "3.9" and python_version < "4.0"
nonebug==0.4.2 ; python_version >= "3.9" and python_version < "4.0"
pydantic-core==2.27.0 ; python_version >= "3.9" and python_version < "4.0"
pydantic==2.10.0 ; python_version >= "3.9" and python_version < "4.0"
"""

    requirements = parse_requirements(output)

    assert requirements == {
        "anyio": "4.6.2.post1",
        "nonebot2": "2.4.0",
        "nonebug": "0.4.2",
        "pydantic-core": "2.27.0",
        "pydantic": "2.10.0",
    }
