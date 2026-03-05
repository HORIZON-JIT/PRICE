"""列挙型定義."""
from enum import Enum


class PartPrefix(Enum):
    """部品番号のプレフィックスによる分類."""
    M = "M"       # 製造部品
    FOUR = "4"    # 購入品
    E = "E"       # E番
    F = "F"       # F番 (E番と同じ掛率)
    A = "A"       # 組立品 (除算で計算)
    L = "L"       # L番
    CV = "CV"     # CV番
    UM = "UM"     # UM番
    P = "P"       # P番


class ProcessType(Enum):
    """内外作区分."""
    INTERNAL = "PC001"     # 社内
    OUTSOURCE = "PC002"    # 社外
    OUTSOURCE2 = "PC003"   # 社外2


class MachinePersonType(Enum):
    """機人区分."""
    MACHINE = "機"    # 機 (HC001)
    PERSON = "人"     # 人 (HC002)


def classify_prefix(part_number: str) -> PartPrefix:
    """部品番号からプレフィックスを判定する."""
    if not part_number:
        raise ValueError("部品番号が空です")
    pn = part_number.strip()
    if pn.startswith("CV"):
        return PartPrefix.CV
    if pn.startswith("UM"):
        return PartPrefix.UM
    first = pn[0]
    mapping = {
        "M": PartPrefix.M,
        "4": PartPrefix.FOUR,
        "E": PartPrefix.E,
        "F": PartPrefix.F,
        "A": PartPrefix.A,
        "L": PartPrefix.L,
        "P": PartPrefix.P,
    }
    prefix = mapping.get(first)
    if prefix is None:
        raise ValueError(f"未知のプレフィックス: {first} (部品番号: {pn})")
    return prefix
