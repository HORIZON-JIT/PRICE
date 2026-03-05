"""ECOデータベースのSQLテンプレート.

VBAの各サブルーチン内に散在していたSQL文を一箇所に集約。
{placeholders} はバインド変数に動的に置換される。
"""

# 商品部品マスタ: H仕切り, I仕切り, D仕切り, 上代を取得
# VBA: 一括改作成(), H仕切り追加(), アフター部品取り出し()
FETCH_SHOHIN_BUHIN = """
    SELECT shohin_buhin_cd, h_sikiri, i_sikiri, d_sikiri, jyoudai,
           jp_buhi_name, buhinkubun
      FROM ecouser.hv_shohin_buhin
     WHERE shohin_buhin_cd IN ({placeholders})
       AND zaiko_kyoten_cd = 'A'
       AND torisaki_cd = 'T10000'
"""

# H仕切り取得 (最新改版)
# VBA: H仕切り追加() - 品番の先頭7文字でMAX検索
FETCH_H_SIKIRI_LATEST = """
    SELECT a.h_sikiri, a.shohin_buhin_cd
      FROM ecouser.hv_shohin_buhin a
     WHERE a.shohin_buhin_cd = (
               SELECT MAX(b.shohin_buhin_cd)
                 FROM ecouser.hv_shohin_buhin b
                WHERE b.shohin_buhin_cd LIKE :prefix || '%'
                  AND b.zaiko_kyoten_cd = 'A'
                  AND b.torisaki_cd = 'T10000'
           )
       AND a.zaiko_kyoten_cd = 'A'
       AND a.torisaki_cd = 'T10000'
     ORDER BY a.hannkou_date DESC
"""

# 製造ビュー: M番の工程データ取得
# VBA: M番_計算(), 親子()
FETCH_SEIZOU_VIEW = """
    SELECT a.oya_hinban, b.hm_nm_1,
           (a.buhin_juuryou / 1000 * a.juuryou_tanka) AS zairyo_cost,
           a.naigaisaku_kbn, a.ko_hinban, c.torisaki_cd, c.tanka AS gaichu_cost,
           a.dandori_time, a.lot_futai, a.buhin_futai, a.machining_cycle,
           DECODE(a.kizin_kbn, 'HC001', '機', 'HC002', '人') AS kizin_kbn,
           a.line_no, a.oya_line_no
      FROM ecouser.v_seizou_view a
      LEFT JOIN ecouser.t_hm_mst b
        ON a.oya_hinban = b.hinban AND b.seiban = '' AND b.end_date = '9999/1/1'
      LEFT JOIN ecouser.t_torisaki_hm_mst d
        ON a.oya_hinban = d.hinban AND a.ko_hinban = d.koutei_cd
       AND d.end_date = '9999/1/1' AND d.seiban = ''
      LEFT JOIN ecouser.t_kakakuhyou_h_mst e
        ON a.oya_hinban = e.hinban AND a.ko_hinban = e.koutei_cd
       AND e.end_date = '9999/1/1' AND e.seiban = '' AND e.torisaki_cd = d.torisaki_cd
      LEFT JOIN ecouser.t_kakakuhyou_m_mst c
        ON a.oya_hinban = c.hinban AND a.ko_hinban = c.koutei_cd
       AND c.end_date = '9999/1/1' AND c.seiban = '' AND c.torisaki_cd = d.torisaki_cd
       AND c.kkhh_start_date = e.start_date
     WHERE a.oya_hinban IN ({placeholders})
       AND a.oya_seiban = ''
       AND a.bkj_end_date = '9999/1/1'
       AND a.ko_data_kbn = 'PC003'
     ORDER BY a.oya_hinban, a.oya_line_no DESC
"""

# 親子関係: 構成部品の取得
# VBA: 親子()
FETCH_PARENT_CHILD = """
    SELECT ko_hinban, inzuu
      FROM ecouser.v_seizou_view
     WHERE oya_hinban IN ({placeholders})
       AND oya_seiban = '*'
       AND ko_data_kbn = 'PC001'
       AND bkj_end_date = '9999/1/1'
       AND apply_stat = 'PC001'
"""

# 標準加工数: ECOの標準加工数
# VBA: 標準加工数()
FETCH_STD_KAKOU_SUU = """
    SELECT hinban, std_kakou_suu
      FROM ecouser.t_hm_tehai_attr_mst
     WHERE hinban IN ({placeholders})
       AND seiban = '*'
       AND end_date = '9999/1/1'
"""

# 標準加工数フォールバック: 過去1年の平均良品数
# VBA: 標準加工数() - 1部品ずつ実行
FETCH_AVG_KAKOU_SUU = """
    SELECT SUM(ryouhin_suu) AS total_qty, COUNT(*) AS work_count
      FROM ecouser.t_sgy_j_m j
      LEFT JOIN ecouser.hv_sagyou_siji s
        ON j.sgy_siji_no = s.sgy_siji_no AND j.koutei_line_no = s.koutei_line_no
     WHERE j.hinban LIKE :hinban_prefix
       AND s.start_koutei_flg = 1
       AND TO_CHAR(j.kanryou_j_date, 'yyyy/mm/dd') >= :start_date
"""

# 購入品価格: 4番の単価取得
# VBA: 購入品4番(), 購入品4番2()
FETCH_KAKAKUHYOU = """
    SELECT DISTINCT km.tanka, km.hinban, thm.tori_tuuka_tani_kbn
      FROM ecouser.t_kakakuhyou_h_mst kh
      LEFT JOIN ecouser.t_kakakuhyou_m_mst km
        ON kh.hinban = km.hinban
       AND kh.sgy_bumon_kbn = km.sgy_bumon_kbn
       AND kh.koutei_cd = km.koutei_cd
       AND kh.start_date = km.kkhh_start_date
       AND km.seiban = '' AND km.end_date = '9999/1/1'
       AND kh.torisaki_cd = km.torisaki_cd
     INNER JOIN ecouser.v_seizou_view sv
        ON kh.hinban = sv.oya_hinban
       AND kh.koutei_cd = sv.ko_hinban
       AND sv.oya_seiban = '' AND sv.bkj_end_date = '9999/1/1'
     INNER JOIN ecouser.t_torisaki_hm_mst thm
        ON kh.hinban = thm.hinban
       AND kh.sgy_bumon_kbn = thm.sgy_bumon_kbn
       AND kh.koutei_cd = thm.koutei_cd
       AND thm.end_date = '9999/1/1'
       AND kh.torisaki_cd = thm.torisaki_cd
       AND thm.seiban = ''
     WHERE kh.end_date = '9999/1/1'
       AND kh.sgy_bumon_kbn = ''
       AND kh.seiban = ''
       AND kh.hinban IN ({placeholders})
     ORDER BY kh.hinban
"""

# 為替レート
# VBA: 購入品4番() - 通貨ごとに1回
FETCH_RATE = """
    SELECT DISTINCT rm.rate
      FROM ecouser.t_rate_mst rm
     WHERE rm.tuuka_cd_from = :currency
"""

# A番構成部品取得
# VBA: A番()
FETCH_A_COMPONENTS = """
    SELECT a.oya_hinban, a.ko_hinban, inzuu, b.hm_nm_1
      FROM ecouser.v_seizou_view a
      LEFT JOIN ecouser.t_hm_mst b
        ON a.ko_hinban = b.hinban AND b.seiban = '*' AND b.end_date = '9999/1/1'
       AND b.sgy_bumon_kbn = '*' AND b.kyoten_cd = '*'
     WHERE a.oya_hinban IN ({placeholders})
       AND a.oya_seiban = '*'
       AND a.bkj_end_date = '9999/1/1'
       AND a.ko_data_kbn = 'PC001'
"""

# A番組立外注費
# VBA: A番()
FETCH_A_ASSEMBLY_COST = """
    SELECT a.tanka, a.hinban
      FROM ecouser.t_kakakuhyou_m_mst a
      LEFT JOIN ecouser.t_kakakuhyou_h_mst b
        ON a.hinban = b.hinban AND a.kkhh_start_date = b.start_date
       AND b.end_date = '9999/1/1'
     WHERE a.hinban IN ({placeholders})
"""

# A番組立工数
# VBA: A番()
FETCH_A_ASSEMBLY_KOUSUU = """
    SELECT oya_hinban, ko_hinban, dandori_time, naigaisaku_kbn,
           line_cd, torisaki_cd
      FROM ecouser.v_seizou_view
     WHERE oya_hinban IN ({placeholders})
       AND oya_seiban = '*'
       AND bkj_end_date = '9999/1/1'
       AND (ko_hinban = 'K-S' OR ko_hinban = '@K-S')
       AND ko_data_kbn = 'PC003'
"""

# 部品区分取得
# VBA: 部品区分追記()
FETCH_BUHIN_KUBUN = """
    SELECT DISTINCT shohin_buhin_cd, buhinkubun
      FROM ecouser.hv_shohin_buhin
     WHERE shohin_buhin_cd IN ({placeholders})
       AND zaiko_kyoten_cd = 'A'
"""

# 消耗品区分取得
# VBA: 消耗品データ追記()
FETCH_CONSUMABLE_KBN = """
    SELECT tam.hinban, kc.cd_nm_1
      FROM ecouser.t_hm_tehai_attr_mst tam
      LEFT JOIN ecouser.t_kbn_cd_m kc
        ON tam.buhin_kbn = kc.cd AND kc.cd_kbn = 'HD014'
     WHERE tam.hinban IN ({placeholders})
       AND tam.sgy_bumon_kbn = '*'
       AND tam.kyoten_cd = '*'
       AND tam.seiban = '*'
       AND tam.end_date = '9999/1/1'
"""

# UM番: H仕切り直接取得
# VBA: UM番()
FETCH_UM_H_SIKIRI = """
    SELECT DISTINCT h_sikiri, shohin_buhin_cd
      FROM ecouser.hv_shohin_buhin
     WHERE shohin_buhin_cd IN ({placeholders})
"""
