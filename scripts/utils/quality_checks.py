"""
quality_checks.py
Implements the 5-dimension Data Quality Assessment used in Phase 3:
completeness, uniqueness, validity, consistency, referential integrity.
"""
import pandas as pd


def check_completeness(df: pd.DataFrame, critical_cols: list) -> dict:
    result = {}
    for col in critical_cols:
        if col not in df.columns:
            result[col] = "MISSING COLUMN"
            continue
        missing_pct = round(100 * df[col].isna().sum() / len(df), 2)
        result[col] = f"{missing_pct}% missing"
    return result


def check_uniqueness(df: pd.DataFrame, key_cols: list) -> dict:
    dup_rows = int(df.duplicated().sum())
    dup_keys = int(df.duplicated(subset=key_cols).sum()) if all(c in df.columns for c in key_cols) else None
    return {"duplicate_rows": dup_rows, "duplicate_key_combinations": dup_keys}


def check_validity(df: pd.DataFrame, rules: dict) -> dict:
    """
    rules: {column: (min_value, max_value)}
    Returns count of rows violating each rule.
    """
    result = {}
    for col, (lo, hi) in rules.items():
        if col not in df.columns:
            result[col] = "MISSING COLUMN"
            continue
        violations = int(((df[col] < lo) | (df[col] > hi)).sum())
        result[col] = violations
    return result


def check_consistency(df: pd.DataFrame, categorical_cols: list) -> dict:
    """Flags columns whose categories have inconsistent casing/whitespace."""
    result = {}
    for col in categorical_cols:
        if col not in df.columns:
            continue
        raw_values = df[col].dropna().unique()
        normalized = {str(v).strip().upper() for v in raw_values}
        result[col] = {
            "raw_unique_count": len(raw_values),
            "normalized_unique_count": len(normalized),
            "likely_inconsistent": len(raw_values) != len(normalized),
        }
    return result


def check_referential_integrity(child_df: pd.DataFrame, child_key: str,
                                 parent_df: pd.DataFrame, parent_key: str) -> dict:
    orphan_mask = ~child_df[child_key].isin(parent_df[parent_key])
    return {
        "child_key": child_key,
        "parent_key": parent_key,
        "orphan_rows": int(orphan_mask.sum()),
        "orphan_pct": round(100 * orphan_mask.sum() / len(child_df), 3) if len(child_df) else 0,
    }
