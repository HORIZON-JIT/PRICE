"""計算機の抽象基底クラス."""
from abc import ABC, abstractmethod

from price.config import RateConfig
from price.models.price_result import PriceResult


class BaseCalculator(ABC):
    """H仕切り計算の基底クラス."""

    def __init__(self, rate_cfg: RateConfig):
        self.rate_cfg = rate_cfg

    @abstractmethod
    def calculate(self, part_numbers: list[str], data: dict) -> list[PriceResult]:
        """部品番号リストとプリフェッチ済みデータからH仕切りを計算する.

        Args:
            part_numbers: 同一プレフィックスの部品番号リスト
            data: プリフェッチ済みの全データ辞書

        Returns:
            計算結果のリスト
        """
