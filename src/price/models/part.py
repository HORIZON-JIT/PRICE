"""部品データモデル."""
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class ShohinBuhin:
    """商品部品マスタ (hv_shohin_buhin)."""
    shohin_buhin_cd: str
    h_sikiri: Decimal | None = None
    i_sikiri: Decimal | None = None
    d_sikiri: Decimal | None = None
    jyoudai: Decimal | None = None
    jp_buhi_name: str = ""
    buhinkubun: str = ""
    zaiko_cd: str = ""


@dataclass
class KakakuRow:
    """価格表データ (t_kakakuhyou_m_mst)."""
    hinban: str
    tanka: Decimal | None = None
    torisaki_cd: str = ""
    tori_tuuka_tani_kbn: str = "JPY"


@dataclass
class HyotankaRow:
    """標準単価データ (honps.hv_ma_ta_hyotanka)."""
    hinban: str
    standard_price: Decimal | None = None  # tan_cost or tan_cost + tan_cost_ko
    naikote_cost: Decimal | None = None
    gaikote_cost: Decimal | None = None
    konyu_cost: Decimal | None = None
    tan_cost_ko: Decimal | None = None
    kote_1: str = ""  # 第1工程


@dataclass
class ParentChild:
    """親子関係 (v_seizou_view / YOSEKOSE)."""
    oya_hinban: str
    ko_hinban: str
    inzuu: Decimal = Decimal("1")


@dataclass
class Part:
    """計算対象の部品."""
    buhin_bango: str
    standard_price: Decimal | None = None
    h_sikiri_eco: Decimal | None = None
    h_sikiri: int | None = None
    hi_sikiri: int | None = None
    kari_jyoudai: int | None = None
    dealer_sikiri: int | None = None
    jyoudai: int | None = None
    kakeru: Decimal | None = None
    buhin_kubun: str = ""
    first_process: str = ""
    naikote_cost: Decimal | None = None  # 内作コスト
    has_null_data: bool = False
    children: list["Part"] = field(default_factory=list)
