from src.providers.utils import load_json_from_web


def get_user_id(name: str) -> int:
    """获取用户信息"""
    data = load_json_from_web(f"https://api.github.com/users/{name}")
    return data["id"]
