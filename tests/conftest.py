"""テスト用フィクスチャ."""
import pytest
from decimal import Decimal

from price.config import RateConfig, MBandConfig, PriceChainConfig


@pytest.fixture
def sample_rate_config():
    """テスト用の掛率設定."""
    return RateConfig(
        m_band=MBandConfig(
            band1_threshold=Decimal("5000"),
            band2_threshold=Decimal("20000"),
            band3_threshold=Decimal("20000"),
            rate_M1=Decimal("1.5"),
            rate_M2=Decimal("1.4"),
            rate_M3=Decimal("1.3"),
        ),
        rate_4=Decimal("1.2"),
        rate_e=Decimal("1.35"),
        rate_a=Decimal("0.9"),
        rate_l=Decimal("1.25"),
        rate_cv=Decimal("1.3"),
        rate_um=Decimal("1.0"),
        rate_p=Decimal("1.15"),
        up_rate=Decimal("3600"),
        charge_rate=Decimal("5000"),
        price_chain=PriceChainConfig(
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
        ),
    )
