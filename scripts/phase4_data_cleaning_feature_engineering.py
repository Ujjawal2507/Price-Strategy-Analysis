"""
Phase 4 — Data Cleaning & Feature Engineering
Cleans the transaction table and derives business metrics needed by every
later phase: unit price, discounts, profit proxy, margin, basket value,
promo flags, and household purchase frequency.

NOTE on profit: Dunnhumby has no cost data, so profit here is a PROXY —
profit = SALES_VALUE - total_discount, i.e. realized revenue after discount
is treated as a stand-in for margin. Replace with real COGS if you have it.
"""
import pandas as pd
from utils.file_utils import load_raw, save_processed
from utils.validation import (
    validate_no_negative_sales, validate_quantity_positive,
    validate_discount_not_exceeding_price,
)

COST_PROXY_MARGIN_RATE = 0.30  # assume 30% of sales value is cost, if no COGS is available
TRANSACTION_DTYPES = {
    "household_key": "int32", "BASKET_ID": "int64", "DAY": "int16",
    "PRODUCT_ID": "int64", "QUANTITY": "int32", "SALES_VALUE": "float32",
    "STORE_ID": "int32", "RETAIL_DISC": "float32", "TRANS_TIME": "int32",
    "WEEK_NO": "int16", "COUPON_DISC": "float32", "COUPON_MATCH_DISC": "float32",
}


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates()
    df = df[df["QUANTITY"] > 0]
    df = df[df["SALES_VALUE"] >= 0]
    df["RETAIL_DISC"] = df["RETAIL_DISC"].fillna(0)
    df["COUPON_DISC"] = df["COUPON_DISC"].fillna(0)
    df["COUPON_MATCH_DISC"] = df.get("COUPON_MATCH_DISC", pd.Series(0, index=df.index)).fillna(0)
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["total_discount"] = df["RETAIL_DISC"].abs() + df["COUPON_DISC"].abs() + df["COUPON_MATCH_DISC"].abs()
    df["unit_price"] = (df["SALES_VALUE"] / df["QUANTITY"]).replace([float("inf")], 0)
    df["list_price"] = df["unit_price"] + (df["total_discount"] / df["QUANTITY"]).replace([float("inf")], 0)
    df["is_promo"] = (df["total_discount"] > 0).astype(int)

    # Proxy profit / margin (swap in real cost data if available)
    df["estimated_cost"] = df["SALES_VALUE"] * (1 - COST_PROXY_MARGIN_RATE)
    df["estimated_profit"] = df["SALES_VALUE"] - df["estimated_cost"]
    df["profit_margin_pct"] = (df["estimated_profit"] / df["SALES_VALUE"].replace(0, pd.NA)) * 100

    return df


def add_basket_and_frequency_features(df: pd.DataFrame) -> pd.DataFrame:
    basket_value = df.groupby("BASKET_ID")["SALES_VALUE"].transform("sum")
    df["basket_value"] = basket_value

    hh_freq = df.groupby("household_key")["BASKET_ID"].transform("nunique")
    df["household_purchase_frequency"] = hh_freq

    return df


def main():
    transactions = load_raw("transaction_data.csv", dtype=TRANSACTION_DTYPES)
    print(f"[loaded] transactions: {transactions.shape}")

    transactions = clean_transactions(transactions)
    transactions = engineer_features(transactions)
    transactions = add_basket_and_frequency_features(transactions)

    validate_no_negative_sales(transactions)
    validate_quantity_positive(transactions)
    validate_discount_not_exceeding_price(transactions)

    save_processed(transactions, "transactions_clean.csv")

    # Carry product & household dims through unchanged (light cleaning only)
    products = load_raw("product.csv").drop_duplicates(subset="PRODUCT_ID")
    households = load_raw("hh_demographic.csv", dtype={"household_key": "int32"}).drop_duplicates(subset="household_key")
    save_processed(products, "products_clean.csv")
    save_processed(households, "households_clean.csv")

if __name__ == "__main__":
    main()
