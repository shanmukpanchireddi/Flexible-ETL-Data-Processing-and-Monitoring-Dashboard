import io
import json
import sqlite3
import html
from pathlib import Path

import pandas as pd
import streamlit as st

from etl import REQUIRED_HEADERS, make_run_id, parse_rows
from sqlite_load import (
    DB_PATH,
    init_db,
    load_cleaned_rows,
    load_rejected_rows,
)

PROJECT_DIR = Path(__file__).parent
DB_FILE = PROJECT_DIR / DB_PATH

st.set_page_config(
    page_title="Flexible ETL Data Monitor",
    page_icon="🔄",
    layout="wide",
)

# =========================================================
# STYLING
# =========================================================

st.markdown("""
<style>
.block-container {
    padding-top: 1.6rem;
    padding-bottom: 2rem;
}

.hero {
    padding: 1.5rem;
    border-radius: 16px;
    background: linear-gradient(120deg, #102a43, #176b87);
    color: white;
    margin-bottom: 1.2rem;
}

.hero h1 {
    color: white !important;
    margin: 0 0 0.4rem 0;
}

.hero p {
    color: #e4f3f8 !important;
    margin: 0;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: 12px 0;
}

.metric-grid.two {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

.metric-grid.three {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.metric-card {
    box-sizing: border-box;
    min-height: 145px;
    padding: 18px 16px;
    border: 1px solid;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.metric-label {
    font-size: 16px;
    font-weight: 600;
    line-height: 1.4;
}

.metric-value {
    font-size: 32px;
    font-weight: 750;
    line-height: 1.2;
    margin: 10px 0;
}

.metric-help {
    font-size: 12px;
    line-height: 1.4;
}

.metric-blue {
    background: #e3f2fd;
    border-color: #90caf9;
    color: #1554a6;
}

.metric-green {
    background: #e8f5e9;
    border-color: #a5d6a7;
    color: #216e32;
}

.metric-red {
    background: #ffebee;
    border-color: #ef9a9a;
    color: #b71c1c;
}

.metric-orange {
    background: #fff3e0;
    border-color: #ffcc80;
    color: #bf4d00;
}

.metric-card .metric-help {
    color: inherit;
}

@media (max-width: 700px) {
    .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .metric-grid.two,
    .metric-grid.three {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
</style>

<div class="hero">
    <h1>Flexible ETL Data Monitor</h1>
    <p>Upload CSV data · configure validation · inspect clean and rejected records</p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# REUSABLE COLOURED METRIC CARDS
# =========================================================

def show_metrics(cards, columns=4):
    grid_class = {
        2: "two",
        3: "three",
        4: "",
    }.get(columns, "")

    card_html = []

    for label, value, help_text, colour in cards:
        card_html.append(
            f'<div class="metric-card metric-{colour}">'
            f'<div class="metric-label">{html.escape(str(label))}</div>'
            f'<div class="metric-value">{html.escape(str(value))}</div>'
            f'<div class="metric-help">{html.escape(str(help_text))}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="metric-grid {grid_class}">'
        + "".join(card_html)
        + '</div>',
        unsafe_allow_html=True,
    )
# =========================================================
# SIDEBAR AND PROCESSING MODE
# =========================================================

st.write(
    "Upload different CSV datasets and configure validation rules "
    "for student, customer, inventory, sales, or transaction records. "
    "Choose the checks appropriate for your dataset."
)

mode = st.radio(
    "Processing mode",
    [
        "Generic CSV mode (any columns)",
        "Transaction mode (original project rules)",
    ],
    horizontal=True,
)

with st.sidebar:
    st.header("ETL workflow")
    st.markdown("1. **Extract** — read the CSV")
    st.markdown("2. **Transform** — clean selected fields")
    st.markdown("3. **Validate** — apply validation rules")
    st.markdown("4. **Load** — save results in SQLite")
    st.divider()
    st.caption(
        "Generic mode supports different CSV column names. "
        "Your file must have a readable header row."
    )


# =========================================================
# CSV INPUT
# =========================================================

uploaded = st.file_uploader(
    "Upload a CSV file",
    type=["csv"],
    key="csv_uploader",
)

use_sample = False

if uploaded is None and mode.startswith("Transaction"):
    use_sample = st.checkbox(
        "Use the project's sample raw.csv",
        value=True,
    )
elif uploaded is None:
    st.info(
        "Upload a CSV file to begin. Example headers: "
        "student_id,name,age,marks or customer_id,name,city."
    )

source_bytes = uploaded.getvalue() if uploaded is not None else b""
source_name = uploaded.name if uploaded is not None else ""

if use_sample:
    sample_path = PROJECT_DIR / "raw.csv"

    if sample_path.exists():
        source_bytes = sample_path.read_bytes()
        source_name = "raw.csv (project sample)"


def parse_csv_bytes(file_bytes):
    try:
        frame = pd.read_csv(
            io.BytesIO(file_bytes),
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
    except Exception as exc:
        raise ValueError(
            f"Could not read this CSV file: {exc}"
        ) from exc

    if len(frame.columns) == 0:
        raise ValueError("The CSV has no header columns.")

    columns = [str(column).strip() for column in frame.columns]

    if any(not column for column in columns):
        raise ValueError(
            "Every column must have a non-empty header name."
        )

    if len(set(columns)) != len(columns):
        raise ValueError(
            "Column names must be unique after trimming spaces."
        )

    frame.columns = columns
    return frame


source_df = None

if source_bytes:
    try:
        source_df = parse_csv_bytes(source_bytes)

        st.subheader("1 · Source data preview")
        st.caption(
            f"Source: {source_name} · "
            f"{len(source_df)} data row(s) · "
            f"{len(source_df.columns)} column(s)"
        )

        st.dataframe(
            source_df.head(100),
            use_container_width=True,
            hide_index=True,
        )

        if len(source_df) > 100:
            st.caption(
                "Showing the first 100 rows. "
                "The pipeline processes all rows."
            )

    except ValueError as exc:
        st.error(str(exc))


# =========================================================
# GENERIC SQLITE STORAGE
# =========================================================

def ensure_generic_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS generic_etl_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                record_status TEXT NOT NULL,
                error_reason TEXT,
                row_json TEXT NOT NULL,
                source_file TEXT
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_generic_etl_run
            ON generic_etl_records(run_id)
        """)

        conn.commit()


def save_generic_records(
    run_id,
    source,
    clean_records,
    rejected_records,
):
    ensure_generic_db()
    rows = []

    for record in clean_records:
        rows.append((
            run_id,
            "clean",
            None,
            json.dumps(record, ensure_ascii=False),
            source,
        ))

    for record in rejected_records:
        data = {
            key: value
            for key, value in record.items()
            if key != "error_reason"
        }

        rows.append((
            run_id,
            "rejected",
            record.get("error_reason", "validation_error"),
            json.dumps(data, ensure_ascii=False),
            source,
        ))

    with sqlite3.connect(DB_FILE) as conn:
        conn.executemany(
            """
            INSERT INTO generic_etl_records
            (run_id, record_status, error_reason, row_json, source_file)
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()


# =========================================================
# CONFIGURABLE VALIDATION
# =========================================================

if source_df is not None and mode.startswith("Generic"):

    st.subheader("2 · Configure validation rules")

    columns = list(source_df.columns)
    left, right = st.columns(2)

    with left:
        required_columns = st.multiselect(
            "Columns that must not be empty",
            options=columns,
            help="Rows missing these values will be rejected.",
        )

        numeric_columns = st.multiselect(
            "Columns that must contain numbers",
            options=columns,
            help="Select fields such as age, marks, price or quantity.",
        )

    with right:
        duplicate_column = st.selectbox(
            "Optional column for duplicate detection",
            options=["(Do not check duplicates)"] + columns,
            help="For example, student_id or customer_id.",
        )

        trim_values = st.checkbox(
            "Trim leading/trailing spaces",
            value=True,
        )

    st.caption(
        "Choose validation rules that make sense for your dataset."
    )

    run_clicked = st.button(
        "▶ Run configurable ETL pipeline",
        type="primary",
    )

elif source_df is not None and mode.startswith("Transaction"):

    st.subheader("2 · Transaction validation")

    st.caption(
        "Validates transaction IDs, numeric amounts, "
        "three-letter currencies and duplicate transaction IDs."
    )

    run_clicked = st.button(
        "▶ Run transaction ETL pipeline",
        type="primary",
    )

else:
    run_clicked = False


# =========================================================
# EXECUTE PIPELINE
# =========================================================

if run_clicked and source_df is not None:

    run_id = make_run_id()

    try:
        if mode.startswith("Generic"):

            clean_records = []
            rejected_records = []
            seen = set()

            for row in source_df.to_dict(orient="records"):

                record = {
                    str(key): (
                        str(value).strip()
                        if trim_values and isinstance(value, str)
                        else value
                    )
                    for key, value in row.items()
                }

                errors = []

                for column in required_columns:
                    if str(record.get(column, "")).strip() == "":
                        errors.append(f"missing_value:{column}")

                for column in numeric_columns:
                    value = str(record.get(column, "")).strip()

                    if value == "":
                        errors.append(
                            f"missing_numeric_value:{column}"
                        )
                    else:
                        try:
                            float(value.replace(",", ""))
                        except ValueError:
                            errors.append(f"not_numeric:{column}")

                if duplicate_column != "(Do not check duplicates)":

                    key = str(
                        record.get(duplicate_column, "")
                    ).strip()

                    if key and key in seen:
                        errors.append(
                            f"duplicate_value:{duplicate_column}"
                        )
                    elif key:
                        seen.add(key)

                if errors:
                    rejected_records.append({
                        **record,
                        "error_reason": "; ".join(errors),
                    })
                else:
                    clean_records.append(record)

            save_generic_records(
                run_id,
                source_name,
                clean_records,
                rejected_records,
            )

            st.session_state["etl_result"] = {
                "mode": "generic",
                "run_id": run_id,
                "source_name": source_name,
                "input_count": len(source_df),
                "clean_records": clean_records,
                "rejected_records": rejected_records,
            }

        else:

            rows = source_df.to_dict(orient="records")
            missing = REQUIRED_HEADERS - set(source_df.columns)

            if missing:
                raise ValueError(
                    "Transaction mode requires transaction_id, "
                    "amount and currency. Missing columns: "
                    + ", ".join(sorted(missing))
                )

            clean_records, rejected_records = parse_rows(
                rows,
                run_id,
            )

            init_db(str(DB_FILE))

            load_cleaned_rows(
                str(DB_FILE),
                clean_records,
            )

            load_rejected_rows(
                str(DB_FILE),
                rejected_records,
            )

            st.session_state["etl_result"] = {
                "mode": "transaction",
                "run_id": run_id,
                "source_name": source_name,
                "input_count": len(rows),
                "clean_records": clean_records,
                "rejected_records": rejected_records,
            }

        st.success("ETL run completed. Review the results below.")

    except Exception as exc:
        st.error(f"Pipeline could not complete: {exc}")


# =========================================================
# RUN SUMMARY AND RESULTS
# =========================================================

result = st.session_state.get("etl_result")

if result:

    st.divider()
    st.subheader("3 · Run summary")

    clean_records = result["clean_records"]
    rejected_records = result["rejected_records"]
    total = result["input_count"]

    acceptance_rate = (
        len(clean_records) / total * 100
        if total
        else 0
    )

    # Coloured summary cards
    show_metrics([
        (
            "Input rows",
            total,
            "Total records read from the source CSV.",
            "blue",
        ),
        (
            "Accepted rows",
            len(clean_records),
            "Records that passed validation.",
            "green",
        ),
        (
            "Rejected rows",
            len(rejected_records),
            "Records that failed validation.",
            "red",
        ),
        (
            "Acceptance rate",
            f"{acceptance_rate:.1f}%",
            "Percentage of input records accepted.",
            "orange",
        ),
    ])

    st.caption(
        f"Run ID: {result['run_id']} · "
        f"Source: {result['source_name']}"
    )

    clean_df = pd.DataFrame(clean_records)
    rejected_df = pd.DataFrame(rejected_records)

    if (
        not rejected_df.empty
        and "error_reason" in rejected_df.columns
    ):
        reasons = (
            rejected_df["error_reason"]
            .value_counts()
            .rename_axis("Rejection reason")
            .reset_index(name="Count")
        )
    else:
        reasons = pd.DataFrame(
            columns=["Rejection reason", "Count"]
        )

    clean_tab, rejected_tab, profile_tab = st.tabs([
        "✅ Accepted records",
        "⚠️ Rejected records",
        "📊 Data profile",
    ])

    with clean_tab:

        if clean_df.empty:
            st.info("No records passed the selected validation rules.")
        else:
            st.dataframe(
                clean_df,
                use_container_width=True,
                hide_index=True,
            )

        st.download_button(
            "Download clean.csv",
            clean_df.to_csv(index=False).encode("utf-8-sig"),
            "clean.csv",
            "text/csv",
        )

    with rejected_tab:

        if not reasons.empty:
            st.markdown("**Rejection reasons**")
            st.dataframe(
                reasons,
                use_container_width=True,
                hide_index=True,
            )

        if rejected_df.empty:
            st.info("No records were rejected.")
        else:
            st.dataframe(
                rejected_df,
                use_container_width=True,
                hide_index=True,
            )

        st.download_button(
            "Download rejected.csv",
            rejected_df.to_csv(index=False).encode("utf-8-sig"),
            "rejected.csv",
            "text/csv",
        )

    with profile_tab:

        st.markdown("**Column summary for the uploaded dataset**")

        if source_df is not None:

            profile_rows = []

            for column in source_df.columns:
                series = source_df[column].astype(str).str.strip()
                numeric_values = pd.to_numeric(
                    series,
                    errors="coerce",
                )

                profile_rows.append({
                    "Column": column,
                    "Non-empty values": int((series != "").sum()),
                    "Empty values": int((series == "").sum()),
                    "Distinct values": int(
                        source_df[column].nunique(dropna=False)
                    ),
                    "Inferred type": (
                        "Numeric-like"
                        if numeric_values.notna().any()
                        else "Text / mixed"
                    ),
                })

            st.dataframe(
                pd.DataFrame(profile_rows),
                use_container_width=True,
                hide_index=True,
            )

    # =====================================================
    # SQLITE STORAGE
    # =====================================================

    st.divider()
    st.subheader("4 · SQLite storage")

    if result["mode"] == "generic":

        ensure_generic_db()

        with sqlite3.connect(DB_FILE) as conn:

            counts = pd.read_sql_query(
                """
                SELECT record_status, COUNT(*) AS records
                FROM generic_etl_records
                WHERE run_id = ?
                GROUP BY record_status
                """,
                conn,
                params=(result["run_id"],),
            )

            stored_total = conn.execute(
                """
                SELECT COUNT(*)
                FROM generic_etl_records
                WHERE run_id = ?
                """,
                (result["run_id"],),
            ).fetchone()[0]

        clean_stored = (
            int(
                counts.loc[
                    counts["record_status"] == "clean",
                    "records",
                ].sum()
            )
            if not counts.empty
            else 0
        )

        rejected_stored = (
            int(
                counts.loc[
                    counts["record_status"] == "rejected",
                    "records",
                ].sum()
            )
            if not counts.empty
            else 0
        )

        show_metrics([
            (
                "Total clean rows stored",
                clean_stored,
                "Accepted records stored for this run.",
                "green",
            ),
            (
                "Total rejected rows stored",
                rejected_stored,
                "Rejected records stored for this run.",
                "red",
            ),
        ], columns=2)

        st.caption(
            "Generic records are stored as JSON in the "
            "generic_etl_records SQLite table to preserve "
            "different CSV column structures."
        )

    else:

        with sqlite3.connect(DB_FILE) as conn:

            clean_stored = conn.execute(
                "SELECT COUNT(*) FROM clean_transactions"
            ).fetchone()[0]

            rejected_stored = conn.execute(
                "SELECT COUNT(*) FROM rejected_transactions"
            ).fetchone()[0]

        show_metrics([
            (
                "Total clean rows stored",
                clean_stored,
                "Accepted transaction records in the database.",
                "green",
            ),
            (
                "Total rejected rows stored",
                rejected_stored,
                "Rejected transaction records in the database.",
                "red",
            ),
        ], columns=2)

        st.caption(
            "Transaction-mode database totals include records "
            "from previous runs too."
        )

st.divider()

st.caption(
    "Generic mode supports different CSV structures, but it does "
    "not automatically understand every dataset's business rules. "
    "Configure required, numeric and duplicate checks for your data."
)

# ==============================================
# SQLITE DATABASE RECORD VIEWER
# ==============================================

st.markdown("### Database Records")

import sqlite3

try:
    conn = sqlite3.connect(DB_PATH)

    with st.expander("View recent clean database records"):
        clean_df = pd.read_sql_query(
            """
            SELECT transaction_id, amount, currency, run_id
            FROM clean_transactions
            ORDER BY rowid DESC
            LIMIT 100
            """,
            conn
        )

        if clean_df.empty:
            st.info("No clean records available.")
        else:
            st.dataframe(
                clean_df,
                use_container_width=True,
                hide_index=True
            )

    with st.expander("View recent rejected database records"):
        rejected_df = pd.read_sql_query(
            """
            SELECT transaction_id, amount, currency,
                   error_reason, run_id
            FROM rejected_transactions
            ORDER BY rowid DESC
            LIMIT 100
            """,
            conn
        )

        if rejected_df.empty:
            st.info("No rejected records available.")
        else:
            st.dataframe(
                rejected_df,
                use_container_width=True,
                hide_index=True
            )

except sqlite3.Error as e:
    st.error(f"Database error: {e}")

finally:
    if "conn" in locals():
        conn.close()