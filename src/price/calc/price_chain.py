"""価格チェーン計算.

T仕切りからHI仕切り→仮上代→ディーラー仕切り→上代を連鎖的に計算する。
VBAの上代等追加()に対応。
"""
from decimal import Decimal

from price.config import PriceChainConfig
from price.models.enums import PartPrefix, classify_prefix
from price.models.price_result import PriceResult
from price.util.rounding import (
    round_half_up_to_10,
    roundup_to_10,
)


class PriceChainCalculator:
    """価格チェーン計算機."""

    def __init__(self, chain_cfg: PriceChainConfig):
        self.cfg = chain_cfg

    def apply(self, result: PriceResult) -> None:
        """PriceResultにHI仕切り～上代を計算して設定する."""
        if result.t_sikiri is None or result.t_sikiri <= 0:
            return

        t = Decimal(str(result.t_sikiri))
        prefix = classify_prefix(result.buhin_bango)

        # HI仕切り = roundup(T仕切 / var1 × var2 × var3, -1)
        result.hi_sikiri = roundup_to_10(
            t / self.cfg.hi_var1 * self.cfg.hi_var2 * self.cfg.hi_var3
        )

        # 仮上代
        if prefix == PartPrefix.FOUR:
            # 4番: roundup(T仕切 / var1 × var2, 0)
            kari = t / self.cfg.kari_var1 * self.cfg.kari_var2
        else:
            # その他: roundup(T仕切 / var1 × var2 × var3 × var4, 0)
            kari = (t / self.cfg.kari_var1
                    * self.cfg.kari_var2
                    * self.cfg.kari_var3
                    * self.cfg.kari_var4)
        result.kari_jyoudai = roundup_to_10(kari)

        # ディーラー仕切り = roundup(HI仕切 × var1_de, -1)
        result.dealer_sikiri = roundup_to_10(
            Decimal(str(result.hi_sikiri)) * self.cfg.dealer_var1
        )

        # 上代 (段階別計算) — Ver.8.0: 四捨五入(10の位)に変更
        kj = Decimal(str(result.kari_jyoudai))
        if kj < self.cfg.jyoudai_band1:
            result.jyoudai = round_half_up_to_10(kj * self.cfg.jyoudai_rate1)
        elif kj < self.cfg.jyoudai_band2:
            result.jyoudai = round_half_up_to_10(kj * self.cfg.jyoudai_rate2)
        else:
            result.jyoudai = round_half_up_to_10(kj * self.cfg.jyoudai_rate3)
