from __future__ import annotations

import threading
from functools import lru_cache

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

from .config import load_settings


_pool_lock = threading.Lock()


@lru_cache(maxsize=1)
def get_pool() -> MySQLConnectionPool:
    settings = load_settings()
    with _pool_lock:
        # A small shared pool is enough here because the challenge runs a
        # single threaded-worker process and mostly short-lived requests.
        return MySQLConnectionPool(
            pool_name="enpc_pool",
            pool_size=10,
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_pass,
            database=settings.db_name,
            autocommit=False,
        )


def get_connection():
    return get_pool().get_connection()


def get_admin_connection():
    settings = load_settings()
    return mysql.connector.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_admin_user,
        password=settings.db_admin_pass,
        database=settings.db_name,
        autocommit=False,
    )


def get_cursor(conn, *, dictionary: bool = False):
    # Buffered cursors avoid "Unread result found" errors during back-to-back
    # reads in the challenge flows.
    return conn.cursor(dictionary=dictionary, buffered=True)
