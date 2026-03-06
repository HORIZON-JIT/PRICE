"""コネクションプール管理.

VBAでは各サブルーチンが毎回myCon.Open/myCon.Closeしていたが、
本モジュールでプールを一括管理し、接続のオーバーヘッドを排除する。
"""
from __future__ import annotations

import os
import platform
from contextlib import contextmanager
from typing import Generator

import oracledb

from price.config import DbConfig

# Oracle Instant Clientの設定ディレクトリ（tnsnames.ora の場所）
# 環境変数 TNS_ADMIN > デフォルトパス の優先順位で探索
_DEFAULT_CONFIG_DIRS = [
    r"C:\app\power\product\11.2.0\client_1\network\admin",
]

# Thick モード用 Instant Client パス候補
_INSTANT_CLIENT_DIRS = [
    r"C:\oracle\instantclient",
    r"C:\oracle\instantclient_11_2",
]


def _find_config_dir() -> str | None:
    """tnsnames.ora が存在するディレクトリを探す."""
    # 環境変数が設定済みならそれを使う
    tns_admin = os.environ.get("TNS_ADMIN")
    if tns_admin and os.path.isfile(os.path.join(tns_admin, "tnsnames.ora")):
        return tns_admin

    oracle_home = os.environ.get("ORACLE_HOME")
    if oracle_home:
        candidate = os.path.join(oracle_home, "network", "admin")
        if os.path.isfile(os.path.join(candidate, "tnsnames.ora")):
            return candidate

    # Windows のデフォルトパスを確認
    if platform.system() == "Windows":
        for d in _DEFAULT_CONFIG_DIRS:
            if os.path.isfile(os.path.join(d, "tnsnames.ora")):
                return d

    return None


def _init_thick_mode() -> None:
    """古い Oracle DB (11g等) に接続するため thick モードを初期化する.

    thin モードは Oracle 12.1+ のみ対応のため、
    64bit Instant Client を使った thick モードが必要。
    既に初期化済みの場合は何もしない。
    """
    if oracledb.is_thin_mode():
        for lib_dir in _INSTANT_CLIENT_DIRS:
            if os.path.isfile(os.path.join(lib_dir, "oci.dll")):
                oracledb.init_oracle_client(lib_dir=lib_dir)
                return
        # パス候補に見つからない場合はlib_dir指定なしで試行（PATH依存）
        oracledb.init_oracle_client()


def _output_type_handler(cursor, metadata):
    """Oracle CHAR型の末尾スペースパディングを自動トリムする.

    VBAのADODBは自動的にトリムするため問題にならないが、
    python-oracledbはCHAR型の値をそのまま返す。
    このハンドラにより、CHAR型カラムの値が自動的にstrip()される。
    """
    if metadata.type_code is oracledb.DB_TYPE_CHAR:
        return cursor.var(
            str,
            arraysize=cursor.arraysize,
            outconverter=lambda val: val.strip() if val else val,
        )


class PoolManager:
    """ECOとHONPSの2つのコネクションプールを管理するシングルトン."""

    _eco_pool: oracledb.ConnectionPool | None = None
    _honps_pool: oracledb.ConnectionPool | None = None

    @classmethod
    def init(cls, eco_cfg: DbConfig, honps_cfg: DbConfig) -> None:
        """起動時に1回だけ呼ぶ。2つのプールを初期化する.

        古い Oracle DB (11g) に対応するため thick モードで動作。
        TNS名(例: ORAGOLD)の解決には config_dir で tnsnames.ora の場所を渡す。
        """
        _init_thick_mode()
        config_dir = _find_config_dir()
        if cls._eco_pool is None:
            cls._eco_pool = oracledb.create_pool(
                user=eco_cfg.user,
                password=eco_cfg.password,
                dsn=eco_cfg.dsn,
                min=eco_cfg.pool_min,
                max=eco_cfg.pool_max,
                increment=1,
                config_dir=config_dir,
            )
        if cls._honps_pool is None:
            cls._honps_pool = oracledb.create_pool(
                user=honps_cfg.user,
                password=honps_cfg.password,
                dsn=honps_cfg.dsn,
                min=honps_cfg.pool_min,
                max=honps_cfg.pool_max,
                increment=1,
                config_dir=config_dir,
            )

    @classmethod
    @contextmanager
    def eco_conn(cls) -> Generator[oracledb.Connection, None, None]:
        """ECOプールからコネクションを取得するコンテキストマネージャ."""
        if cls._eco_pool is None:
            raise RuntimeError("PoolManager未初期化。init()を先に呼んでください。")
        conn = cls._eco_pool.acquire()
        conn.outputtypehandler = _output_type_handler
        try:
            yield conn
        finally:
            cls._eco_pool.release(conn)

    @classmethod
    @contextmanager
    def honps_conn(cls) -> Generator[oracledb.Connection, None, None]:
        """HONPSプールからコネクションを取得するコンテキストマネージャ."""
        if cls._honps_pool is None:
            raise RuntimeError("PoolManager未初期化。init()を先に呼んでください。")
        conn = cls._honps_pool.acquire()
        conn.outputtypehandler = _output_type_handler
        try:
            yield conn
        finally:
            cls._honps_pool.release(conn)

    @classmethod
    def close(cls) -> None:
        """終了時にプールを閉じる."""
        if cls._eco_pool is not None:
            cls._eco_pool.close()
            cls._eco_pool = None
        if cls._honps_pool is not None:
            cls._honps_pool.close()
            cls._honps_pool = None


def chunk_list(items: list, size: int = 999) -> list[list]:
    """リストをOracleのIN句上限(1000)に合わせてチャンク分割する."""
    return [items[i:i + size] for i in range(0, len(items), size)]


def make_bind_placeholders(count: int) -> str:
    """バインド変数プレースホルダを生成する. 例: ':1, :2, :3'."""
    return ", ".join(f":{i + 1}" for i in range(count))
