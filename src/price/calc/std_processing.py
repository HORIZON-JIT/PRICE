"""標準加工数の取得ロジック.

VBAの標準加工数()に対応。
1. ECOのt_hm_tehai_attr_mstから標準加工数を取得
2. なければ過去1年間の平均良品数をフォールバックとして使用
3. それもなければ1を返す
"""
from decimal import Decimal

from price.db.eco_repo import EcoRepo


def get_std_kakou_suu(
    part_numbers: list[str],
    first_processes: dict[str, str],
    history_days: int = 365,
) -> dict[str, Decimal]:
    """標準加工数をバッチ取得する.

    Args:
        part_numbers: 対象部品番号リスト
        first_processes: {部品番号: 第1工程名} のマッピング
        history_days: 平均計算の日数

    Returns:
        {部品番号: 標準加工数} のマッピング
    """
    result: dict[str, Decimal] = {}

    # MOLまたはTNC工程の部品のみECOから標準加工数を取得
    eligible = [
        pn for pn in part_numbers
        if first_processes.get(pn, "") in ("MOL", "TNC")
    ]

    if eligible:
        eco_data = EcoRepo.fetch_std_kakou_suu(eligible)
        result.update(eco_data)

    # 取得できなかった部品は過去1年平均にフォールバック
    missing = [pn for pn in part_numbers if pn not in result]
    for pn in missing:
        avg = EcoRepo.fetch_avg_kakou_suu(pn, history_days)
        result[pn] = avg

    return result
