from __future__ import annotations

PRIORITY_TO_COLOR_ID: dict[int, str] = {
    1: '9',
    2: '10',
    3: '5',
    4: '6',
    5: '11',
}

COLOR_ID_TO_PRIORITY: dict[str, int] = {
    color_id: priority for priority, color_id in PRIORITY_TO_COLOR_ID.items()
}


def get_color_id_for_priority(priority: int) -> str:
    return PRIORITY_TO_COLOR_ID[priority]



def get_priority_for_color_id(color_id: str | None) -> int | None:
    if color_id is None:
        return None

    return COLOR_ID_TO_PRIORITY.get(color_id)
