from __future__ import annotations

import threading
import time
from typing import Any

import bcrypt
import mysql.connector

from .architect import grant_architect_reward_if_needed
from .auth import issue_jwt
from .catalog import DELAYED_ITEMS, ITEMS, USERNAME_RE, get_rank
from .db import get_connection, get_cursor


_purchase_lock_guard = threading.Lock()
_purchase_locks: dict[tuple[int, str], threading.Lock] = {}


def get_purchase_lock(user_id: int, item_id: str) -> threading.Lock:
    key = (user_id, item_id)
    with _purchase_lock_guard:
        lock = _purchase_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _purchase_locks[key] = lock
        return lock


def normalize_inventory(rows: list[dict[str, Any]]) -> dict[str, int]:
    inventory = {item_id: 0 for item_id in ITEMS}
    for row in rows:
        item_id = row["item_id"]
        if item_id in inventory:
            inventory[item_id] = int(row["quantity"])
    return inventory


def fetch_user_bundle(user_id: int) -> dict[str, Any] | None:
    grant_architect_reward_if_needed(user_id)
    conn = get_connection()
    try:
        cur = get_cursor(conn, dictionary=True)
        cur.execute(
            "SELECT id, username, bits, score FROM users WHERE id = %s",
            (user_id,),
        )
        user = cur.fetchone()
        if user is None:
            return None

        cur.execute(
            "SELECT item_id, quantity FROM inventory WHERE user_id = %s",
            (user_id,),
        )
        inventory_rows = cur.fetchall()
        return {
            "id": int(user["id"]),
            "username": user["username"],
            "bits": int(user["bits"]),
            "score": int(user["score"]),
            "rank": get_rank(int(user["score"])),
            "inventory": normalize_inventory(inventory_rows),
        }
    finally:
        conn.close()


def create_user(username: str, password: str) -> tuple[str, dict[str, Any]]:
    if not USERNAME_RE.fullmatch(username):
        raise ValueError("Username must be 3-32 chars using letters, numbers, or _")
    if len(password) < 6 or len(password) > 72:
        raise ValueError("Password must be between 6 and 72 characters")

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, bits, score) VALUES (%s, %s, 65, 0)",
            (username, password_hash),
        )
        user_id = int(cur.lastrowid)
        conn.commit()
    except mysql.connector.IntegrityError as exc:
        conn.rollback()
        raise ValueError("Username already taken") from exc
    finally:
        conn.close()

    user = fetch_user_bundle(user_id)
    token = issue_jwt(user_id, username)
    return token, user


def authenticate_user(username: str, password: str) -> tuple[str, dict[str, Any]]:
    conn = get_connection()
    try:
        cur = get_cursor(conn, dictionary=True)
        cur.execute(
            "SELECT id, username, password FROM users WHERE username = %s",
            (username,),
        )
        user = cur.fetchone()
    finally:
        conn.close()

    if user is None or not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        raise PermissionError("Invalid credentials")

    user_id = int(user["id"])
    token = issue_jwt(user_id, user["username"])
    bundle = fetch_user_bundle(user_id)
    return token, bundle


def buy_store_item(user_id: int, item_id: str | None) -> dict[str, Any]:
    if item_id not in ITEMS:
        raise ValueError("Unknown item")

    if item_id in DELAYED_ITEMS:
        return _buy_delayed_item(user_id, item_id)
    return _buy_regular_item(user_id, item_id)


def _buy_delayed_item(user_id: int, item_id: str) -> dict[str, Any]:
    item = ITEMS[item_id]
    lock = get_purchase_lock(user_id, item_id)

    # This path is intentionally vulnerable: the balance is checked on one
    # connection, then a delayed stale write is performed on another one.
    with lock:
        check_conn = get_connection()
        try:
            cur = get_cursor(check_conn, dictionary=True)
            cur.execute("SELECT bits FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if row is None:
                raise PermissionError("Unauthorized")

            bits_before = int(row["bits"])
            if bits_before < item.cost:
                raise ValueError("Not enough bits")
        finally:
            check_conn.close()

        time.sleep(0.6)

        use_conn = get_connection()
        try:
            cur = get_cursor(use_conn, dictionary=True)
            stale_new_bits = bits_before - item.cost
            cur.execute(
                "UPDATE users SET bits = LEAST(bits, %s) WHERE id = %s",
                (stale_new_bits, user_id),
            )
            cur.execute(
                """
                INSERT INTO inventory (user_id, item_id, quantity)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE quantity = quantity + 1
                """,
                (user_id, item_id),
            )
            cur.execute("SELECT bits FROM users WHERE id = %s", (user_id,))
            bits_after = int(cur.fetchone()["bits"])
            cur.execute(
                """
                INSERT INTO purchase_log (user_id, item_id, bits_before, bits_after)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, item_id, bits_before, bits_after),
            )
            cur.execute(
                "SELECT quantity FROM inventory WHERE user_id = %s AND item_id = %s",
                (user_id, item_id),
            )
            quantity = int(cur.fetchone()["quantity"])
            use_conn.commit()
            return {
                "message": "Purchased!",
                "item_id": item_id,
                "bits": bits_after,
                "inventory_quantity": quantity,
            }
        except Exception:
            use_conn.rollback()
            raise
        finally:
            use_conn.close()


def _buy_regular_item(user_id: int, item_id: str) -> dict[str, Any]:
    item = ITEMS[item_id]
    conn = get_connection()
    try:
        cur = get_cursor(conn, dictionary=True)
        cur.execute("START TRANSACTION")
        cur.execute("SELECT bits FROM users WHERE id = %s FOR UPDATE", (user_id,))
        row = cur.fetchone()
        if row is None:
            conn.rollback()
            raise PermissionError("Unauthorized")

        bits_before = int(row["bits"])
        if bits_before < item.cost:
            conn.rollback()
            raise ValueError("Not enough bits")

        bits_after = bits_before - item.cost
        cur.execute(
            "UPDATE users SET bits = %s WHERE id = %s",
            (bits_after, user_id),
        )
        cur.execute(
            """
            INSERT INTO inventory (user_id, item_id, quantity)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE quantity = quantity + 1
            """,
            (user_id, item_id),
        )
        cur.execute(
            """
            INSERT INTO purchase_log (user_id, item_id, bits_before, bits_after)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, item_id, bits_before, bits_after),
        )
        cur.execute(
            "SELECT quantity FROM inventory WHERE user_id = %s AND item_id = %s",
            (user_id, item_id),
        )
        quantity = int(cur.fetchone()["quantity"])
        conn.commit()
        return {
            "message": "Purchased!",
            "item_id": item_id,
            "bits": bits_after,
            "inventory_quantity": quantity,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def feed_inventory_item(user_id: int, item_id: str | None) -> dict[str, Any]:
    if item_id not in ITEMS:
        raise ValueError("Unknown item")

    item = ITEMS[item_id]
    conn = get_connection()
    try:
        cur = get_cursor(conn, dictionary=True)
        cur.execute("START TRANSACTION")
        cur.execute(
            "SELECT quantity FROM inventory WHERE user_id = %s AND item_id = %s FOR UPDATE",
            (user_id, item_id),
        )
        inventory_row = cur.fetchone()
        quantity = int(inventory_row["quantity"]) if inventory_row else 0
        if quantity < 1:
            conn.rollback()
            raise ValueError("Item not in inventory")

        new_quantity = quantity - 1
        cur.execute(
            "UPDATE inventory SET quantity = %s WHERE user_id = %s AND item_id = %s",
            (new_quantity, user_id, item_id),
        )
        cur.execute("SELECT score FROM users WHERE id = %s FOR UPDATE", (user_id,))
        user_row = cur.fetchone()
        if user_row is None:
            conn.rollback()
            raise PermissionError("Unauthorized")

        new_score = int(user_row["score"]) + item.score
        cur.execute(
            "UPDATE users SET score = %s WHERE id = %s",
            (new_score, user_id),
        )
        conn.commit()
        reward_granted = grant_architect_reward_if_needed(user_id)
        return {
            "message": "Fed!",
            "item_id": item_id,
            "score_gained": item.score,
            "new_score": new_score,
            "new_rank": get_rank(new_score),
            "inventory_quantity": new_quantity,
            "architect_reward_balls": 15 if reward_granted else 0,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
