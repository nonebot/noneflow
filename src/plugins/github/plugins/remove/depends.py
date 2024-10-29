from nonebot.params import Depends

from src.plugins.github.depends import get_name_by_labels


def check_labels(labels: list[str] | str):
    """检查标签是否存在"""
    if isinstance(labels, str):
        labels = [labels]

    async def _check_labels(
        has_labels: list[str] = Depends(get_name_by_labels),
    ) -> bool:
        return all(label in has_labels for label in labels)

    return Depends(_check_labels)
