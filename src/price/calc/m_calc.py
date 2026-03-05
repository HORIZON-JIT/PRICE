"""M番（製造部品）の計算.

VBAのM番_計算に対応。標準単価に対して価格帯別の掛率を適用。
特殊条件: 第1工程が@BYのみの場合は掛率_4を使用。

H仕切 = roundup(標準単価 × 掛率_M[tier], -1)
"""
from decimal import Decimal

from price.calc.base import BaseCalculator
from price.models.price_result import PriceResult
from price.util.rounding import roundup_to_10


class MCalculator(BaseCalculator):
    """M番（製造部品）の計算機."""

    def __init__(self, rate_cfg):
        super().__init__(rate_cfg)
        self.m_details: dict = {}

    def _select_rate(self, std_price: Decimal, first_process: str,
                     naikote_cost: Decimal | None) -> Decimal:
        """価格帯に基づいて掛率を選択する.

        VBAロジック:
        - 第1工程が@BYまたはBYで内作コストが0の場合 → 掛率_4
        - それ以外は価格帯で M1/M2/M3 を選択
        """
        # @BYのみの特殊条件 (25/2/20清野)
        if first_process in ("@BY", "BY"):
            if naikote_cost is None or naikote_cost == 0:
                return self.rate_cfg.rate_4

        mb = self.rate_cfg.m_band
        if std_price < mb.band1_threshold:
            return mb.rate_M1
        elif std_price < mb.band2_threshold:
            return mb.rate_M2
        else:
            return mb.rate_M3

    def calculate(self, part_numbers: list[str], data: dict) -> list[PriceResult]:
        hyotanka = data.get("hyotanka", {})
        m_buhin = data.get("m_buhin", {})
        results = []

        # M番工程詳細を保持
        for pn in part_numbers:
            if pn in m_buhin:
                self.m_details[pn] = m_buhin[pn]

        for pn in part_numbers:
            ht = hyotanka.get(pn)
            std_price = ht.standard_price if ht else None
            first_process = ht.kote_1 if ht else ""
            naikote_cost = ht.naikote_cost if ht else None

            h_sikiri = None
            kakeru = None
            if std_price is not None and std_price > 0:
                kakeru = self._select_rate(std_price, first_process, naikote_cost)
                h_sikiri = roundup_to_10(std_price * kakeru)

            results.append(PriceResult(
                buhin_bango=pn,
                standard_price=std_price,
                h_sikiri=h_sikiri,
                kakeru=kakeru,
                naikote_cost=naikote_cost,
                gaikote_cost=ht.gaikote_cost if ht else None,
                konyu_cost=ht.konyu_cost if ht else None,
                first_process=first_process,
                has_null_data=(std_price is None or std_price == 0),
            ))
        return results
