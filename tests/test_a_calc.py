"""A番計算のテスト."""
from decimal import Decimal

from price.calc.a_calc import ACalculator
from price.models.manufacturing import AssemblyComponent
from price.models.part import HyotankaRow


class TestACalculator:

    def test_basic_assembly(self, sample_rate_config):
        calc = ACalculator(sample_rate_config)
        data = {
            "a_components": {
                "A1234567-00": [
                    AssemblyComponent(
                        a_bango="A1234567-00",
                        buhin_bango="M1111111-00",
                        inzuu=Decimal("2"),
                    ),
                    AssemblyComponent(
                        a_bango="A1234567-00",
                        buhin_bango="4222222-00",
                        inzuu=Decimal("1"),
                    ),
                ],
            },
            "a_assembly_cost": {"A1234567-00": Decimal("500")},
            "a_assembly_kousuu": {
                "A1234567-00": {
                    "dandori_time": Decimal("60"),
                    "naigaisaku_kbn": "PC001",
                },
            },
            "hyotanka": {
                "M1111111-00": HyotankaRow(
                    hinban="M1111111-00",
                    standard_price=Decimal("3000"),
                    kote_1="PNC",
                ),
                "4222222-00": HyotankaRow(
                    hinban="4222222-00",
                    standard_price=Decimal("1000"),
                ),
            },
        }
        results = calc.calculate(["A1234567-00"], data)
        assert len(results) == 1
        r = results[0]
        assert r.t_sikiri is not None
        assert r.t_sikiri > 0
        # A番は除算: roundup(total / 0.9, -1)
        assert r.kakeru == Decimal("0.9")

    def test_empty_assembly(self, sample_rate_config):
        calc = ACalculator(sample_rate_config)
        data = {
            "a_components": {},
            "a_assembly_cost": {},
            "a_assembly_kousuu": {},
            "hyotanka": {},
        }
        results = calc.calculate(["A9999999-00"], data)
        assert len(results) == 1
        # 構成部品なし → 工数×チャージのみ
        r = results[0]
        # dandori=0, component_count=5(最低) → kousuu = 0/60 + 5*2 = 10min
        # kousuu_x_charge = 10/60 * 5000 ≈ 833.33
        # assembly_cost = 0
        # total ≈ 833.33
        # roundup(833.33 / 0.9, -1) = roundup(925.93, -1) = 930
        assert r.t_sikiri is not None
