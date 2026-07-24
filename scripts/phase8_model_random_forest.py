"""
modeling_prep.py
Shared feature-building logic for Phase 7/8/9/9b demand-prediction models,
so all three models are trained on an identical, comparable feature set.

Target: weekly QUANTITY demand per product (aggregated), predicted from
price and promotional features. Aggregating to product-week avoids
treating each transaction row as an independent demand observation.
"""
import pandas as pd
from sklearn.model_selection import train_test_split

FEATURE_COLS = [
    "unit_price", "is_promo", "total_discount", "display_flag", "mailer_flag",
    "department_enc", "week_no",
]
TARGET_COL = "total_quantity"


def build_product_week_panel(transactions: pd.DataFrame, products: pd.DataFrame,
                              causal: pd.DataFrame = None) -> pd.DataFrame:
    df = transactions.merge(products[["PRODUCT_ID", "DEPARTMENT"]], on="PRODUCT_ID", how="left")

    panel = df.groupby(["PRODUCT_ID", "WEEK_NO", "DEPARTMENT"]).agg(
        total_quantity=("QUANTITY", "sum"),
        unit_price=("unit_price", "mean"),
        total_discount=("total_discount", "sum"),
        is_promo=("is_promo", "max"),
    ).reset_index()
    panel = panel.rename(columns={"WEEK_NO": "week_no"})

    if causal is not None:
        causal_agg = causal.groupby(["PRODUCT_ID", "WEEK_NO"]).agg(
            display_flag=("display", lambda x: int((x.notna() & (x != "")).any())),
            mailer_flag=("mailer", lambda x: int((x.notna() & (x != "")).any())),
        ).reset_index()
        causal_agg = causal_agg.rename(columns={"WEEK_NO": "week_no"})
        panel = panel.merge(causal_agg, on=["PRODUCT_ID", "week_no"], how="left")

    for col in ["display_flag", "mailer_flag"]:
        if col not in panel.columns:
            panel[col] = 0
        panel[col] = panel[col].fillna(0).astype(int)

    panel["department_enc"] = panel["DEPARTMENT"].astype("category").cat.codes
    panel = panel.dropna(subset=["unit_price", "total_quantity"])
    panel = panel[panel["total_quantity"] > 0]

    return panel


def train_test_split_panel(panel: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
    X = panel[FEATURE_COLS]
    y = panel[TARGET_COL]
    return train_test_split(X, y, test_size=test_size, random_state=random_state)
