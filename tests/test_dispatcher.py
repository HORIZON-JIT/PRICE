"""ディスパッチャのテスト."""
from decimal import Decimal

from price.calc.dispatcher import PriceDispatcher
from price.models.part import HyotankaRow, KakakuRow


class TestPriceDispatcher:

    def test_routes_to_correct_calculator(self, sample_rate_config):
        dispatcher = PriceDispatcher(sample_rate_config)
        data = {
            "hyotanka": {
                "M1234567-00": HyotankaRow(
                    hinban="M1234567-00",
                    standard_price=Decimal("3000"),
                    kote_1="PNC",
                ),
                "E1234567-00": HyotankaRow(
                    hinban="E1234567-00",
                    standard_price=Decimal("2000"),
                ),
                "L1234567-00": HyotankaRow(
                    hinban="L1234567-00",
                    standard_price=Decimal("1500"),
                ),
            },
            "kakakuhyou": {
                "4037888-00": KakakuRow(
                    hinban="4037888-00",
                    tanka=Decimal("500"),
                ),
            },
            "fx_rates": {},
            "shohin_buhin": {},
            "buhin_kubun": {},
            "a_components": {},
            "a_assembly_cost": {},
            "a_assembly_kousuu": {},
        }
        parts = ["M1234567-00", "4037888-00", "E1234567-00", "L1234567-00"]
        results = dispatcher.calculate_batch(parts, data)

        assert len(results) == 4
        # 入力順に並んでいることを確認
        assert results[0].buhin_bango == "M1234567-00"
        assert results[1].buhin_bango == "4037888-00"
        assert results[2].buhin_bango == "E1234567-00"
        assert results[3].buhin_bango == "L1234567-00"
        # 全てH仕切りが計算されていることを確認
        for r in results:
            assert r.h_sikiri is not None
            assert r.h_sikiri > 0

    def test_unknown_prefix_handled(self, sample_rate_config):
        dispatcher = PriceDispatcher(sample_rate_config)
        data = {"hyotanka": {}, "shohin_buhin": {}, "buhin_kubun": {}}
        results = dispatcher.calculate_batch(["X9999-00"], data)
        assert len(results) == 1
        assert results[0].has_null_data is True

    def test_preserves_input_order(self, sample_rate_config):
        dispatcher = PriceDispatcher(sample_rate_config)
        data = {
            "hyotanka": {
                f"M000000{i}-00": HyotankaRow(
                    hinban=f"M000000{i}-00",
                    standard_price=Decimal("1000"),
                )
                for i in range(5)
            },
            "shohin_buhin": {},
            "buhin_kubun": {},
        }
        parts = [f"M000000{i}-00" for i in range(5)]
        results = dispatcher.calculate_batch(parts, data)
        for i, r in enumerate(results):
            assert r.buhin_bango == parts[i]
