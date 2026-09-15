from __future__ import annotations

import re
from typing import Any

from .catalog import get_rank
from .config import load_settings
from .db import get_admin_connection, get_connection, get_cursor


ENPC_NAMES = (
    "LMRAKCHI",
    "FASSI",
    "CASAWI",
    "MEKNESSI",
    "TANJAWE",
    "7ERBI",
    "AGADIRI",
    "TETOUANI",
    "FLIFLA",
    "SLAWI",
)
TETOUANI_INDEX = ENPC_NAMES.index("TETOUANI")
OUTFILE_RE = re.compile(
    r"(?is)^(?P<query>.+?)\s+INTO\s+(?:OUTFILE|DUMPFILE)\s+(?P<quote>['\"])(?P<path>.+?)(?P=quote)\s*;?\s*$"
)

TRIGGER_LABELS = {
    "eat_apple": "EATS AN APPLE",
    "eat_berry": "EATS A BERRY",
    "eat_carrot": "EATS A CARROT",
    "eat_snack_pack": "EATS A SNACK PACK",
    "drink_drink": "DRINKS A DRINK",
    "kick_ball": "KICKS THE BALL",
    "touch_enpc": "TOUCH ANOTHER ENPC",
}


def _ensure_architect(cur, user_id: int) -> None:
    cur.execute("SELECT score FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    if row is None:
        raise PermissionError("Unauthorized")
    if int(row["score"]) < 200:
        raise PermissionError("Architect rank required")


def grant_architect_reward_if_needed(user_id: int) -> bool:
    conn = get_connection()
    try:
        cur = get_cursor(conn, dictionary=True)
        cur.execute("START TRANSACTION")
        cur.execute("SELECT score FROM users WHERE id = %s FOR UPDATE", (user_id,))
        row = cur.fetchone()
        if row is None:
            conn.rollback()
            raise PermissionError("Unauthorized")
        if int(row["score"]) < 200:
            conn.rollback()
            return False

        cur.execute("INSERT IGNORE INTO architect_rewards (user_id) VALUES (%s)", (user_id,))
        if cur.rowcount == 0:
            conn.commit()
            return False

        cur.execute(
            """
            INSERT INTO inventory (user_id, item_id, quantity)
            VALUES (%s, 'ball', 15)
            ON DUPLICATE KEY UPDATE quantity = quantity + 15
            """,
            (user_id,),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_architect_lessons(user_id: int) -> dict[str, Any]:
    conn = get_connection()
    try:
        cur = get_cursor(conn, dictionary=True)
        _ensure_architect(cur, user_id)
        cur.execute(
            """
            SELECT npc_index, trigger_key, phrase
            FROM enpc_lessons
            WHERE user_id = %s
            ORDER BY npc_index, trigger_key
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        return {
            "names": list(ENPC_NAMES),
            "actions": [{"key": key, "label": label} for key, label in TRIGGER_LABELS.items()],
            "lessons": [
                {
                    "npc_index": int(row["npc_index"]),
                    "trigger": row["trigger_key"],
                    "phrase": row["phrase"],
                }
                for row in rows
            ],
        }
    finally:
        conn.close()


def _format_outfile_rows(rows: list[tuple[Any, ...]]) -> str:
    lines: list[str] = []
    for row in rows:
        rendered = "\t".join("" if value is None else str(value) for value in row)
        lines.append(rendered)
    return "\n".join(lines) + ("\n" if lines else "")


def _execute_tetouani_outfile(statement: str) -> bool:
    match = OUTFILE_RE.match(statement)
    if not match:
        return False

    select_sql = match.group("query").strip()
    if not select_sql:
        return False

    admin_conn = get_admin_connection()
    try:
        admin_cur = get_cursor(admin_conn, dictionary=False)
        admin_cur.execute(select_sql)
        rows = list(admin_cur.fetchall())
    finally:
        admin_conn.close()

    target_path = load_settings().root_dir / "flag.txt"
    target_path.write_text(_format_outfile_rows(rows), encoding="utf-8")
    return True


def _save_lesson_statement(cur, user_id: int, npc_index: int, trigger: str, phrase: str) -> None:
    if npc_index == TETOUANI_INDEX:
        # TETOUANI intentionally uses the unsafe authoring path for the challenge.
        normalized = phrase.lstrip()
        if _execute_tetouani_outfile(normalized):
            normalized = ""
        head = normalized.split(None, 1)[0].upper() if normalized else ""
        if head in {"SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "WITH", "SET"}:
            admin_conn = get_admin_connection()
            try:
                admin_cur = get_cursor(admin_conn, dictionary=True)
                result_iter = admin_cur.execute(normalized, multi=True)
                if result_iter is not None:
                    for _ in result_iter:
                        pass
                admin_conn.commit()
            except Exception:
                admin_conn.rollback()
                raise
            finally:
                admin_conn.close()

    cur.execute(
        """
        INSERT IGNORE INTO enpc_lessons (user_id, npc_index, trigger_key, phrase)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE phrase = VALUES(phrase)
        """,
        (user_id, npc_index, trigger, phrase),
    )


def save_architect_lesson(user_id: int, npc_index: int, trigger: str, phrase: str) -> dict[str, Any]:
    cleaned_phrase = phrase.strip()
    if trigger not in TRIGGER_LABELS:
        raise ValueError("Unknown architect trigger")
    if npc_index < 0 or npc_index >= len(ENPC_NAMES):
        raise ValueError("Unknown ENPC")
    if not cleaned_phrase or len(cleaned_phrase) > 100:
        raise ValueError("Phrase must be between 1 and 100 characters")

    conn = get_connection()
    try:
        cur = get_cursor(conn, dictionary=True)
        cur.execute("START TRANSACTION")
        _ensure_architect(cur, user_id)
        cur.execute(
            """
            SELECT 1
            FROM enpc_lessons
            WHERE user_id = %s AND npc_index = %s AND trigger_key = %s
            FOR UPDATE
            """,
            (user_id, npc_index, trigger),
        )
        had_lesson = cur.fetchone() is not None
        _save_lesson_statement(cur, user_id, npc_index, trigger, cleaned_phrase)
        cur.execute(
            """
            SELECT 1
            FROM enpc_lessons
            WHERE user_id = %s AND npc_index = %s AND trigger_key = %s
            """,
            (user_id, npc_index, trigger),
        )
        lesson_exists = cur.fetchone() is not None

        score_gained = 0
        bits_gained = 0
        if not had_lesson and lesson_exists:
            score_gained = 2
            bits_gained = 2
            cur.execute("SELECT bits, score FROM users WHERE id = %s FOR UPDATE", (user_id,))
            user_row = cur.fetchone()
            if user_row is None:
                raise PermissionError("Unauthorized")
            new_bits = int(user_row["bits"]) + bits_gained
            new_score = int(user_row["score"]) + score_gained
            cur.execute(
                "UPDATE users SET bits = %s, score = %s WHERE id = %s",
                (new_bits, new_score, user_id),
            )
        else:
            cur.execute(
                """
                UPDATE enpc_lessons
                SET phrase = %s
                WHERE user_id = %s AND npc_index = %s AND trigger_key = %s
                """,
                (cleaned_phrase, user_id, npc_index, trigger),
            )
            cur.execute("SELECT bits, score FROM users WHERE id = %s", (user_id,))
            user_row = cur.fetchone()
            if user_row is None:
                raise PermissionError("Unauthorized")
            new_bits = int(user_row["bits"])
            new_score = int(user_row["score"])

        conn.commit()
        return {
            "message": "Lesson saved!",
            "npc_index": npc_index,
            "trigger": trigger,
            "phrase": cleaned_phrase,
            "bits_gained": bits_gained,
            "new_bits": new_bits,
            "score_gained": score_gained,
            "new_score": new_score,
            "new_rank": get_rank(new_score),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
