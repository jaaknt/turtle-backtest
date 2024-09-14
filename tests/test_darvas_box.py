import pytest
import pandas as pd
from turtle.strategy.darvas_box import DarvasBoxStrategy

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources")


def test_check_local_max():
    series = pd.Series([1, 2, 3, 10, 3, 2, 1])
    assert DarvasBoxStrategy.check_local_max(3, series, 3, 3) is True
    assert DarvasBoxStrategy.check_local_max(2, series, 3, 3) is False


def test_check_local_min():
    series = pd.Series([10, 9, 8, 1, 8, 9, 10])
    assert DarvasBoxStrategy.check_local_min(3, series, 3) is True
    assert DarvasBoxStrategy.check_local_min(2, series, 3) is False
