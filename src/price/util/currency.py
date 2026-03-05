"""外貨換算ユーティリティ."""
from decimal import Decimal


def convert_to_jpy(amount, rate) -> Decimal:
    """外貨金額を日本円に変換する.

    Args:
        amount: 外貨金額
        rate: 為替レート (外貨→JPY)

    Returns:
        日本円金額
    """
    if amount is None or rate is None:
        return Decimal("0")
    return Decimal(str(amount)) * Decimal(str(rate))
