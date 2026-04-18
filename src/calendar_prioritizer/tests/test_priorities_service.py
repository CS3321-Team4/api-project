from __future__ import annotations

from calendar_prioritizer.services.priorities import get_color_id_for_priority, get_priority_for_color_id



def test_get_color_id_for_priority_returns_expected_google_color() -> None:
    assert get_color_id_for_priority(1) == '9'
    assert get_color_id_for_priority(2) == '10'
    assert get_color_id_for_priority(3) == '5'
    assert get_color_id_for_priority(4) == '6'
    assert get_color_id_for_priority(5) == '11'



def test_get_priority_for_color_id_returns_none_for_unmapped_color() -> None:
    assert get_priority_for_color_id('1') is None
    assert get_priority_for_color_id(None) is None



def test_get_priority_for_color_id_returns_mapped_priority() -> None:
    assert get_priority_for_color_id('9') == 1
    assert get_priority_for_color_id('10') == 2
    assert get_priority_for_color_id('5') == 3
    assert get_priority_for_color_id('6') == 4
    assert get_priority_for_color_id('11') == 5
