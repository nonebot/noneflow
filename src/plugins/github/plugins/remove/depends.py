from nonebot.params import Depends

from src.plugins.github.depends import get_labels
from src.plugins.github.typing import LabelsItems


def get_name_by_labels(
    labels: LabelsItems = Depends(get_labels),
) -> list[str]:
    """通过标签获取名称"""
    label_names: list[str] = []
    if not labels:
        return label_names

    for label in labels:
        if label.name:
            label_names.append(label.name)
    return label_names


def check_labels(labels: list[str] | str):
    """检查标签是否存在"""
    if isinstance(labels, str):
        labels = [labels]

    async def _check_labels(
        has_labels: list[str] = Depends(get_name_by_labels),
    ) -> bool:
        return all(label in has_labels for label in labels)

    return Depends(_check_labels)
