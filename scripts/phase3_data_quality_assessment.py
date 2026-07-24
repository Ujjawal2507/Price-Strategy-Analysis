"""
Phase 3 — Data Quality Assessment
Applies the 5 dimensions (completeness, uniqueness, validity, consistency,
referential integrity) to the raw tables and writes a report. This is a
gate: fix what this phase flags before moving to Phase 4 cleaning.
"""
import pandas as pd
from utils.file_utils import load_raw
from utils.quality_checks import (
    check_completeness, check_uniqueness, check_validity,
    check_consistency, check_referential_integrity,
)
from utils.report_generator import write_excel_report


def main():
    transactions = load_raw("transaction_data.csv")
    products = load_raw("product.csv")
    households = load_raw("hh_demographic.csv")

    # --- Completeness ---
    completeness = check_completeness(
        transactions, ["household_key", "PRODUCT_ID", "QUANTITY", "SALES_VALUE", "STORE_ID", "WEEK_NO"]
    )

    # --- Uniqueness ---
    uniqueness = check_uniqueness(transactions, key_cols=["household_key", "BASKET_ID", "PRODUCT_ID", "DAY"])

    # --- Validity ---
    validity = check_validity(transactions, rules={
        "QUANTITY": (0, 10_000),
        "SALES_VALUE": (0, 5_000),
    })

    # --- Consistency ---
    consistency = check_consistency(products, categorical_cols=["DEPARTMENT", "BRAND", "COMMODITY_DESC"])

    # --- Referential integrity ---
    ref_integrity_products = check_referential_integrity(
        transactions, "PRODUCT_ID", products, "PRODUCT_ID"
    )
    ref_integrity_households = check_referential_integrity(
        transactions, "household_key", households, "household_key"
    )

    print("=== Completeness ===", completeness)
    print("=== Uniqueness ===", uniqueness)
    print("=== Validity (violation counts) ===", validity)
    print("=== Consistency ===", consistency)
    print("=== Referential integrity (products) ===", ref_integrity_products)
    print("=== Referential integrity (households) ===", ref_integrity_households)

    report_df = pd.DataFrame([
        {"check": "completeness", "detail": str(completeness)},
        {"check": "uniqueness", "detail": str(uniqueness)},
        {"check": "validity", "detail": str(validity)},
        {"check": "consistency", "detail": str(consistency)},
        {"check": "referential_integrity_products", "detail": str(ref_integrity_products)},
        {"check": "referential_integrity_households", "detail": str(ref_integrity_households)},
    ])
    write_excel_report({"data_quality_summary": report_df}, "phase3_data_quality_report.xlsx")


if __name__ == "__main__":
    main()
