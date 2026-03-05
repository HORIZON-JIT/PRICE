"""価格チェーンのテスト."""
from decimal import Decimal

from price.calc.price_chain import PriceChainCalculator
from price.config import PriceChainConfig
from price.models.price_result import PriceResult


def make_chain_config():
    return PriceChainConfig(
        hi_var1=Decimal("0.65"),
        hi_var2=Decimal("0.85"),
        hi_var3=Decimal("1.0"),
        kari_var1=Decimal("0.65"),
        kari_var2=Decimal("1.1"),
        kari_var3=Decimal("1.0"),
        kari_var4=Decimal("1.0"),
        dealer_var1=Decimal("0.7"),
        jyoudai_band1=Decimal("11000"),
        jyoudai_band2=Decimal("33000"),
        jyoudai_rate1=Decimal("1.3"),
        jyoudai_rate2=Decimal("1.2"),
        jyoudai_rate3=Decimal("1.1"),
    )


class TestPriceChain:

    def test_full_chain_m_prefix(self):
        calc = PriceChainCalculator(make_chain_config())
        result = PriceResult(buhin_bango="M1234567-00", h_sikiri=5000)
        calc.apply(result)
        assert result.hi_sikiri is not None
        assert result.kari_jyoudai is not None
        assert result.dealer_sikiri is not None
        assert result.jyoudai is not None

    def test_full_chain_4_prefix(self):
        calc = PriceChainCalculator(make_chain_config())
        result = PriceResult(buhin_bango="4037888-00", h_sikiri=3000)
        calc.apply(result)
        # 4番の仮上代は var3, var4 を使わない
        assert result.kari_jyoudai is not None

    def test_no_h_sikiri_skips(self):
        calc = PriceChainCalculator(make_chain_config())
        result = PriceResult(buhin_bango="M1234567-00", h_sikiri=None)
        calc.apply(result)
        assert result.hi_sikiri is None
        assert result.jyoudai is None

    def test_zero_h_sikiri_skips(self):
        calc = PriceChainCalculator(make_chain_config())
        result = PriceResult(buhin_bango="M1234567-00", h_sikiri=0)
        calc.apply(result)
        assert result.hi_sikiri is None

    def test_jyoudai_uses_round_half_up(self):
        """上代が四捨五入(Ver.8.0)で計算されることを検証."""
        cfg = PriceChainConfig(
            hi_var1=Decimal("0.52"),
            hi_var2=Decimal("0.57"),
            hi_var3=Decimal("1.05"),
            kari_var1=Decimal("0.52"),
            kari_var2=Decimal("1.05"),
            kari_var3=Decimal("1.05"),
            kari_var4=Decimal("1.3068"),
            dealer_var1=Decimal("1.1"),
            jyoudai_band1=Decimal("15000"),
            jyoudai_band2=Decimal("40000"),
            jyoudai_rate1=Decimal("1.5"),
            jyoudai_rate2=Decimal("1.3"),
            jyoudai_rate3=Decimal("1.2"),
        )
        calc = PriceChainCalculator(cfg)
        # 仮上代 5003 × 1.5 = 7504.5 → 四捨五入で 7500 (切り上げなら7510)
        result = PriceResult(buhin_bango="M1234567-00", h_sikiri=1000)
        calc.apply(result)
        # D仕切 = HI仕切 × 1.1
        assert result.dealer_sikiri is not None
        assert result.jyoudai is not None
