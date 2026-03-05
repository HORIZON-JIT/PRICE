"""A番（組立品）の計算.

VBAのA番()に対応。
構成部品のH仕切りを合計し、工数×チャージ＋社外組立費を加算。
A番H仕切 = roundup(H仕切合計 / 掛率_A, -1)  ※除算
"""
from decimal import Decimal

from price.calc.base import BaseCalculator
from price.config import RateConfig
from price.models.enums import PartPrefix, classify_prefix
from price.models.manufacturing import AssemblyResult
from price.models.price_result import PriceResult
from price.util.rounding import roundup_to_10


class ACalculator(BaseCalculator):
    """A番（組立品）の計算機."""

    def __init__(self, rate_cfg: RateConfig, sub_calculators: dict | None = None):
        super().__init__(rate_cfg)
        self._sub_calcs = sub_calculators or {}
        self.assembly_details: dict[str, AssemblyResult] = {}

    def _calc_component_h_sikiri(self, buhin_bango: str, std_price: Decimal | None,
                                 first_process: str, naikote_cost: Decimal | None) -> int | None:
        """構成部品のH仕切を計算する."""
        if std_price is None or std_price <= 0:
            return None

        prefix = classify_prefix(buhin_bango)
        mb = self.rate_cfg.m_band

        if prefix == PartPrefix.M:
            # M番: @BYのみなら掛率_4、それ以外は価格帯別
            if first_process in ("@BY", "BY") and (naikote_cost is None or naikote_cost == 0):
                kakeru = self.rate_cfg.rate_4
            elif std_price < mb.band1_threshold:
                kakeru = mb.rate_M1
            elif std_price < mb.band2_threshold:
                kakeru = mb.rate_M2
            else:
                kakeru = mb.rate_M3
            return roundup_to_10(std_price * kakeru)

        elif prefix == PartPrefix.FOUR:
            return roundup_to_10(std_price * self.rate_cfg.rate_4)

        elif prefix in (PartPrefix.E, PartPrefix.F):
            return roundup_to_10(std_price * self.rate_cfg.rate_e)

        elif prefix == PartPrefix.L:
            return roundup_to_10(std_price * self.rate_cfg.rate_l)

        elif prefix == PartPrefix.CV:
            return roundup_to_10(std_price * self.rate_cfg.rate_cv)

        elif prefix == PartPrefix.UM:
            return roundup_to_10(std_price * self.rate_cfg.rate_um)

        elif prefix == PartPrefix.P:
            return roundup_to_10(std_price * self.rate_cfg.rate_p)

        return None

    def calculate(self, part_numbers: list[str], data: dict) -> list[PriceResult]:
        a_components = data.get("a_components", {})
        a_assembly_cost = data.get("a_assembly_cost", {})
        a_assembly_kousuu = data.get("a_assembly_kousuu", {})
        hyotanka = data.get("hyotanka", {})

        results = []
        for pn in part_numbers:
            components = a_components.get(pn, [])
            assembly_cost = a_assembly_cost.get(pn, Decimal("0"))
            kousuu_data = a_assembly_kousuu.get(pn, {})

            # 工数計算 (KIT工程の工数を追加: 241022清野)
            component_count = max(len(components), 5)  # 最低5部品分
            dandori_time = kousuu_data.get("dandori_time", Decimal("0"))
            kousuu_min = dandori_time / 60 + Decimal(str(component_count)) * 2
            kousuu_x_charge = kousuu_min / 60 * self.rate_cfg.charge_rate

            # 構成部品ごとのH仕切り計算
            h_sikiri_total = Decimal("0")
            buhin_total = Decimal("0")
            has_null = False

            # 構成部品の詳細を保持するためコピーを作成
            detail_components = []
            for comp in components:
                comp_ht = hyotanka.get(comp.buhin_bango)
                comp_price = comp_ht.standard_price if comp_ht else None
                comp_first = comp_ht.kote_1 if comp_ht else ""
                comp_naikote = comp_ht.naikote_cost if comp_ht else None

                comp_h_sikiri = self._calc_component_h_sikiri(
                    comp.buhin_bango, comp_price, comp_first, comp_naikote
                )

                if comp_h_sikiri is not None:
                    h_sikiri_total += comp.inzuu * comp_h_sikiri
                else:
                    has_null = True

                if comp_price is not None:
                    buhin_total += comp.inzuu * comp_price

                # 詳細用に構成部品データを記録
                from price.models.manufacturing import AssemblyComponent
                detail_comp = AssemblyComponent(
                    a_bango=pn,
                    buhin_bango=comp.buhin_bango,
                    inzuu=comp.inzuu,
                    buhin_name=comp.buhin_name,
                    tanka=comp_price,
                    h_sikiri=comp_h_sikiri,
                    h_sikiri_x_inzuu=int(comp.inzuu * comp_h_sikiri) if comp_h_sikiri else None,
                )
                detail_components.append(detail_comp)

            # A番H仕切合計 = Σ(員数×H仕切) + 工数×チャージ + 社外組立費
            h_sikiri_sum = h_sikiri_total + kousuu_x_charge + assembly_cost

            # A番H仕切 = roundup(H仕切合計 / 掛率_A, -1)  ※除算
            a_h_sikiri = None
            if h_sikiri_sum > 0:
                a_h_sikiri = roundup_to_10(h_sikiri_sum / self.rate_cfg.rate_a)

            # 原価合計 = 部品合計 + 工数×チャージ + 社外組立費
            genka_total = buhin_total + kousuu_x_charge + assembly_cost

            # A番詳細データを保存
            assembly_place = kousuu_data.get("line_cd", "")
            self.assembly_details[pn] = AssemblyResult(
                a_bango=pn,
                components=detail_components,
                buhin_total=buhin_total,
                h_sikiri_total=int(h_sikiri_total),
                kousuu=kousuu_min,
                kousuu_x_charge=kousuu_x_charge,
                kumitate_gaichuhi=assembly_cost,
                genka_total=genka_total,
                h_sikiri_sum=int(h_sikiri_sum) if h_sikiri_sum > 0 else 0,
                assembly_place=assembly_place,
                has_null_data=has_null,
            )

            results.append(PriceResult(
                buhin_bango=pn,
                standard_price=h_sikiri_sum if h_sikiri_sum > 0 else None,
                h_sikiri=a_h_sikiri,
                kakeru=self.rate_cfg.rate_a,
                has_null_data=has_null,
            ))
        return results
