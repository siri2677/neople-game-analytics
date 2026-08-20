"""Load processed CSV files into PostgreSQL for SQL and Power BI analysis."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from .io_utils import PROCESSED_DIR, ROOT


TABLES: list[tuple[str, str, list[str]]] = [
    (
        "dnf_character_snapshot.csv",
        "dnf_character_snapshot",
        [
            "game_code", "snapshot_date", "server_id", "character_id", "character_name",
            "level", "job_id", "job_grow_id", "job_name", "job_grow_name", "fame", "source",
        ],
    ),
    (
        "dnf_equipment.csv",
        "dnf_equipment",
        [
            "game_code", "collected_at", "character_id", "item_id", "item_name", "slot_id",
            "slot_name", "rarity", "reinforce", "refine",
        ],
    ),
    (
        "dnf_auction_sold.csv",
        "dnf_auction_sold",
        [
            "game_code", "collected_at", "item_id", "item_name", "sold_date", "unit_price",
            "average_price", "count",
        ],
    ),
    (
        "dnf_timeline.csv",
        "dnf_timeline",
        [
            "game_code", "collected_at", "character_id", "event_date", "event_code",
            "event_name", "event_data",
        ],
    ),
    ("cyphers_player.csv", "cyphers_player", ["game_code", "collected_at", "player_id", "nickname"]),
    (
        "cyphers_match.csv",
        "cyphers_match",
        ["game_code", "collected_at", "player_id", "match_id", "match_date", "game_type"],
    ),
    (
        "cyphers_player_match_performance.csv",
        "cyphers_player_match_performance",
        [
            "game_code", "collected_at", "match_id", "player_id", "nickname", "character_id",
            "character_name", "team", "result", "kill_count", "death_count", "assist_count",
        ],
    ),
    (
        "cyphers_match_item.csv",
        "cyphers_match_item",
        [
            "game_code", "collected_at", "match_id", "player_id", "character_id", "item_id",
            "item_name", "slot_code",
        ],
    ),
]


def connection_kwargs() -> dict[str, str | int]:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "neople"),
        "user": os.getenv("POSTGRES_USER", "neople"),
        "password": os.getenv("POSTGRES_PASSWORD", "neople_local_only"),
    }


def sql_file(name: str) -> str:
    return (ROOT / "sql" / name).read_text(encoding="utf-8")


def copy_sql(table: str, columns: list[str]) -> str:
    column_sql = ", ".join(columns)
    return (
        f"COPY neople.{table} ({column_sql}) FROM STDIN "
        "WITH (FORMAT CSV, HEADER TRUE, NULL '', QUOTE '\"', ESCAPE '\"')"
    )


def load_csv(cursor: psycopg.Cursor, path: Path, table: str, columns: list[str]) -> int:
    if not path.exists():
        return 0
    with cursor.copy(copy_sql(table, columns)) as copy, path.open("rb") as source:
        copy.write(source.read())
    cursor.execute(f"SELECT COUNT(*) FROM neople.{table}")
    return int(cursor.fetchone()[0])


def truncate_tables(cursor: psycopg.Cursor) -> None:
    names = ", ".join(f"neople.{table}" for _, table, _ in TABLES)
    cursor.execute(f"TRUNCATE TABLE {names}")


def load(mode: str) -> None:
    schema_sql = sql_file("01_schema.sql")
    views_sql = sql_file("03_views.sql")
    with psycopg.connect(**connection_kwargs()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema_sql)
            if mode == "replace":
                truncate_tables(cursor)
            loaded: dict[str, int] = {}
            for filename, table, columns in TABLES:
                loaded[table] = load_csv(cursor, PROCESSED_DIR / filename, table, columns)
            cursor.execute(views_sql)
        connection.commit()
    print("PostgreSQL load completed")
    for table, count in loaded.items():
        print(f"- {table}: {count:,} rows")


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["replace", "append"], default="replace")
    parser.add_argument("--init-only", action="store_true")
    args = parser.parse_args()
    if args.init_only:
        with psycopg.connect(**connection_kwargs()) as connection:
            connection.execute(sql_file("01_schema.sql"))
            connection.execute(sql_file("03_views.sql"))
            connection.commit()
        print("PostgreSQL schema and views initialized")
        return
    load(args.mode)


if __name__ == "__main__":
    main()
