"""SQLite-backed profile storage for the local portfolio dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3


@dataclass(frozen=True)
class ProfileHoldingInput:
    """A user-provided holding row stored in a profile."""

    symbol: str
    average_cost: float
    shares: int


def initialize_profile_store(database_path: str | Path) -> Path | str:
    """Create the profile database and required tables when missing."""

    path = _normalize_database_path(database_path)
    if not _is_sqlite_uri(path):
        path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cash REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS profile_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                average_cost REAL NOT NULL,
                shares INTEGER NOT NULL,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_profile_holdings_profile_id
            ON profile_holdings(profile_id)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS profile_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_profile_logs_profile_id
            ON profile_logs(profile_id)
            """
        )
    return path


def create_profile(
    database_path: str | Path,
    *,
    name: str,
    cash: float,
    holdings: list[ProfileHoldingInput],
) -> int:
    """Persist a new profile and return its identifier."""

    if not name.strip():
        raise ValueError("Profile name cannot be empty.")
    if cash < 0:
        raise ValueError("Cash cannot be negative.")

    with _connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO profiles (name, cash)
            VALUES (?, ?)
            """,
            (name.strip(), float(cash)),
        )
        profile_id = int(cursor.lastrowid)
        connection.executemany(
            """
            INSERT INTO profile_holdings (profile_id, symbol, average_cost, shares)
            VALUES (?, ?, ?, ?)
            """,
            [
                (profile_id, holding.symbol.upper().strip(), float(holding.average_cost), int(holding.shares))
                for holding in holdings
            ],
        )
        _insert_profile_log(
            connection,
            profile_id=profile_id,
            action_type="create",
            note="Profile created.",
            snapshot=_snapshot_payload(profile_id=profile_id, name=name.strip(), cash=float(cash), holdings=holdings),
        )
    return profile_id


def update_profile(
    database_path: str | Path,
    *,
    profile_id: int,
    name: str,
    cash: float,
    holdings: list[ProfileHoldingInput],
    log_action: bool = True,
) -> None:
    """Replace a profile's core fields and holding rows."""

    if not name.strip():
        raise ValueError("Profile name cannot be empty.")
    if cash < 0:
        raise ValueError("Cash cannot be negative.")

    with _connect(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE profiles
            SET name = ?, cash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (name.strip(), float(cash), int(profile_id)),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Profile {profile_id} does not exist.")

        connection.execute(
            """
            DELETE FROM profile_holdings
            WHERE profile_id = ?
            """,
            (int(profile_id),),
        )
        connection.executemany(
            """
            INSERT INTO profile_holdings (profile_id, symbol, average_cost, shares)
            VALUES (?, ?, ?, ?)
            """,
            [
                (int(profile_id), holding.symbol.upper().strip(), float(holding.average_cost), int(holding.shares))
                for holding in holdings
            ],
        )
        if log_action:
            _insert_profile_log(
                connection,
                profile_id=int(profile_id),
                action_type="edit",
                note="Profile manually updated.",
                snapshot=_snapshot_payload(profile_id=int(profile_id), name=name.strip(), cash=float(cash), holdings=holdings),
            )


def list_profiles(database_path: str | Path) -> list[dict[str, object]]:
    """Return profile summaries ordered by most recently updated."""

    with _connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                p.id,
                p.name,
                p.cash,
                p.created_at,
                p.updated_at,
                COUNT(h.id) AS holding_count
            FROM profiles AS p
            LEFT JOIN profile_holdings AS h
                ON h.profile_id = p.id
            GROUP BY p.id
            ORDER BY p.updated_at DESC, p.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_profile(database_path: str | Path, profile_id: int) -> dict[str, object] | None:
    """Return a full profile payload with holdings."""

    with _connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        profile_row = connection.execute(
            """
            SELECT id, name, cash, created_at, updated_at
            FROM profiles
            WHERE id = ?
            """,
            (int(profile_id),),
        ).fetchone()
        if profile_row is None:
            return None

        holdings = connection.execute(
            """
            SELECT symbol, average_cost, shares
            FROM profile_holdings
            WHERE profile_id = ?
            ORDER BY symbol ASC
            """,
            (int(profile_id),),
        ).fetchall()

    profile = dict(profile_row)
    profile["holdings"] = [dict(row) for row in holdings]
    return profile


def list_profile_logs(database_path: str | Path, profile_id: int) -> list[dict[str, object]]:
    """Return profile log entries newest-first."""

    with _connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, profile_id, action_type, note, snapshot_json, created_at
            FROM profile_logs
            WHERE profile_id = ?
            ORDER BY id DESC
            """,
            (int(profile_id),),
        ).fetchall()
    logs = [dict(row) for row in rows]
    for log in logs:
        log["snapshot"] = json.loads(log["snapshot_json"])
    return logs


def get_profile_log(database_path: str | Path, log_id: int) -> dict[str, object] | None:
    """Return one profile log entry."""

    with _connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT id, profile_id, action_type, note, snapshot_json, created_at
            FROM profile_logs
            WHERE id = ?
            """,
            (int(log_id),),
        ).fetchone()
    if row is None:
        return None
    payload = dict(row)
    payload["snapshot"] = json.loads(payload["snapshot_json"])
    return payload


def append_profile_log(
    database_path: str | Path,
    *,
    profile_id: int,
    action_type: str,
    note: str,
    snapshot: dict[str, object],
) -> None:
    """Append a log entry for an existing profile."""

    with _connect(database_path) as connection:
        _insert_profile_log(
            connection,
            profile_id=int(profile_id),
            action_type=action_type,
            note=note,
            snapshot=snapshot,
        )


def restore_profile_from_log(database_path: str | Path, *, profile_id: int, log_id: int) -> None:
    """Restore a profile to a previous logged snapshot."""

    log_entry = get_profile_log(database_path, log_id)
    if log_entry is None:
        raise ValueError(f"Log {log_id} does not exist.")
    if int(log_entry["profile_id"]) != int(profile_id):
        raise ValueError("Log does not belong to the requested profile.")

    snapshot = log_entry["snapshot"]
    holdings = [
        ProfileHoldingInput(
            symbol=str(row["symbol"]),
            average_cost=float(row["average_cost"]),
            shares=int(row["shares"]),
        )
        for row in snapshot["holdings"]
    ]
    update_profile(
        database_path,
        profile_id=int(profile_id),
        name=str(snapshot["name"]),
        cash=float(snapshot["cash"]),
        holdings=holdings,
        log_action=False,
    )
    append_profile_log(
        database_path,
        profile_id=int(profile_id),
        action_type="rollback",
        note=f"Profile restored from log #{int(log_id)}.",
        snapshot=_snapshot_payload(
            profile_id=int(profile_id),
            name=str(snapshot["name"]),
            cash=float(snapshot["cash"]),
            holdings=holdings,
        ),
    )


def _normalize_database_path(database_path: str | Path) -> Path | str:
    if isinstance(database_path, Path):
        return database_path
    if str(database_path).startswith("file:"):
        return str(database_path)
    return Path(database_path)


def _is_sqlite_uri(database_path: Path | str) -> bool:
    return isinstance(database_path, str) and database_path.startswith("file:")


def _connect(database_path: str | Path) -> sqlite3.Connection:
    normalized = _normalize_database_path(database_path)
    return sqlite3.connect(normalized, uri=_is_sqlite_uri(normalized))


def _snapshot_payload(
    *,
    profile_id: int,
    name: str,
    cash: float,
    holdings: list[ProfileHoldingInput],
) -> dict[str, object]:
    return {
        "profile_id": int(profile_id),
        "name": name,
        "cash": float(cash),
        "holdings": [
            {
                "symbol": holding.symbol.upper().strip(),
                "average_cost": float(holding.average_cost),
                "shares": int(holding.shares),
            }
            for holding in holdings
        ],
    }


def _insert_profile_log(
    connection: sqlite3.Connection,
    *,
    profile_id: int,
    action_type: str,
    note: str,
    snapshot: dict[str, object],
) -> None:
    connection.execute(
        """
        INSERT INTO profile_logs (profile_id, action_type, note, snapshot_json)
        VALUES (?, ?, ?, ?)
        """,
        (int(profile_id), action_type, note, json.dumps(snapshot)),
    )
