"""ECOデータベースのバッチ取得メソッド群.

VBAでは1行ずつSQLを発行していたが、ここではIN句で一括取得する。
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from price.db import eco_queries as Q
from price.db.pool import PoolManager, chunk_list, make_bind_placeholders
from price.models.manufacturing import AssemblyComponent, SeizouRow
from price.models.part import HyotankaRow, KakakuRow, ParentChild, ShohinBuhin


class EcoRepo:
    """ECOデータベースへのバッチアクセスを提供する."""

    @staticmethod
    def fetch_shohin_buhin(part_numbers: list[str]) -> dict[str, ShohinBuhin]:
        """商品部品マスタから一括取得."""
        result: dict[str, ShohinBuhin] = {}
        with PoolManager.eco_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_SHOHIN_BUHIN.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        sb = ShohinBuhin(
                            shohin_buhin_cd=row[0],
                            h_sikiri=Decimal(str(row[1])) if row[1] is not None else None,
                            i_sikiri=Decimal(str(row[2])) if row[2] is not None else None,
                            d_sikiri=Decimal(str(row[3])) if row[3] is not None else None,
                            jyoudai=Decimal(str(row[4])) if row[4] is not None else None,
                            jp_buhi_name=row[5] or "",
                            buhinkubun=row[6] or "",
                            zaiko_cd=row[7] or "",
                        )
                        result[sb.shohin_buhin_cd] = sb
        return result

    @staticmethod
    def fetch_seizou_view(part_numbers: list[str]) -> dict[str, list[SeizouRow]]:
        """製造ビューから工程データを一括取得."""
        result: dict[str, list[SeizouRow]] = defaultdict(list)
        with PoolManager.eco_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_SEIZOU_VIEW.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        sr = SeizouRow(
                            oya_hinban=row[0],
                            hm_nm_1=row[1] or "",
                            zairyo_cost=Decimal(str(row[2])) if row[2] is not None else None,
                            naigaisaku_kbn=row[3] or "",
                            ko_hinban=row[4] or "",
                            torisaki_cd=row[5] or "",
                            gaichu_cost=Decimal(str(row[6])) if row[6] is not None else None,
                            dandori_time=Decimal(str(row[7])) if row[7] is not None else None,
                            lot_futai=Decimal(str(row[8])) if row[8] is not None else None,
                            buhin_futai=Decimal(str(row[9])) if row[9] is not None else None,
                            machining_cycle=Decimal(str(row[10])) if row[10] is not None else None,
                            kizin_kbn=row[11] or "",
                            line_no=str(row[12]) if row[12] is not None else "",
                            oya_line_no=str(row[13]) if row[13] is not None else "",
                        )
                        result[sr.oya_hinban].append(sr)
        return dict(result)

    @staticmethod
    def fetch_parent_child(part_numbers: list[str]) -> dict[str, list[ParentChild]]:
        """親子関係を一括取得."""
        result: dict[str, list[ParentChild]] = defaultdict(list)
        with PoolManager.eco_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_PARENT_CHILD.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        # oya_hinbanはIN句の値なので、チャンクから特定する必要あり
                        # このクエリは個別実行が必要
                        pass
        # 親子関係はoya_hinbanごとに個別取得が必要（IN句にoya_hinbanがないため）
        result = defaultdict(list)
        with PoolManager.eco_conn() as conn:
            for pn in part_numbers:
                sql = Q.FETCH_PARENT_CHILD.format(placeholders=":1")
                with conn.cursor() as cur:
                    cur.execute(sql, [pn])
                    for row in cur:
                        pc = ParentChild(
                            oya_hinban=pn,
                            ko_hinban=row[0],
                            inzuu=Decimal(str(row[1])) if row[1] is not None else Decimal("1"),
                        )
                        result[pn].append(pc)
        return dict(result)

    @staticmethod
    def fetch_std_kakou_suu(part_numbers: list[str]) -> dict[str, Decimal]:
        """標準加工数を一括取得."""
        result: dict[str, Decimal] = {}
        with PoolManager.eco_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_STD_KAKOU_SUU.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        if row[1] is not None:
                            result[row[0]] = Decimal(str(row[1]))
        return result

    @staticmethod
    def fetch_avg_kakou_suu(hinban: str, history_days: int = 365) -> Decimal:
        """過去N日間の平均加工数を取得（フォールバック用）."""
        hinban_prefix = hinban[:7] + "%"
        start_date = (date.today() - timedelta(days=history_days)).strftime("%Y/%m/%d")
        with PoolManager.eco_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(Q.FETCH_AVG_KAKOU_SUU,
                            {"hinban_prefix": hinban_prefix, "start_date": start_date})
                row = cur.fetchone()
                if row and row[0] is not None and row[1] is not None and row[1] > 0:
                    return Decimal(str(row[0])) / Decimal(str(row[1]))
        return Decimal("1")

    @staticmethod
    def fetch_kakakuhyou(part_numbers: list[str]) -> dict[str, KakakuRow]:
        """購入品の価格表データを一括取得."""
        result: dict[str, KakakuRow] = {}
        with PoolManager.eco_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_KAKAKUHYOU.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        kr = KakakuRow(
                            hinban=row[1] if row[1] else "",
                            tanka=Decimal(str(row[0])) if row[0] is not None else None,
                            tori_tuuka_tani_kbn=row[2] or "JPY",
                        )
                        if kr.hinban:
                            result[kr.hinban] = kr
        return result

    @staticmethod
    def fetch_rate(currency: str) -> Decimal | None:
        """為替レートを取得."""
        with PoolManager.eco_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(Q.FETCH_RATE, {"currency": currency})
                row = cur.fetchone()
                if row and row[0] is not None:
                    return Decimal(str(row[0]))
        return None

    @staticmethod
    def fetch_a_components(part_numbers: list[str]) -> dict[str, list[AssemblyComponent]]:
        """A番の構成部品を一括取得."""
        result: dict[str, list[AssemblyComponent]] = defaultdict(list)
        with PoolManager.eco_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_A_COMPONENTS.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        ac = AssemblyComponent(
                            a_bango=row[0],
                            buhin_bango=row[1],
                            inzuu=Decimal(str(row[2])) if row[2] is not None else Decimal("1"),
                            buhin_name=row[3] or "",
                        )
                        result[ac.a_bango].append(ac)
        return dict(result)

    @staticmethod
    def fetch_a_assembly_cost(part_numbers: list[str]) -> dict[str, Decimal]:
        """A番の組立外注費を一括取得（最大値を使用）."""
        raw: dict[str, list[Decimal]] = defaultdict(list)
        with PoolManager.eco_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_A_ASSEMBLY_COST.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        if row[0] is not None and row[1]:
                            raw[row[1]].append(Decimal(str(row[0])))
        # VBAと同様に最大値を使用
        return {k: max(v) for k, v in raw.items() if v}

    @staticmethod
    def fetch_a_assembly_kousuu(part_numbers: list[str]) -> dict[str, dict]:
        """A番の組立工数データを一括取得."""
        result: dict[str, dict] = {}
        with PoolManager.eco_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_A_ASSEMBLY_KOUSUU.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        result[row[0]] = {
                            "dandori_time": Decimal(str(row[2])) if row[2] is not None else Decimal("0"),
                            "naigaisaku_kbn": row[3] or "",
                            "line_cd": row[4] or "",
                            "torisaki_cd": row[5] or "",
                        }
        return result

    @staticmethod
    def fetch_um_h_sikiri(part_numbers: list[str]) -> dict[str, ShohinBuhin]:
        """UM番のH仕切りを一括取得（zaiko_kyoten_cd/torisaki_cd条件なし）."""
        result: dict[str, ShohinBuhin] = {}
        with PoolManager.eco_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_UM_H_SIKIRI.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        if row[1]:
                            result[row[1]] = ShohinBuhin(
                                shohin_buhin_cd=row[1],
                                h_sikiri=Decimal(str(row[0])) if row[0] is not None else None,
                            )
        return result

    @staticmethod
    def fetch_buhin_kubun(part_numbers: list[str]) -> dict[str, list[str]]:
        """部品区分を一括取得（複数区分をリストで返す）."""
        result: dict[str, list[str]] = defaultdict(list)
        with PoolManager.eco_conn() as conn:
            for chunk in chunk_list(part_numbers):
                ph = make_bind_placeholders(len(chunk))
                sql = Q.FETCH_BUHIN_KUBUN.format(placeholders=ph)
                with conn.cursor() as cur:
                    cur.execute(sql, chunk)
                    for row in cur:
                        if row[1]:
                            result[row[0]].append(row[1])
        return dict(result)
