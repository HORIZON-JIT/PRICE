"""部品プレフィックスで計算機を振り分けるディスパッチャ.

VBAの一括()に対応する中核モジュール。
"""
from collections import defaultdict

from price.calc.a_calc import ACalculator
from price.calc.base import BaseCalculator
from price.calc.m_calc import MCalculator
from price.calc.price_chain import PriceChainCalculator
from price.calc.purchased_calc import PurchasedCalculator
from price.calc.simple_calc import SimpleRateCalculator
from price.config import RateConfig
from price.models.enums import PartPrefix, classify_prefix
from price.models.manufacturing import AssemblyResult
from price.models.price_result import PriceResult


class PriceDispatcher:
    """部品番号のプレフィックスに基づいて適切な計算機にルーティングする."""

    def __init__(self, rate_cfg: RateConfig):
        self._a_calc = ACalculator(rate_cfg)
        self._calculators: dict[PartPrefix, BaseCalculator] = {
            PartPrefix.M: MCalculator(rate_cfg),
            PartPrefix.FOUR: PurchasedCalculator(rate_cfg),
            PartPrefix.A: self._a_calc,
            PartPrefix.E: SimpleRateCalculator(rate_cfg, PartPrefix.E),
            PartPrefix.F: SimpleRateCalculator(rate_cfg, PartPrefix.F),
            PartPrefix.L: SimpleRateCalculator(rate_cfg, PartPrefix.L),
            PartPrefix.CV: SimpleRateCalculator(rate_cfg, PartPrefix.CV),
            PartPrefix.UM: SimpleRateCalculator(rate_cfg, PartPrefix.UM),
            PartPrefix.P: SimpleRateCalculator(rate_cfg, PartPrefix.P),
        }
        self._price_chain = PriceChainCalculator(rate_cfg.price_chain)

    def calculate_batch(
        self,
        part_numbers: list[str],
        data: dict,
    ) -> list[PriceResult]:
        """全部品のT仕切り〜上代を一括計算する.

        Args:
            part_numbers: 全部品番号リスト
            data: プリフェッチ済みデータ辞書。キー:
                - hyotanka: {部品番号: HyotankaRow}
                - kakakuhyou: {部品番号: KakakuRow}
                - fx_rates: {通貨コード: Decimal}
                - a_components: {A番: [AssemblyComponent]}
                - a_assembly_cost: {A番: Decimal}
                - a_assembly_kousuu: {A番: dict}
                - shohin_buhin: {部品番号: ShohinBuhin}
                - buhin_kubun: {部品番号: [区分名]}

        Returns:
            全部品の計算結果リスト
        """
        # プレフィックスでグルーピング
        groups: dict[PartPrefix, list[str]] = defaultdict(list)
        errors: list[PriceResult] = []

        for pn in part_numbers:
            try:
                prefix = classify_prefix(pn)
                groups[prefix].append(pn)
            except ValueError:
                errors.append(PriceResult(
                    buhin_bango=pn,
                    has_null_data=True,
                ))

        # 各グループを対応する計算機で処理
        results: list[PriceResult] = []
        for prefix, pns in groups.items():
            calc = self._calculators.get(prefix)
            if calc is None:
                for pn in pns:
                    errors.append(PriceResult(buhin_bango=pn, has_null_data=True))
                continue
            group_results = calc.calculate(pns, data)
            results.extend(group_results)

        results.extend(errors)

        # 価格チェーン適用 (HI仕切り→仮上代→D仕切り→上代)
        for r in results:
            self._price_chain.apply(r)

        # ECO H仕切りとの比較チェック
        shohin_buhin = data.get("shohin_buhin", {})
        h_sikiri_adj = data.get("h_sikiri_adjustment", None)
        for r in results:
            sb = shohin_buhin.get(r.buhin_bango)
            if sb and sb.h_sikiri is not None:
                r.h_sikiri_eco = sb.h_sikiri
                if h_sikiri_adj is not None and r.t_sikiri is not None:
                    from decimal import Decimal
                    adjusted = int(sb.h_sikiri * Decimal(str(h_sikiri_adj)))
                    r.h_sikiri_eco_adjusted = adjusted
                    if r.t_sikiri >= adjusted:
                        r.price_comparison_flag = "高"
                    elif r.t_sikiri < int(sb.h_sikiri):
                        r.price_comparison_flag = "安"

        # 部品区分の追加
        buhin_kubun = data.get("buhin_kubun", {})
        for r in results:
            kubuns = buhin_kubun.get(r.buhin_bango, [])
            r.buhin_kubun = "_".join(kubuns)

        # 入力順に並べ替え
        order = {pn: i for i, pn in enumerate(part_numbers)}
        results.sort(key=lambda r: order.get(r.buhin_bango, len(part_numbers)))

        return results

    def get_assembly_details(self) -> dict[str, AssemblyResult]:
        """A番の構成部品詳細データを返す."""
        return self._a_calc.assembly_details
