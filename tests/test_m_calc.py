"""M番計算のテスト."""
from decimal import Decimal

from price.calc.m_calc import MCalculator
from price.models.part import HyotankaRow


class TestMCalculator:
    """M番の掛率選択とT仕切り計算を検証."""

    def test_band1_rate(self, sample_rate_config):
        calc = MCalculator(sample_rate_config)
        data = {
            "hyotanka": {
                "M1234567-00": HyotankaRow(
                    hinban="M1234567-00",
                    standard_price=Decimal("3000"),
                    kote_1="PNC",
                ),
            },
        }
        results = calc.calculate(["M1234567-00"], data)
        assert len(results) == 1
        r = results[0]
        # 3000 < 5000(band1) → rate_M1=1.5
        # roundup(3000 * 1.5, -1) = roundup(4500, -1) = 4500
        assert r.t_sikiri == 4500
        assert r.kakeru == Decimal("1.5")

    def test_band2_rate(self, sample_rate_config):
        calc = MCalculator(sample_rate_config)
        data = {
            "hyotanka": {
                "M1234567-00": HyotankaRow(
                    hinban="M1234567-00",
                    standard_price=Decimal("10000"),
                    kote_1="TNC",
                ),
            },
        }
        results = calc.calculate(["M1234567-00"], data)
        r = results[0]
        # 5000 <= 10000 < 20000 → rate_M2=1.4
        # roundup(10000 * 1.4, -1) = 14000
        assert r.t_sikiri == 14000

    def test_band3_rate(self, sample_rate_config):
        calc = MCalculator(sample_rate_config)
        data = {
            "hyotanka": {
                "M1234567-00": HyotankaRow(
                    hinban="M1234567-00",
                    standard_price=Decimal("25000"),
                    kote_1="MOL",
                ),
            },
        }
        results = calc.calculate(["M1234567-00"], data)
        r = results[0]
        # 25000 >= 20000 → rate_M3=1.3
        # roundup(25000 * 1.3, -1) = 32500 → 32500
        assert r.t_sikiri == 32500

    def test_by_only_uses_rate_4(self, sample_rate_config):
        """第1工程が@BYで内作コスト0の場合は掛率_4を使用."""
        calc = MCalculator(sample_rate_config)
        data = {
            "hyotanka": {
                "M1234567-00": HyotankaRow(
                    hinban="M1234567-00",
                    standard_price=Decimal("3000"),
                    naikote_cost=Decimal("0"),
                    kote_1="@BY",
                ),
            },
        }
        results = calc.calculate(["M1234567-00"], data)
        r = results[0]
        # @BY + naikote=0 → rate_4=1.2
        # roundup(3000 * 1.2, -1) = 3600
        assert r.t_sikiri == 3600
        assert r.kakeru == Decimal("1.2")

    def test_null_price(self, sample_rate_config):
        calc = MCalculator(sample_rate_config)
        data = {"hyotanka": {}}
        results = calc.calculate(["M9999999-00"], data)
        r = results[0]
        assert r.t_sikiri is None
        assert r.has_null_data is True
