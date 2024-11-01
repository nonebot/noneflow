from nonebot.params import Depends

from src.plugins.github.depends import get_labels_name


def check_labels(labels: list[str] | str):
    """检查标签是否存在"""
    if isinstance(labels, str):
        labels = [labels]

    async def _check_labels(
        has_labels: list[str] = Depends(get_labels_name),
    ) -> bool:
        return any(label in has_labels for label in labels)

    return Depends(_check_labels)
