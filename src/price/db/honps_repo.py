"""HONPSデータベースのバッチ取得メソッド群."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from price.db import honps_queries as Q
from price.db.pool import PoolManager, chunk_list, make_bind_placeholders
from price.models.part import HyotankaRow


class HonpsRepo:
    """HONPSデータベースへのバッチアクセスを提供する."""

    @staticmethod
    def fetch_hyotanka(part_numbers: list[str]) -> dict[str, HyotankaRow]:
        """標準単価を一括取得.

        honps.hv_ma_ta_hyotanka ビュー経由で取得。
        tan_cost_ko がある場合は tan_cost + tan_cost_ko を使用。
        """
        result: dict[str, HyotankaRow] = {}
        with PoolManager.honps_conn() as conn:
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
        return result

    @staticmethod
    def fetch_m_buhin(part_numbers: list[str]) -> dict[str, list[dict]]:
        """HONPS M番部品データを一括取得."""
        result: dict[str, list[dict]] = defaultdict(list)
        with PoolManager.honps_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_M_BUHIN.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        result[row[0]].append({
                            "zuban": row[0],
                            "buhi_mei": row[1] or "",
                            "zairyo_cost": Decimal(str(row[2])) if row[2] is not None else None,
                            "kote_jun": row[3],
                            "koutei": row[4] or "",
                            "ka": row[5] or "",
                            "han": row[6] or "",
                            "gyusya": row[7] or "",
                            "gyusyacost": Decimal(str(row[8])) if row[8] is not None else None,
                            "in_plan_t": Decimal(str(row[9])) if row[9] is not None else None,
                            "lot_inc_t": Decimal(str(row[10])) if row[10] is not None else None,
                            "buh_inc_t": Decimal(str(row[11])) if row[11] is not None else None,
                            "kakou_cycle_t": Decimal(str(row[12])) if row[12] is not None else None,
                            "kijin_flg": row[13] or "",
                        })
        return dict(result)

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
