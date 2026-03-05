"""HONPSデータベースのSQLテンプレート.

レガシーシステム(ORAGOLD)のSQL。HONPSスキーマとhonpsスキーマの
ビュー(hv_ma_ta_hyotanka)を使用する。
"""

# 標準単価 (ECO経由のビュー)
# VBA: 標準単価追記(), 標準単価追記_A番用()
FETCH_HYOTANKA = """
    SELECT hinban,
           CASE WHEN tan_cost_ko IS NULL
                THEN tan_cost
                ELSE (tan_cost + tan_cost_ko)
           END AS standard_price,
           naikote_cost, gaikote_cost, konyu_cost, tan_cost_ko,
           kote_1
      FROM honps.hv_ma_ta_hyotanka
     WHERE hinban IN ({placeholders})
"""

# HONPS M番部品データ (旧システム直接)
# VBA: H_M番_計算()
FETCH_M_BUHIN = """
    SELECT a.zuban, a.buhi_mei, a.zairyo_cost, a.kote_jun,
           a.koutei, a.ka, a.han, a.gyusya, a.gyusyacost,
           a.in_plan_t, a.lot_inc_t, a.buh_inc_t, a.kakou_cycle_t,
           b.kijin_flg
      FROM honps.m_buhin a
      LEFT JOIN honps.koutei b ON a.koutei = b.koutei
     WHERE a.zuban IN ({placeholders})
     ORDER BY a.zuban, a.kote_jun
"""

# HONPS 親子関係
# VBA: H_親子()
FETCH_YOSEKOSE = """
    SELECT oya_zuban, ko_zuban, inzu
      FROM honps.yosekose
     WHERE oya_zuban IN ({placeholders})
"""

# HONPS 標準単価 (旧形式)
# VBA: H_M番_計算()
FETCH_TA_HYOTANKA = """
    SELECT key AS hinban, tan_cost
      FROM honps.ta_hyotanka
     WHERE key IN ({placeholders})
"""

# HONPS 購入品価格
# VBA: H_購入品4番(), H_購入品4番2()
FETCH_BUHINHYO = """
    SELECT zuban, by_cost
      FROM honps.buhinhyo
     WHERE zuban IN ({placeholders})
"""

# HONPS A番構成
# VBA: H_A番()
FETCH_PA_BUKOUSE = """
    SELECT parts_no, buhi_no, inzu
      FROM honps.pa_bukouse
     WHERE parts_no IN ({placeholders})
"""

# HONPS 組立外注費
# VBA: H_A番()
FETCH_P_BUHIN = """
    SELECT kataban, tanka
      FROM honps.p_buhin
     WHERE kataban IN ({placeholders})
"""

# HONPS 組立工数
# VBA: H_A番()
FETCH_PA_PATMST_TIME = """
    SELECT parts_no, hyojyun_time
      FROM honps.pa_patmst
     WHERE parts_no IN ({placeholders})
"""

# HONPS 組立場所
# VBA: H_A番()
FETCH_PA_PATMST_PLACE = """
    SELECT parts_no, kumi_place
      FROM honps.pa_patmst
     WHERE parts_no IN ({placeholders})
"""

# HONPS 備考
# VBA: H_A番備考追加()
FETCH_PA_PATMST_BIKOU = """
    SELECT parts_no, bikou
      FROM honps.pa_patmst
     WHERE parts_no IN ({placeholders})
"""

# HONPS 手配数 (標準加工数計算用)
# VBA: H_標準加工数()
FETCH_M_TEHAI = """
    SELECT zuban, tehai_su, nouki
      FROM honps.m_tehai
     WHERE zuban IN ({placeholders})
       AND kote_jun = 1
       AND nouki >= :start_date
"""

# HONPS 標準加工数 (MOL工程)
# VBA: H_標準加工数()
FETCH_STD_KAKOU_SU = """
    SELECT zuban, std_kakou_su
      FROM honps.m_buhin
     WHERE zuban IN ({placeholders})
       AND kote_jun = 1
"""
