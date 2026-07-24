"""
file_utils.py
Reusable helpers for reading/writing project data consistently across phases.
"""
import os
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(PROCESSED_DIR, "models")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

for _d in (RAW_DIR, PROCESSED_DIR, MODELS_DIR, REPORTS_DIR):
    os.makedirs(_d, exist_ok=True)


def load_raw(filename: str, dtype: dict = None) -> pd.DataFrame:
    """Load a raw Dunnhumby CSV by filename, e.g. 'transaction_data.csv'."""
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Expected raw file at {path}. Download the Dunnhumby "
            f"'Complete Journey' dataset and place CSVs in data/raw/."
        )
    return pd.read_csv(path, engine="pyarrow", dtype=dtype)


def load_processed(filename: str) -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(...)
    return pd.read_csv(path, engine="pyarrow")


def save_processed(df: pd.DataFrame, filename: str) -> str:
    path = os.path.join(PROCESSED_DIR, filename)
    df.to_csv(path, index=False)
    print(f"[saved] {path}  ({len(df):,} rows, {df.shape[1]} cols)")
    return path


def save_report(df: pd.DataFrame, filename: str, sheet_name: str = "Sheet1") -> str:
    path = os.path.join(REPORTS_DIR, filename)
    if filename.endswith(".xlsx"):
        df.to_excel(path, index=False, sheet_name=sheet_name)
    else:
        df.to_csv(path, index=False)
    print(f"[report] {path}")
    return path
