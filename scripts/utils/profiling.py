"""
profiling.py
Dataset profiling: shape, dtypes, missing values, duplicates, uniqueness,
memory footprint, and summary statistics — used by Phase 2.
"""
import pandas as pd


def profile_dataframe(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Return a one-row-per-column profiling summary for a dataframe."""
    rows = []
    n = len(df)
    for col in df.columns:
        s = df[col]
        rows.append({
            "dataset": name,
            "column": col,
            "dtype": str(s.dtype),
            "n_rows": n,
            "n_missing": int(s.isna().sum()),
            "pct_missing": round(100 * s.isna().sum() / n, 2) if n else 0,
            "n_unique": int(s.nunique(dropna=True)),
            "pct_unique": round(100 * s.nunique(dropna=True) / n, 2) if n else 0,
            "min": s.min() if pd.api.types.is_numeric_dtype(s) else None,
            "max": s.max() if pd.api.types.is_numeric_dtype(s) else None,
            "mean": round(s.mean(), 3) if pd.api.types.is_numeric_dtype(s) else None,
            "std": round(s.std(), 3) if pd.api.types.is_numeric_dtype(s) else None,
        })
    return pd.DataFrame(rows)


def dataset_overview(df: pd.DataFrame, name: str) -> dict:
    return {
        "dataset": name,
        "n_rows": len(df),
        "n_columns": df.shape[1],
        "n_duplicate_rows": int(df.duplicated().sum()),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
    }
