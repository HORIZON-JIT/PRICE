"""製造工程データモデル."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class SeizouRow:
    """製造ビュー行 (v_seizou_view for PC003工程)."""
    oya_hinban: str
    hm_nm_1: str = ""               # 部品名
    zairyo_cost: Decimal | None = None  # 材料費 (buhin_juuryou/1000*juuryou_tanka)
    naigaisaku_kbn: str = ""         # 内外作区分 (PC001/PC002/PC003)
    ko_hinban: str = ""              # 工程
    torisaki_cd: str = ""            # 業者
    gaichu_cost: Decimal | None = None  # 外注費
    dandori_time: Decimal | None = None  # 内段取り
    lot_futai: Decimal | None = None     # LOT付帯
    buhin_futai: Decimal | None = None   # 部品付帯
    machining_cycle: Decimal | None = None  # 加工サイクル
    kizin_kbn: str = ""              # 機人 (機/人)
    line_no: str = ""                # 員数
    oya_line_no: str = ""            # 工数計算用


@dataclass
class AssemblyComponent:
    """A番構成部品."""
    a_bango: str           # A番
    buhin_bango: str       # 部品番号
    inzuu: Decimal         # 員数
    buhin_name: str = ""   # 部品名
    tanka: Decimal | None = None       # 単価
    h_sikiri: int | None = None        # H仕切り
    h_sikiri_x_inzuu: int | None = None  # H仕切り×員数


@dataclass
class AssemblyResult:
    """A番計算結果."""
    a_bango: str
    components: list[AssemblyComponent]
    buhin_total: Decimal = Decimal("0")     # 部品合計 (Σ員数×単価)
    h_sikiri_total: int = 0                 # H仕切合計 (Σ員数×H仕切)
    kousuu: Decimal = Decimal("0")          # 工数 (分)
    kousuu_x_charge: Decimal = Decimal("0") # 工数×チャージ
    kumitate_gaichuhi: Decimal = Decimal("0")  # 社外組立費
    genka_total: Decimal = Decimal("0")     # 原価合計
    h_sikiri_sum: int = 0                   # H仕切合計(最終)
    assembly_place: str = ""                # 組立場所
    has_null_data: bool = False
