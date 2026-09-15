from __future__ import annotations

from .db import get_connection, get_cursor


def ensure_runtime_schema() -> None:
    conn = get_connection()
    try:
        cur = get_cursor(conn)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS architect_rewards (
              user_id INT PRIMARY KEY,
              granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT fk_architect_rewards_user
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS enpc_lessons (
              id INT AUTO_INCREMENT PRIMARY KEY,
              user_id INT NOT NULL,
              npc_index TINYINT UNSIGNED NOT NULL,
              trigger_key VARCHAR(32) NOT NULL,
              phrase VARCHAR(100) NOT NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              UNIQUE KEY uq_enpc_lessons (user_id, npc_index, trigger_key),
              CONSTRAINT fk_enpc_lessons_user
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS flag (
              `key` VARCHAR(64) PRIMARY KEY,
              `value` VARCHAR(255) NOT NULL
            )
            """
        )
        cur.execute(
            """
            INSERT INTO flag (`key`, `value`)
            VALUES ('', 'NSC{Tet0uan1_g4lss_3La_Lfl4g}')
            ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)
            """
        )
        conn.commit()
    finally:
        conn.close()
