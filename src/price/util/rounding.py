"""VBA互換の丸め関数群."""
import math
from decimal import Decimal, ROUND_CEILING


def roundup_to_10(value) -> int:
    """VBAの WorksheetFunction.RoundUp(value, -1) と同等.

    10の位に切り上げる。
    例: 123 → 130, 100 → 100, 101 → 110, -5 → 0
    """
    if value is None or value == 0:
        return 0
    v = Decimal(str(value))
    return int((v / 10).to_integral_value(rounding=ROUND_CEILING) * 10)


def roundup_to_1(value) -> int:
    """VBAの WorksheetFunction.RoundUp(value, 0) と同等.

    1の位に切り上げる。
    例: 1.1 → 2, 1.0 → 1, -0.5 → 0
    """
    if value is None or value == 0:
        return 0
    return int(math.ceil(float(value)))
