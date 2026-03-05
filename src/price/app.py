"""Streamlit Web UI for PRICE 価格演算システム.

起動: streamlit run src/price/app.py
"""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st
from openpyxl import load_workbook

from price.config import load_config
from price.db.pool import PoolManager
from price.export.excel_writer import COLUMNS, write_results
from price.main import process_parts
from price.models.enums import PartPrefix, classify_prefix

# ---------- ページ設定 ----------
st.set_page_config(page_title="PRICE 価格演算", layout="wide")

# ---------- サイドバー: 設定 ----------
with st.sidebar:
    st.header("設定")

    settings_path = st.text_input("DB設定ファイル", value="config/settings.yaml")

    rate_source = st.radio("掛率ソース", ["YAML", "Excel"])
    if rate_source == "YAML":
        rates_path = st.text_input("掛率YAML", value="config/rates.yaml")
        rates_excel_path = None
        rates_sheet_name = "テーブル"
    else:
        rates_excel_path = st.text_input("掛率Excelファイル", value="config/掛率.xlsx")
        rates_sheet_name = st.text_input("シート名", value="テーブル")
        rates_path = None

# ---------- メインエリア ----------
st.title("PRICE 価格演算システム")

# ---------- 入力タブ ----------
tab_excel, tab_manual = st.tabs(["Excelアップロード", "手入力"])

with tab_excel:
    uploaded_file = st.file_uploader(
        "品番リスト（A列に品番、1行目ヘッダー）",
        type=["xlsx"],
    )

with tab_manual:
    manual_input = st.text_area(
        "品番を1行ずつ入力してください",
        height=200,
        placeholder="M12345\n4ABCDE\nA99999",
    )


def _is_a_part(buhin_bango: str) -> bool:
    """A番かどうか判定する."""
    try:
        return classify_prefix(buhin_bango) == PartPrefix.A
    except ValueError:
        return False


def _get_part_numbers() -> list[str] | None:
    """アクティブな入力方法から品番リストを取得する."""
    if uploaded_file is not None:
        wb = load_workbook(uploaded_file, read_only=True, data_only=True)
        ws = wb.active
        parts = []
        for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
            val = row[0]
            if val is not None and str(val).strip():
                parts.append(str(val).strip())
        wb.close()
        return parts if parts else None
    if manual_input and manual_input.strip():
        lines = manual_input.strip().splitlines()
        return [ln.strip() for ln in lines if ln.strip()]
    return None


# ---------- 実行ボタン ----------
if st.button("実行", type="primary", use_container_width=True):
    part_numbers = _get_part_numbers()
    if part_numbers is None:
        st.error("品番が入力されていません。Excelをアップロードするか、手入力してください。")
        st.stop()

    st.info(f"品番数: {len(part_numbers)}")

    # 設定読み込み
    try:
        config = load_config(
            settings_path,
            rates_path,
            rates_excel_path=rates_excel_path,
            rates_sheet_name=rates_sheet_name,
        )
    except Exception as e:
        st.error(f"設定読み込みエラー: {e}")
        st.stop()

    # DB接続プール初期化（冪等）
    try:
        PoolManager.init(config.eco_db, config.honps_db)
    except Exception as e:
        st.error(f"DB接続エラー: {e}")
        st.stop()

    # 処理実行（プログレスバー付き）
    progress_bar = st.progress(0, text="処理開始...")

    def _on_progress(step: int, total: int, msg: str) -> None:
        progress_bar.progress(step / total, text=msg)

    try:
        results, stats = process_parts(part_numbers, config, _on_progress)
    except Exception as e:
        st.error(f"処理エラー: {e}")
        st.stop()

    progress_bar.progress(1.0, text="完了")

    # セッションに保存（Streamlit の rerun でも保持）
    st.session_state["results"] = results
    st.session_state["stats"] = stats

# ---------- 結果表示 ----------
if "results" in st.session_state:
    results = st.session_state["results"]
    stats = st.session_state["stats"]

    # サマリー指標
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("処理件数", stats["total"])
    col2.metric("NULLデータ", stats["null_count"])
    col3.metric("データ取得", f"{stats['fetch_time']:.1f}秒")
    col4.metric("計算処理", f"{stats['calc_time']:.1f}秒")

    # DataFrame 構築
    rows = []
    for r in results:
        row = {}
        for header, attr in COLUMNS:
            val = getattr(r, attr, None)
            if attr == "has_null_data":
                val = "有" if val else ""
            row[header] = val
        rows.append(row)
    df = pd.DataFrame(rows)

    # 条件付き色付け
    def _highlight_rows(row_series: pd.Series) -> list[str]:
        styles = [""] * len(row_series)
        idx = {col: i for i, col in enumerate(row_series.index)}

        std_price = row_series.get("標準単価")
        if std_price is None or std_price == 0:
            styles[idx["品番"]] = "background-color: #FFFF00"
            styles[idx["標準単価"]] = "background-color: #FFFF00"

        flag = row_series.get("価格比較")
        if flag == "高":
            styles[idx["T仕切り"]] = "background-color: #FFFF00"
        elif flag == "安":
            styles[idx["T仕切り"]] = "background-color: #00FFFF"

        return styles

    styled_df = df.style.apply(_highlight_rows, axis=1)
    st.dataframe(styled_df, use_container_width=True, height=600)

    # Excel ダウンロード
    buf = io.BytesIO()
    write_results(results, buf)
    buf.seek(0)

    st.download_button(
        label="Excelダウンロード",
        data=buf,
        file_name="price_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.document",
    )

    # ---------- A番 構成部品詳細 ----------
    assembly_details = stats.get("assembly_details", {})
    if assembly_details:
        st.markdown("---")
        st.subheader("A番 構成部品詳細")

        # A番の品番リストを作成
        a_parts = [r.buhin_bango for r in results
                    if _is_a_part(r.buhin_bango) and r.buhin_bango in assembly_details]

        if a_parts:
            # 各A番に詳細表示ボタンを配置
            cols_per_row = 4
            for i in range(0, len(a_parts), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(a_parts):
                        pn = a_parts[idx]
                        if col.button(f"詳細表示: {pn}", key=f"detail_{pn}",
                                      use_container_width=True):
                            st.session_state["selected_a_detail"] = pn

            # 選択中のA番の詳細を表示
            selected_a = st.session_state.get("selected_a_detail")
            if selected_a and selected_a in assembly_details:
                detail = assembly_details[selected_a]

                st.markdown(f"### {selected_a} の構成部品")

                # サマリー情報
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("部品合計", f"{detail.buhin_total:,.0f}")
                col2.metric("T仕切合計", f"{detail.t_sikiri_total:,}")
                col3.metric("工数×チャージ", f"{detail.kousuu_x_charge:,.0f}")
                col4.metric("社外組立費", f"{detail.kumitate_gaichuhi:,.0f}")

                col5, col6, col7, col8 = st.columns(4)
                col5.metric("工数(分)", f"{detail.kousuu:,.1f}")
                col6.metric("原価合計", f"{detail.genka_total:,.0f}")
                col7.metric("組立場所", detail.assembly_place or "-")
                a_result = next((r for r in results if r.buhin_bango == selected_a), None)
                col8.metric("A番T仕切", f"{a_result.t_sikiri:,}" if a_result and a_result.t_sikiri else "-")

                # 構成部品テーブル
                comp_rows = []
                for comp in detail.components:
                    comp_rows.append({
                        "部品番号": comp.buhin_bango,
                        "員数": int(comp.inzuu),
                        "単価": float(comp.tanka) if comp.tanka is not None else None,
                        "T仕切り": comp.t_sikiri,
                        "T仕切り×員数": comp.t_sikiri_x_inzuu,
                        "部品名": comp.buhin_name,
                    })
                if comp_rows:
                    comp_df = pd.DataFrame(comp_rows)
                    st.dataframe(comp_df, use_container_width=True, hide_index=False)
                else:
                    st.info("構成部品がありません。")
