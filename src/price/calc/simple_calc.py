"""E/F/L/CV/P番の単純掛率計算.

T仕切 = roundup(標準単価 × 掛率, -1)
"""
from decimal import Decimal

from price.calc.base import BaseCalculator
from price.config import RateConfig
from price.models.enums import PartPrefix
from price.models.price_result import PriceResult
from price.util.rounding import roundup_to_10


class SimpleRateCalculator(BaseCalculator):
    """単純な掛率適用で計算するプレフィックス群."""

    def __init__(self, rate_cfg: RateConfig, prefix: PartPrefix):
        super().__init__(rate_cfg)
        self.prefix = prefix
        self._rate = self._get_rate(prefix)

    def _get_rate(self, prefix: PartPrefix) -> Decimal:
        mapping = {
            PartPrefix.E: self.rate_cfg.rate_e,
            PartPrefix.F: self.rate_cfg.rate_e,  # F番はE番と同じ掛率
            PartPrefix.L: self.rate_cfg.rate_l,
            PartPrefix.CV: self.rate_cfg.rate_cv,
            PartPrefix.UM: self.rate_cfg.rate_um,
            PartPrefix.P: self.rate_cfg.rate_p,
        }
        return mapping[prefix]

    def calculate(self, part_numbers: list[str], data: dict) -> list[PriceResult]:
        hyotanka = data.get("hyotanka", {})
        results = []
        for pn in part_numbers:
            ht = hyotanka.get(pn)
            std_price = ht.standard_price if ht else None

            t_sikiri = None
            if std_price is not None and std_price > 0:
                t_sikiri = roundup_to_10(std_price * self._rate)

            results.append(PriceResult(
                buhin_bango=pn,
                standard_price=std_price,
                t_sikiri=t_sikiri,
                kakeru=self._rate,
                naikote_cost=ht.naikote_cost if ht else None,
                gaikote_cost=ht.gaikote_cost if ht else None,
                konyu_cost=ht.konyu_cost if ht else None,
                first_process=ht.kote_1 if ht else "",
                has_null_data=(std_price is None or std_price == 0),
            ))
        return results
