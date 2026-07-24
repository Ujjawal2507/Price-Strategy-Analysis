"""
Phase 5 — Load cleaned data into MySQL

Requires a running MySQL instance and the schema in sql/schema.sql
already applied, e.g.:
    mysql -u <user> -p <db> < sql/schema.sql

Set connection details via environment variables or edit DB_URL /
DB_KWARGS below.

This version bulk-loads via `LOAD DATA LOCAL INFILE`, which is far
faster than row-by-row/multi-row INSERTs for large tables (typically
10-50x). It requires local_infile to be enabled on both the client
connection and the MySQL server (see NOTE below).
"""
import os
import sys
import time
import mysql.connector
from utils.file_utils import load_processed

DB_KWARGS = dict(
    host=os.environ.get("PRICE_ANALYSIS_DB_HOST", "localhost"),
    port=int(os.environ.get("PRICE_ANALYSIS_DB_PORT", "3306")),
    user=os.environ.get("PRICE_ANALYSIS_DB_USER", "root"),
    password=os.environ.get("PRICE_ANALYSIS_DB_PASSWORD", "Ujjawal@2511"),
    database=os.environ.get("PRICE_ANALYSIS_DB_NAME", "price_strategy_analysis"),
    allow_local_infile=True,
)

COLUMN_RENAME = {
    "household_key": "household_key", "BASKET_ID": "basket_id", "DAY": "day",
    "PRODUCT_ID": "product_id", "QUANTITY": "quantity", "SALES_VALUE": "sales_value",
    "STORE_ID": "store_id", "RETAIL_DISC": "retail_disc", "TRANS_TIME": "trans_time",
    "WEEK_NO": "week_no", "COUPON_DISC": "coupon_disc", "COUPON_MATCH_DISC": "coupon_match_disc",
}

PRODUCT_RENAME = {
    "PRODUCT_ID": "product_id", "MANUFACTURER": "manufacturer", "DEPARTMENT": "department",
    "BRAND": "brand", "COMMODITY_DESC": "commodity_desc",
    "SUB_COMMODITY_DESC": "sub_commodity_desc", "CURR_SIZE_OF_PRODUCT": "curr_size_of_product",
}

HOUSEHOLD_RENAME = {
    "household_key": "household_key", "AGE_DESC": "age_desc",
    "MARITAL_STATUS_CODE": "marital_status_code", "INCOME_DESC": "income_desc",
    "HOMEOWNER_DESC": "homeowner_desc", "HH_COMP_DESC": "hh_comp_desc",
    "HOUSEHOLD_SIZE_DESC": "household_size_desc", "KID_CATEGORY_DESC": "kid_category_desc",
}


def check_connection():
    """Fail fast with a clear message if MySQL isn't reachable, instead of
    hanging silently inside a later insert."""
    print(f"[check] connecting to {DB_KWARGS['host']}:{DB_KWARGS['port']} "
          f"as {DB_KWARGS['user']} ...", flush=True)
    start = time.time()
    try:
        conn = mysql.connector.connect(connection_timeout=10, **DB_KWARGS)
    except mysql.connector.Error as e:
        print(f"[FAILED] could not connect to MySQL: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"[ok] connected in {time.time() - start:.2f}s", flush=True)
    return conn


def bulk_load(conn, df, table, tmp_csv_path, disable_keys=False):
    """Write df to a temp CSV and bulk-load it into `table` with
    LOAD DATA LOCAL INFILE, printing progress before/after.

    If disable_keys=True (use for large tables like fact_transactions),
    temporarily disables FK/unique checks and secondary index maintenance
    during the load, then rebuilds them after. This is the standard
    speed-up for bulk-loading large InnoDB tables.
    """
    print(f"[load] {table}: writing {len(df):,} rows to temp CSV ...", flush=True)
    df.to_csv(tmp_csv_path, index=False, header=False)
    print(f"[load] {table}: starting import of {len(df):,} rows — "
          f"do not interrupt, this can take a few minutes for large tables.",
          flush=True)

    cols = ", ".join(df.columns)
    sql = f"""
        LOAD DATA LOCAL INFILE '{tmp_csv_path.as_posix()}'
        INTO TABLE {table}
        FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\\n'
        ({cols})
    """
    cursor = conn.cursor()
    start = time.time()

    if disable_keys:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("SET UNIQUE_CHECKS = 0")
        cursor.execute(f"ALTER TABLE {table} DISABLE KEYS")

    cursor.execute(sql)
    conn.commit()

    if disable_keys:
        print(f"[load] {table}: rebuilding indexes ...", flush=True)
        cursor.execute(f"ALTER TABLE {table} ENABLE KEYS")
        cursor.execute("SET UNIQUE_CHECKS = 1")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()

    elapsed = time.time() - start
    print(f"[done] {table}: loaded {cursor.rowcount:,} rows in {elapsed:.1f}s "
          f"({cursor.rowcount / max(elapsed, 0.01):,.0f} rows/sec)", flush=True)
    cursor.close()
    tmp_csv_path.unlink(missing_ok=True)


def main():
    from pathlib import Path
    tmp_dir = Path("data/processed")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    conn = check_connection()

    print("[read] loading processed CSVs ...", flush=True)
    products = load_processed("products_clean.csv").rename(columns=PRODUCT_RENAME)
    households = load_processed("households_clean.csv").rename(columns=HOUSEHOLD_RENAME)
    transactions = load_processed("transactions_clean.csv").rename(columns=COLUMN_RENAME)

    fact_cols = list(COLUMN_RENAME.values()) + [
        "total_discount", "unit_price", "list_price", "is_promo",
        "estimated_cost", "estimated_profit", "profit_margin_pct",
        "basket_value", "household_purchase_frequency",
    ]
    fact_cols = [c for c in fact_cols if c in transactions.columns]

    print(f"[info] products={len(products):,} rows, "
          f"households={len(households):,} rows, "
          f"transactions={len(transactions):,} rows", flush=True)

    # Dimensions first (fact table has FK constraints)
    bulk_load(conn, products[list(PRODUCT_RENAME.values())], "dim_products",
              tmp_dir / "_tmp_products.csv")
    bulk_load(conn, households[list(HOUSEHOLD_RENAME.values())], "dim_households",
              tmp_dir / "_tmp_households.csv")
    bulk_load(conn, transactions[fact_cols], "fact_transactions",
              tmp_dir / "_tmp_transactions.csv", disable_keys=True)

    conn.close()
    print("[loaded] dim_products, dim_households, fact_transactions into MySQL")


if __name__ == "__main__":
    main()
