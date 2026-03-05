"""価格計算バッチ処理のメインエントリーポイント.

VBAの一括()に対応する2フェーズ処理:
  Phase 1: データ一括取得
  Phase 2: 一括計算 → Excel出力
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path

from openpyxl import load_workbook

from price.calc.dispatcher import PriceDispatcher
from price.config import AppConfig, load_config
from price.db.eco_repo import EcoRepo
from price.db.honps_repo import HonpsRepo
from price.db.pool import PoolManager
from price.export.excel_writer import write_results
from price.models.enums import PartPrefix, classify_prefix


def read_input_parts(input_path: str | Path) -> list[str]:
    """Excelファイルから品番リストを読み込む.

    A列に品番が入っている前提（1行目はヘッダー）。
    """
    wb = load_workbook(input_path, read_only=True, data_only=True)
    ws = wb.active
    parts = []
    for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
        val = row[0]
        if val is not None and str(val).strip():
            parts.append(str(val).strip())
    wb.close()
    return parts


def prefetch_data(part_numbers: list[str], config: AppConfig) -> dict:
    """Phase 1: 全データを一括プリフェッチする.

    VBAでは各行で個別にDB接続・クエリしていた処理を、
    プレフィックス別にグルーピングして一括取得する。
    """
    data: dict = {}

    # プレフィックス別に分類
    groups: dict[PartPrefix, list[str]] = defaultdict(list)
    for pn in part_numbers:
        try:
            prefix = classify_prefix(pn)
            groups[prefix].append(pn)
        except ValueError:
            pass

    print(f"  部品数: {len(part_numbers)}")
    for prefix, pns in groups.items():
        print(f"    {prefix.value}番: {len(pns)}件")

    # 1. HONPS標準単価 (A番以外の全部品)
    non_a_parts = [pn for pn in part_numbers
                   if classify_prefix(pn) != PartPrefix.A]
    print("  標準単価を取得中...")
    data["hyotanka"] = HonpsRepo.fetch_hyotanka(non_a_parts)

    # A番の構成部品の標準単価も取得
    a_parts = groups.get(PartPrefix.A, [])
    if a_parts:
        print("  A番構成データを取得中...")
        data["a_components"] = EcoRepo.fetch_a_components(a_parts)
        # 構成部品の品番を集める
        component_pns = set()
        for comps in data["a_components"].values():
            for c in comps:
                component_pns.add(c.buhin_bango)
        # 構成部品の標準単価を追加取得
        if component_pns:
            comp_hyotanka = HonpsRepo.fetch_hyotanka(list(component_pns))
            data["hyotanka"].update(comp_hyotanka)
        # 組立外注費・工数
        data["a_assembly_cost"] = EcoRepo.fetch_a_assembly_cost(a_parts)
        data["a_assembly_kousuu"] = EcoRepo.fetch_a_assembly_kousuu(a_parts)

    # 2. 購入品(4番)の価格
    four_parts = groups.get(PartPrefix.FOUR, [])
    if four_parts:
        print("  購入品価格を取得中...")
        data["kakakuhyou"] = EcoRepo.fetch_kakakuhyou(four_parts)
        # 外貨レートの取得
        currencies = set()
        for kk in data["kakakuhyou"].values():
            if kk.tori_tuuka_tani_kbn and kk.tori_tuuka_tani_kbn != "JPY":
                currencies.add(kk.tori_tuuka_tani_kbn)
        fx_rates = {}
        for curr in currencies:
            rate = EcoRepo.fetch_rate(curr)
            if rate is not None:
                fx_rates[curr] = rate
        data["fx_rates"] = fx_rates

    # 3. ECO H仕切り (全部品)
    print("  ECO H仕切りを取得中...")
    data["shohin_buhin"] = EcoRepo.fetch_shohin_buhin(part_numbers)

    # 4. 部品区分 (全部品)
    print("  部品区分を取得中...")
    data["buhin_kubun"] = EcoRepo.fetch_buhin_kubun(part_numbers)

    return data


def run_batch(input_path: str, output_path: str,
              settings_path: str = "config/settings.yaml",
              rates_path: str = "config/rates.yaml",
              rates_excel_path: str | None = None,
              rates_sheet_name: str = "テーブル") -> None:
    """バッチ処理のメインフロー."""
    print("=" * 60)
    print("価格計算バッチ処理")
    print("=" * 60)

    # 設定読み込み
    print("\n[1/5] 設定ファイル読み込み...")
    if rates_excel_path:
        print(f"  掛率: {rates_excel_path} (シート: {rates_sheet_name})")
    else:
        print(f"  掛率: {rates_path}")
    config = load_config(settings_path, rates_path,
                         rates_excel_path=rates_excel_path,
                         rates_sheet_name=rates_sheet_name)

    # DB接続プール初期化
    print("[2/5] データベース接続...")
    PoolManager.init(config.eco_db, config.honps_db)

    try:
        # 入力読み込み
        print(f"[3/5] 入力ファイル読み込み: {input_path}")
        part_numbers = read_input_parts(input_path)
        if not part_numbers:
            print("エラー: 品番が見つかりません。")
            return

        # Phase 1: データ一括取得
        print(f"[4/5] データ取得中...")
        start = time.time()
        data = prefetch_data(part_numbers, config)
        fetch_time = time.time() - start
        print(f"  データ取得完了: {fetch_time:.1f}秒")

        # Phase 2: 一括計算
        print(f"[5/5] 計算実行中...")
        start = time.time()
        dispatcher = PriceDispatcher(config.rates)
        results = dispatcher.calculate_batch(part_numbers, data)
        calc_time = time.time() - start
        print(f"  計算完了: {calc_time:.1f}秒")

        # Excel出力
        out = write_results(results, output_path)
        print(f"\n結果出力: {out}")
        print(f"  処理件数: {len(results)}")
        null_count = sum(1 for r in results if r.has_null_data)
        if null_count:
            print(f"  NULLデータあり: {null_count}件")
        print(f"  合計処理時間: {fetch_time + calc_time:.1f}秒")

    finally:
        PoolManager.close()

    print("\n完了")


def main():
    parser = argparse.ArgumentParser(
        description="価格計算バッチ処理システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  price --input parts.xlsx --output result.xlsx
  price -i parts.xlsx -o result.xlsx --settings config/settings.yaml --rates config/rates.yaml
        """,
    )
    parser.add_argument("-i", "--input", required=True,
                        help="入力Excelファイル (A列に品番)")
    parser.add_argument("-o", "--output", required=True,
                        help="出力Excelファイル")
    parser.add_argument("--settings", default="config/settings.yaml",
                        help="DB接続設定ファイル (default: config/settings.yaml)")
    parser.add_argument("--rates", default="config/rates.yaml",
                        help="掛率設定YAMLファイル (default: config/rates.yaml)")
    parser.add_argument("--rates-excel",
                        help="掛率が入ったExcelファイル (「テーブル」シートから読み込み)")
    parser.add_argument("--rates-sheet", default="テーブル",
                        help="Excelの掛率シート名 (default: テーブル)")

    args = parser.parse_args()
    run_batch(args.input, args.output, args.settings, args.rates,
              rates_excel_path=args.rates_excel,
              rates_sheet_name=args.rates_sheet)


if __name__ == "__main__":
    main()
