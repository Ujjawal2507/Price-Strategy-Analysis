"""
validation.py
Business-rule validation applied after cleaning (Phase 4) — sanity checks
that catch logic errors before data reaches SQL/EDA/modelling.
"""
import pandas as pd


def validate_no_negative_sales(df: pd.DataFrame, col: str = "SALES_VALUE") -> bool:
    bad = (df[col] < 0).sum()
    if bad:
        print(f"[validation] WARNING: {bad} rows with negative {col}")
    return bad == 0


def validate_quantity_positive(df: pd.DataFrame, col: str = "QUANTITY") -> bool:
    bad = (df[col] <= 0).sum()
    if bad:
        print(f"[validation] WARNING: {bad} rows with non-positive {col}")
    return bad == 0


def validate_price_range(df: pd.DataFrame, col: str = "unit_price", lo: float = 0.01, hi: float = 500) -> bool:
    bad = ((df[col] < lo) | (df[col] > hi)).sum()
    if bad:
        print(f"[validation] WARNING: {bad} rows with {col} outside [{lo}, {hi}]")
    return bad == 0


def validate_discount_not_exceeding_price(df: pd.DataFrame, price_col: str = "SALES_VALUE",
                                           discount_col: str = "total_discount") -> bool:
    bad = (df[discount_col].abs() > df[price_col].abs() * 1.5).sum()  # 1.5x buffer for stacked promos
    if bad:
        print(f"[validation] WARNING: {bad} rows where discount looks implausibly large vs sales value")
    return bad == 0
