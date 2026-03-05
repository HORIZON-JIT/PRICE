"""4番（購入品）の計算.

T仕切 = roundup(購入単価 × 掛率_4, -1)
外貨の場合は為替レートで変換後に計算。
"""
from decimal import Decimal

from price.calc.base import BaseCalculator
from price.models.price_result import PriceResult
from price.util.currency import convert_to_jpy
from price.util.rounding import roundup_to_10


class PurchasedCalculator(BaseCalculator):
    """4番（購入品）の計算機."""

    def calculate(self, part_numbers: list[str], data: dict) -> list[PriceResult]:
        kakakuhyou = data.get("kakakuhyou", {})
        fx_rates = data.get("fx_rates", {})
        results = []

        for pn in part_numbers:
            kk = kakakuhyou.get(pn)
            tanka = kk.tanka if kk else None
            currency = kk.tori_tuuka_tani_kbn if kk else "JPY"

            # 外貨の場合は日本円に変換
            if tanka is not None and currency != "JPY" and currency:
                rate = fx_rates.get(currency)
                if rate is not None:
                    tanka = convert_to_jpy(tanka, rate)

            t_sikiri = None
            if tanka is not None and tanka > 0:
                t_sikiri = roundup_to_10(tanka * self.rate_cfg.rate_4)

            results.append(PriceResult(
                buhin_bango=pn,
                standard_price=tanka,
                t_sikiri=t_sikiri,
                kakeru=self.rate_cfg.rate_4,
                has_null_data=(tanka is None or tanka == 0),
            ))
        return results
