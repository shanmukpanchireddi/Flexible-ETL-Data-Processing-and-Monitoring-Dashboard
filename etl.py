import csv
import logging
import argparse
from datetime import datetime


logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
) 
logger = logging.getLogger(__name__)

CLEAN_FIELDS = ["transaction_id", "amount", "currency", "run_id"]
REJECT_FIELDS = ["transaction_id", "amount", "currency", "error_reason", "run_id"]
REQUIRED_HEADERS = {"transaction_id", "amount", "currency"}

def read_rows_csv(path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)

        actual_headers = set(reader.fieldnames or [])
        missing = REQUIRED_HEADERS - actual_headers

        if missing:
            msg = f"Missing required CSV headers: {sorted(missing)} (found: {sorted(actual_headers)})"
            logger.error(msg)
            raise ValueError(msg)
        

        return list(reader)

def write_rows_csv(path, rows, fieldnames):
    with open(path,"w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def make_run_id():
    return datetime.now().isoformat(timespec="seconds")

def safe_float(s):
    s = str(s).strip()

    if s == "":
        return None
    try:
       return float(s)
    except ValueError:
        return None
    

def clean_currency(s):
    s = str(s).strip().upper()
    if s == "":
        return None

    if len(s) != 3:
        return None
    
    if not s.isalpha():
        return None
    
    return s

def clean_transaction_id(s):
    s = str(s).strip()
    if s == "":
        return None
    return s


def parse_row(row):
    tx_id = clean_transaction_id(row.get("transaction_id", ""))
    if tx_id is None:
        return None, "invalid_transaction_id"
    
    amount = safe_float(row.get("amount", ""))
    if amount is None:
        return None, "invalid_amount"
    
    currency = clean_currency(row.get("currency", ""))
    if currency is None:
        return None, "invalid_currency"
    
    return {"transaction_id": tx_id, "amount": amount,"currency": currency}, None

def parse_rows(rows, run_id):

    cleaned = []
    rejected = []
    seen_ids = set()

    for row in rows:
        out, err = parse_row(row)

        if err is not None:
            rejected.append({**row, "error_reason": err, "run_id": run_id})
            continue

        tx_id = out["transaction_id"]
        if tx_id in seen_ids:
            rejected.append({**row, "error_reason": "duplicate_transaction_id", "run_id": run_id})
            continue 

        seen_ids.add(tx_id)
        cleaned.append({**out, "run_id": run_id})

    return cleaned, rejected

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="raw.csv")
    parser.add_argument("--clean", default="clean.csv")
    parser.add_argument("--reject", default="rejected.csv")
    parser.add_argument("--run-id", dest="run_id", default=None)
    args = parser.parse_args()

    run_id = args.run_id or make_run_id()

    logger.info("run started run_id=%s", run_id)

    rows = read_rows_csv(args.input)
    cleaned, rejected = parse_rows(rows, run_id)

    logger.info("rows: input=%d cleaned=%d rejected=%d", len(rows), len(cleaned), len(rejected))

    write_rows_csv(args.clean, cleaned, CLEAN_FIELDS)
    write_rows_csv(args.reject, rejected, REJECT_FIELDS)

    logger.info("wrote outputs: clean=%s reject=%s", args.clean, args.reject)

if __name__ == "__main__":
    main()
