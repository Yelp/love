# -*- coding: utf-8 -*-
import pytest

from loveapp.util.formatting import format_loves


@pytest.mark.parametrize('loves, expected', [
    ([], ([], [])),
    (list(range(5)), (list(range(5)), [])),
    (list(range(31)), (list(range(15)) + [30], list(range(15, 30)))),
])
def test_format_loves(loves, expected):
    assert format_loves(loves) == expected
