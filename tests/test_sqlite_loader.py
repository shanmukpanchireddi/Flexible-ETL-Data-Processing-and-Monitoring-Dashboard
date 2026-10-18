import os
import sqlite3
import subprocess

from sqlite_load import (
    init_db,
    read_rows_csv,
    load_cleaned_rows,
    load_rejected_rows,
)


def test_sqlite_loader_rerun_safe():
    db_path = "test_etl.db"

    if os.path.exists(db_path):
        os.remove(db_path)

    subprocess.run(["python", "etl.py"], check=True)

    cleaned_rows = read_rows_csv("clean.csv")
    rejected_rows = read_rows_csv("rejected.csv")

    init_db(db_path)

    load_cleaned_rows(db_path, cleaned_rows)
    load_rejected_rows(db_path, rejected_rows)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM clean_transactions")
    clean_count_first = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rejected_transactions")
    rejected_count_first = cur.fetchone()[0]

    conn.close()

    load_cleaned_rows(db_path, cleaned_rows)
    load_rejected_rows(db_path, rejected_rows)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM clean_transactions")
    clean_count_second = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rejected_transactions")
    rejected_count_second = cur.fetchone()[0]

    conn.close()

    clean_csv_count = len(cleaned_rows)
    rejected_csv_count = len(rejected_rows)

    assert clean_count_first == clean_csv_count
    assert rejected_count_first == rejected_csv_count
    assert clean_count_second == clean_count_first
    assert rejected_count_second == rejected_count_first

    if os.path.exists(db_path):
        os.remove(db_path)