"""HONPSデータベースのバッチ取得メソッド群."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from price.db import honps_queries as Q
from price.db.pool import PoolManager, chunk_list, make_bind_placeholders
from price.models.manufacturing import MDetail, MProcessRow
from price.models.part import HyotankaRow


class HonpsRepo:
    """HONPSデータベースへのバッチアクセスを提供する."""

    @staticmethod
    def fetch_hyotanka(part_numbers: list[str]) -> dict[str, HyotankaRow]:
        """標準単価を一括取得.

        honps.hv_ma_ta_hyotanka ビュー経由で取得。
        tan_cost_ko がある場合は tan_cost + tan_cost_ko を使用。
        ビューで取得できなかった品番は ta_hyotanka (ベーステーブル) からフォールバック取得する。
        """
        result: dict[str, HyotankaRow] = {}
        with PoolManager.honps_conn() as conn:
            # 1. ビュー (hv_ma_ta_hyotanka) から取得
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_HYOTANKA.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        ht = HyotankaRow(
                            hinban=row[0],
                            standard_price=Decimal(str(row[1])) if row[1] is not None else None,
                            naikote_cost=Decimal(str(row[2])) if row[2] is not None else None,
                            gaikote_cost=Decimal(str(row[3])) if row[3] is not None else None,
                            konyu_cost=Decimal(str(row[4])) if row[4] is not None else None,
                            tan_cost_ko=Decimal(str(row[5])) if row[5] is not None else None,
                            kote_1=row[6] or "",
                        )
                        result[ht.hinban] = ht

            # 2. ビューで取得できなかった品番を ta_hyotanka からフォールバック取得
            missing = [pn for pn in part_numbers
                       if pn not in result or result[pn].standard_price is None]
            if missing:
                for chunk in chunk_list(missing):
                    ph = make_bind_placeholders(len(chunk))
                    sql = Q.FETCH_TA_HYOTANKA.format(placeholders=ph)
                    with conn.cursor() as cur:
                        cur.execute(sql, chunk)
                        for row in cur:
                            hinban, tan_cost = row[0], row[1]
                            if tan_cost is not None:
                                if hinban in result:
                                    result[hinban].standard_price = Decimal(str(tan_cost))
                                else:
                                    result[hinban] = HyotankaRow(
                                        hinban=hinban,
                                        standard_price=Decimal(str(tan_cost)),
                                    )
        return result

    @staticmethod
    def fetch_m_buhin(part_numbers: list[str]) -> dict[str, MDetail]:
        """HONPS M番部品データを一括取得."""
        raw: dict[str, list[MProcessRow]] = defaultdict(list)
        names: dict[str, str] = {}
        with PoolManager.honps_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_M_BUHIN.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        zuban = row[0]
                        names.setdefault(zuban, row[1] or "")
                        raw[zuban].append(MProcessRow(
                            kote_jun=row[3],
                            koutei=row[4] or "",
                            ka=row[5] or "",
                            han=row[6] or "",
                            gyusya=row[7] or "",
                            gyusyacost=Decimal(str(row[8])) if row[8] is not None else None,
                            in_plan_t=Decimal(str(row[9])) if row[9] is not None else None,
                            lot_inc_t=Decimal(str(row[10])) if row[10] is not None else None,
                            buh_inc_t=Decimal(str(row[11])) if row[11] is not None else None,
                            kakou_cycle_t=Decimal(str(row[12])) if row[12] is not None else None,
                            kijin_flg=row[13] or "",
                            zairyo_cost=Decimal(str(row[2])) if row[2] is not None else None,
                        ))
        return {
            zuban: MDetail(zuban=zuban, buhi_mei=names.get(zuban, ""), processes=procs)
            for zuban, procs in raw.items()
        }

    @staticmethod
    def fetch_yosekose(part_numbers: list[str]) -> dict[str, list[dict]]:
        """HONPS 親子関係を一括取得."""
        result: dict[str, list[dict]] = defaultdict(list)
        with PoolManager.honps_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_YOSEKOSE.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        result[row[0]].append({
                            "ko_zuban": row[1],
                            "inzu": Decimal(str(row[2])) if row[2] is not None else Decimal("1"),
                        })
        return dict(result)

    @staticmethod
    def fetch_buhinhyo(part_numbers: list[str]) -> dict[str, Decimal]:
        """HONPS 購入品価格を一括取得."""
        result: dict[str, Decimal] = {}
        with PoolManager.honps_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_BUHINHYO.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        if row[1] is not None:
                            result[row[0]] = Decimal(str(row[1]))
        return result

    @staticmethod
    def fetch_pa_patmst(part_numbers: list[str]) -> dict[str, dict]:
        """HONPS 組立工数・場所を一括取得."""
        result: dict[str, dict] = {}
        with PoolManager.honps_conn() as conn:
            # 工数
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_PA_PATMST_TIME.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        result.setdefault(row[0], {})["hyojyun_time"] = (
                            Decimal(str(row[1])) if row[1] is not None else Decimal("0")
                        )
            # 場所
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_PA_PATMST_PLACE.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        result.setdefault(row[0], {})["kumi_place"] = row[1] or ""
        return result
