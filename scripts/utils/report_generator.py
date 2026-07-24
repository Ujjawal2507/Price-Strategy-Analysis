"""
report_generator.py
Turns profiling / quality-check results into Excel reports under reports/.
"""
import pandas as pd
from .file_utils import REPORTS_DIR
import os


def write_excel_report(sheets: dict, filename: str) -> str:
    """
    sheets: {sheet_name: dataframe}
    Writes a multi-sheet Excel workbook.
    """
    path = os.path.join(REPORTS_DIR, filename)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    print(f"[report] {path}")
    return path
