"""設定ファイル読み込み."""
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import yaml


@dataclass
class DbConfig:
    """データベース接続設定."""
    user: str
    password: str
    dsn: str
    pool_min: int = 2
    pool_max: int = 10


@dataclass
class MBandConfig:
    """M番の価格帯別掛率設定."""
    band1_threshold: Decimal
    band2_threshold: Decimal
    band3_threshold: Decimal
    rate_M1: Decimal
    rate_M2: Decimal
    rate_M3: Decimal


@dataclass
class PriceChainConfig:
    """価格チェーン設定."""
    hi_var1: Decimal
    hi_var2: Decimal
    hi_var3: Decimal
    kari_var1: Decimal
    kari_var2: Decimal
    kari_var3: Decimal  # 4番以外
    kari_var4: Decimal  # 4番以外
    dealer_var1: Decimal
    jyoudai_band1: Decimal
    jyoudai_band2: Decimal
    jyoudai_rate1: Decimal
    jyoudai_rate2: Decimal
    jyoudai_rate3: Decimal


@dataclass
class RateConfig:
    """全掛率設定."""
    m_band: MBandConfig
    rate_4: Decimal
    rate_e: Decimal
    rate_a: Decimal
    rate_l: Decimal
    rate_cv: Decimal
    rate_um: Decimal
    rate_p: Decimal
    up_rate: Decimal
    charge_rate: Decimal
    price_chain: PriceChainConfig


@dataclass
class AppConfig:
    """アプリケーション全体設定."""
    eco_db: DbConfig
    honps_db: DbConfig
    rates: RateConfig
    chunk_size: int = 999
    max_depth: int = 10
    history_days: int = 365


def _to_decimal(val) -> Decimal:
    if val is None:
        raise ValueError("掛率が未設定(null)です。config/rates.yamlを確認してください。")
    return Decimal(str(val))


def load_config(
    settings_path: str | Path = "config/settings.yaml",
    rates_path: str | Path = "config/rates.yaml",
) -> AppConfig:
    """設定ファイルを読み込んでAppConfigを返す."""
    with open(settings_path, encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    with open(rates_path, encoding="utf-8") as f:
        rates = yaml.safe_load(f)

    db = settings["database"]
    eco_db = DbConfig(**db["eco"])
    honps_db = DbConfig(**db["honps"])

    ts = rates["t_sikiri"]
    m = ts["M"]
    mfg = rates["manufacturing"]
    pc = rates["price_chain"]

    m_band = MBandConfig(
        band1_threshold=_to_decimal(m["band1_threshold"]),
        band2_threshold=_to_decimal(m["band2_threshold"]),
        band3_threshold=_to_decimal(m["band3_threshold"]),
        rate_M1=_to_decimal(m["rate_M1"]),
        rate_M2=_to_decimal(m["rate_M2"]),
        rate_M3=_to_decimal(m["rate_M3"]),
    )

    price_chain = PriceChainConfig(
        hi_var1=_to_decimal(pc["hi_sikiri"]["var1"]),
        hi_var2=_to_decimal(pc["hi_sikiri"]["var2"]),
        hi_var3=_to_decimal(pc["hi_sikiri"]["var3"]),
        kari_var1=_to_decimal(pc["kari_jyoudai"]["var1"]),
        kari_var2=_to_decimal(pc["kari_jyoudai"]["var2"]),
        kari_var3=_to_decimal(pc["kari_jyoudai"]["var3"]),
        kari_var4=_to_decimal(pc["kari_jyoudai"]["var4"]),
        dealer_var1=_to_decimal(pc["dealer_sikiri"]["var1"]),
        jyoudai_band1=_to_decimal(pc["jyoudai"]["band1_threshold"]),
        jyoudai_band2=_to_decimal(pc["jyoudai"]["band2_threshold"]),
        jyoudai_rate1=_to_decimal(pc["jyoudai"]["rate1"]),
        jyoudai_rate2=_to_decimal(pc["jyoudai"]["rate2"]),
        jyoudai_rate3=_to_decimal(pc["jyoudai"]["rate3"]),
    )

    rate_config = RateConfig(
        m_band=m_band,
        rate_4=_to_decimal(ts["4"]),
        rate_e=_to_decimal(ts["E"]),
        rate_a=_to_decimal(ts["A"]),
        rate_l=_to_decimal(ts["L"]),
        rate_cv=_to_decimal(ts["CV"]),
        rate_um=_to_decimal(ts["UM"]),
        rate_p=_to_decimal(ts["P"]),
        up_rate=_to_decimal(mfg["up_rate"]),
        charge_rate=_to_decimal(mfg["charge_rate"]),
        price_chain=price_chain,
    )

    batch = settings.get("batch", {})
    return AppConfig(
        eco_db=eco_db,
        honps_db=honps_db,
        rates=rate_config,
        chunk_size=batch.get("chunk_size", 999),
        max_depth=batch.get("max_depth", 10),
        history_days=batch.get("manufacturing", {}).get("history_days", 365),
    )
