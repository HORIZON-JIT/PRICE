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
        result = PriceResult(buhin_bango="M1234567-00", t_sikiri=5000)
        calc.apply(result)
        assert result.hi_sikiri is not None
        assert result.kari_jyoudai is not None
        assert result.dealer_sikiri is not None
        assert result.jyoudai is not None

    def test_full_chain_4_prefix(self):
        calc = PriceChainCalculator(make_chain_config())
        result = PriceResult(buhin_bango="4037888-00", t_sikiri=3000)
        calc.apply(result)
        # 4番の仮上代は var3, var4 を使わない
        assert result.kari_jyoudai is not None

    def test_no_t_sikiri_skips(self):
        calc = PriceChainCalculator(make_chain_config())
        result = PriceResult(buhin_bango="M1234567-00", t_sikiri=None)
        calc.apply(result)
        assert result.hi_sikiri is None
        assert result.jyoudai is None

    def test_zero_t_sikiri_skips(self):
        calc = PriceChainCalculator(make_chain_config())
        result = PriceResult(buhin_bango="M1234567-00", t_sikiri=0)
        calc.apply(result)
        assert result.hi_sikiri is None
