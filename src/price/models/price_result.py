"""計算結果モデル."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PriceResult:
    """1部品の最終計算結果."""
    buhin_bango: str
    zaiko_cd: str = ""                     # 在庫CD
    standard_price: Decimal | None = None  # 標準単価
    t_sikiri: int | None = None            # T仕切り
    kakeru: Decimal | None = None          # 使用した掛率
    hi_sikiri: int | None = None           # HI仕切り
    kari_jyoudai: int | None = None        # 仮上代
    dealer_sikiri: int | None = None       # ディーラー仕切り
    jyoudai: int | None = None             # 上代
    h_sikiri_eco: Decimal | None = None    # ECO H仕切り
    h_sikiri_eco_adjusted: int | None = None  # ECO H仕切り × 調整係数
    buhin_kubun: str = ""                  # 部品区分
    naikote_cost: Decimal | None = None    # 内作コスト
    gaikote_cost: Decimal | None = None    # 外注コスト
    konyu_cost: Decimal | None = None      # 購入コスト
    first_process: str = ""                # 第1工程
    has_null_data: bool = False            # NULLデータ有無
    price_comparison_flag: str = ""        # 価格比較フラグ (高い/安い)
