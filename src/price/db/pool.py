"""コネクションプール管理.

VBAでは各サブルーチンが毎回myCon.Open/myCon.Closeしていたが、
本モジュールでプールを一括管理し、接続のオーバーヘッドを排除する。
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import oracledb

from price.config import DbConfig


class PoolManager:
    """ECOとHONPSの2つのコネクションプールを管理するシングルトン."""

    _eco_pool: oracledb.ConnectionPool | None = None
    _honps_pool: oracledb.ConnectionPool | None = None

    @classmethod
    def init(cls, eco_cfg: DbConfig, honps_cfg: DbConfig) -> None:
        """起動時に1回だけ呼ぶ。2つのプールを初期化する."""
        if cls._eco_pool is None:
            cls._eco_pool = oracledb.create_pool(
                user=eco_cfg.user,
                password=eco_cfg.password,
                dsn=eco_cfg.dsn,
                min=eco_cfg.pool_min,
                max=eco_cfg.pool_max,
                increment=1,
            )
        if cls._honps_pool is None:
            cls._honps_pool = oracledb.create_pool(
                user=honps_cfg.user,
                password=honps_cfg.password,
                dsn=honps_cfg.dsn,
                min=honps_cfg.pool_min,
                max=honps_cfg.pool_max,
                increment=1,
            )

    @classmethod
    @contextmanager
    def eco_conn(cls) -> Generator[oracledb.Connection, None, None]:
        """ECOプールからコネクションを取得するコンテキストマネージャ."""
        if cls._eco_pool is None:
            raise RuntimeError("PoolManager未初期化。init()を先に呼んでください。")
        conn = cls._eco_pool.acquire()
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
