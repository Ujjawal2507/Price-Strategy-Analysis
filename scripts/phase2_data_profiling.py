"""
Phase 2 — Data Profiling
Profiles every raw Dunnhumby table and writes an Excel report to reports/.
Run this BEFORE cleaning anything — the goal is to understand the data
as-is, not to fix it yet.
"""
import pandas as pd
from utils.file_utils import load_raw
from utils.profiling import profile_dataframe, dataset_overview
from utils.report_generator import write_excel_report

RAW_FILES = {
    "transactions": "transaction_data.csv",
    "products": "product.csv",
    "households": "hh_demographic.csv",
    "campaigns": "campaign_table.csv",
    "campaign_desc": "campaign_desc.csv",
    "coupons": "coupon.csv",
    "coupon_redemptions": "coupon_redempt.csv",
    "causal": "causal_data.csv",
}


def main():
    overviews = []
    profile_sheets = {}

    for name, filename in RAW_FILES.items():
        try:
            df = load_raw(filename)
        except FileNotFoundError as e:
            print(f"[skip] {e}")
            continue

        overviews.append(dataset_overview(df, name))
        profile_sheets[name[:31]] = profile_dataframe(df, name)
        print(f"[profiled] {name}: {df.shape[0]:,} rows x {df.shape[1]} cols")

    overview_df = pd.DataFrame(overviews)
    print("\n=== Dataset Overview ===")
    print(overview_df.to_string(index=False))

    sheets = {"overview": overview_df, **profile_sheets}
    write_excel_report(sheets, "phase2_data_profiling_report.xlsx")


if __name__ == "__main__":
    main()
