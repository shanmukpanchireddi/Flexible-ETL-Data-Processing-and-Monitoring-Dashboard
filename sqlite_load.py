import sqlite3
import csv

DB_PATH = "etl.db"

def read_rows_csv(path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clean_transactions (
            transaction_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            run_id TEXT NOT NULL,
            UNIQUE(transaction_id, run_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rejected_transactions (
            transaction_id TEXT,
            amount TEXT,
            currency TEXT,
            error_reason TEXT NOT NULL,
            run_id TEXT NOT NULL,
            UNIQUE(transaction_id, error_reason, run_id)
        )
    """)

    conn.commit()
    conn.close()

def load_cleaned_rows(db_path, cleaned_rows):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executemany(
        "INSERT OR IGNORE INTO clean_transactions (transaction_id, amount, currency, run_id) VALUES (?,?,?,?)",
        [(r["transaction_id"], r["amount"], r["currency"], r["run_id"]) for r in cleaned_rows]
    )

    conn.commit()
    conn.close()

def load_rejected_rows(db_path, rejected_rows):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executemany(
        "INSERT OR IGNORE INTO rejected_transactions (transaction_id, amount, currency, error_reason, run_id) VALUES (?,?,?,?,?)",
        [(r["transaction_id"], r["amount"], r["currency"], r["error_reason"], r["run_id"]) for r in rejected_rows]
    )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db(DB_PATH)

    cleaned_rows = read_rows_csv("clean.csv")
    rejected_rows = read_rows_csv("rejected.csv")

    load_cleaned_rows(DB_PATH, cleaned_rows)
    load_rejected_rows(DB_PATH, rejected_rows)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM clean_transactions")
    print("clean_total_rows:", cur.fetchone()[0])

    cur.execute("SELECT COUNT(*) FROM rejected_transactions")
    print("rejected_total_rows:", cur.fetchone()[0])

    conn.close()