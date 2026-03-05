"""丸め関数のテスト."""
from decimal import Decimal

from price.util.rounding import roundup_to_10, roundup_to_1


class TestRoundupTo10:
    """VBAの WorksheetFunction.RoundUp(value, -1) と同等の動作を検証."""

    def test_exact_multiple(self):
        assert roundup_to_10(100) == 100
        assert roundup_to_10(200) == 200

    def test_round_up(self):
        assert roundup_to_10(101) == 110
        assert roundup_to_10(123) == 130
        assert roundup_to_10(199) == 200

    def test_zero(self):
        assert roundup_to_10(0) == 0

    def test_none(self):
        assert roundup_to_10(None) == 0

    def test_small_number(self):
        assert roundup_to_10(1) == 10
        assert roundup_to_10(9) == 10

    def test_decimal_input(self):
        assert roundup_to_10(Decimal("123.45")) == 130
        assert roundup_to_10(Decimal("100.01")) == 110

    def test_float_input(self):
        assert roundup_to_10(123.45) == 130

    def test_large_number(self):
        assert roundup_to_10(12345) == 12350
        assert roundup_to_10(99999) == 100000


class TestRoundupTo1:
    """VBAの WorksheetFunction.RoundUp(value, 0) と同等の動作を検証."""

    def test_integer(self):
        assert roundup_to_1(5) == 5

    def test_round_up(self):
        assert roundup_to_1(1.1) == 2
        assert roundup_to_1(1.9) == 2
        assert roundup_to_1(0.1) == 1

    def test_exact(self):
        assert roundup_to_1(1.0) == 1

    def test_zero(self):
        assert roundup_to_1(0) == 0

    def test_none(self):
        assert roundup_to_1(None) == 0
