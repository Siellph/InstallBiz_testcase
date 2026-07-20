import sqlite3
from contextlib import contextmanager

_db_path = 'app_data.sqlite3'


def init_db(db_path):
    global _db_path
    _db_path = db_path
    with _get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                name TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                downloaded_at TEXT NOT NULL
            )
            ''')
        conn.commit()


@contextmanager
def _get_conn():
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_file(name: str, content: str, downloaded_at: str):
    with _get_conn() as conn:
        conn.execute(
            'INSERT OR REPLACE INTO files (name, content, downloaded_at) VALUES (?, ?, ?)',
            (name, content, downloaded_at),
        )
        conn.commit()


def get_files_page(page: int, per_page: int, sort_dir: str = 'desc'):
    order = 'ASC' if sort_dir == 'asc' else 'DESC'
    offset = max(0, (page - 1) * per_page)

    with _get_conn() as conn:
        rows = conn.execute(
            f'SELECT name, downloaded_at FROM files ORDER BY downloaded_at {order} LIMIT ? OFFSET ?',
            (per_page, offset),
        ).fetchall()
        total = conn.execute('SELECT COUNT(*) AS c FROM files').fetchone()['c']

    return [dict(r) for r in rows], total


def get_files_content(names: list) -> dict:
    if not names:
        return {}
    placeholders = ','.join('?' for _ in names)
    with _get_conn() as conn:
        rows = conn.execute(
            f'SELECT name, content FROM files WHERE name IN ({placeholders})',
            names,
        ).fetchall()
    return {r['name']: r['content'] for r in rows}


def get_known_names() -> set:
    with _get_conn() as conn:
        rows = conn.execute('SELECT name FROM files').fetchall()
    return {r['name'] for r in rows}


def get_all_names() -> list:
    with _get_conn() as conn:
        rows = conn.execute('SELECT name FROM files ORDER BY downloaded_at DESC').fetchall()
    return [r['name'] for r in rows]
