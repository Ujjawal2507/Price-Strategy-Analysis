"""
Phase 11 — Price Optimization (the most important phase)
Answers: "Which price should I recommend?"

Approach: for each product, load the trained production demand model
(XGBoost by default), sweep a grid of candidate prices around the
historical range, predict demand at each price, compute expected profit,
and recommend the profit-maximizing price — subject to the business
constraints defined in Phase 1 (no extrapolation beyond observed prices,
minimum margin floor, capped week-over-week price change).

PERFORMANCE NOTE: this version builds every product's price grid into a
single batch and calls model.predict() ONCE on the whole batch, instead
of once per (product, price) pair. At ~90k Dunnhumby products x 25 grid
points, that's the difference between ~2.3 million individual predict
calls (very slow, single-row overhead dominates) and one call on a
~2.3 million row DataFrame (seconds, since XGBoost is fully vectorized
internally). Always prefer batching predictions over looping when the
model itself does not require sequential state.
"""
import os
import time
import joblib
import numpy as np
import pandas as pd

from utils.file_utils import load_processed, save_processed, MODELS_DIR
from utils.modeling_prep import build_product_week_panel, FEATURE_COLS

# --- Business constraints (tune with the business team, see Phase 1) ---
MIN_MARGIN_PCT = 15          # never recommend a price implying margin below this
MAX_PRICE_CHANGE_PCT = 20    # cap week-over-week price change vs. current price
N_PRICE_POINTS = 25          # grid resolution per product
COST_PROXY_MARGIN_RATE = 0.30  # must match Phase 4's assumption unless you have real COGS

PRODUCTION_MODEL_PATH = os.path.join(MODELS_DIR, "xgboost_demand.joblib")
# To promote LightGBM instead, change the line above to:
# PRODUCTION_MODEL_PATH = os.path.join(MODELS_DIR, "lightgbm_demand.joblib")


def load_production_model():
    bundle = joblib.load(PRODUCTION_MODEL_PATH)
    return bundle["model"], bundle["features"]


def build_price_grid_batch(panel: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Vectorized construction of the full (product x price_grid) batch to score
    in one model.predict() call, instead of looping product-by-product and
    price-by-price.
    """
    panel_sorted = panel.sort_values(["PRODUCT_ID", "week_no"])
    last_rows = panel_sorted.groupby("PRODUCT_ID").tail(1).set_index("PRODUCT_ID")

    price_stats = panel.groupby("PRODUCT_ID")["unit_price"].agg(["min", "max"])
    current_price = last_rows["unit_price"]

    lower = np.maximum(price_stats["min"], current_price * (1 - MAX_PRICE_CHANGE_PCT / 100))
    upper = np.minimum(price_stats["max"], current_price * (1 + MAX_PRICE_CHANGE_PCT / 100))

    valid_mask = upper > lower
    valid_ids = lower[valid_mask].index
    print(f"[optimizer] {len(valid_ids):,} / {panel['PRODUCT_ID'].nunique():,} products have a usable price range")

    lower_v = lower.loc[valid_ids].values
    upper_v = upper.loc[valid_ids].values

    fractions = np.linspace(0, 1, N_PRICE_POINTS)
    grid_matrix = lower_v[:, None] + (upper_v - lower_v)[:, None] * fractions[None, :]

    product_id_flat = np.repeat(valid_ids.values, N_PRICE_POINTS)
    price_flat = grid_matrix.flatten()

    batch = last_rows.loc[product_id_flat, features].reset_index(drop=True)
    batch["unit_price"] = price_flat
    batch.insert(0, "PRODUCT_ID", product_id_flat)
    batch.insert(1, "current_price", np.repeat(current_price.loc[valid_ids].values, N_PRICE_POINTS))
    batch["candidate_price"] = price_flat

    return batch


def main():
    transactions = load_processed("transactions_clean.csv")
    products = load_processed("products_clean.csv")
    panel = build_product_week_panel(transactions, products)

    model, features = load_production_model()

    t0 = time.time()
    batch = build_price_grid_batch(panel, features)
    print(f"[optimizer] scoring batch of {len(batch):,} (product, price) rows in a single predict() call...")

    predicted_demand = model.predict(batch[features])
    batch["predicted_demand"] = np.clip(predicted_demand, 0, None)

    batch["predicted_revenue"] = batch["candidate_price"] * batch["predicted_demand"]
    cost = batch["candidate_price"] * (1 - COST_PROXY_MARGIN_RATE) * batch["predicted_demand"]
    batch["predicted_profit"] = batch["predicted_revenue"] - cost
    batch["predicted_margin_pct"] = np.where(
        batch["predicted_revenue"] > 0,
        100 * batch["predicted_profit"] / batch["predicted_revenue"],
        0,
    )

    print(f"[optimizer] scored in {time.time() - t0:.1f}s")

    valid_batch = batch[batch["predicted_margin_pct"] >= MIN_MARGIN_PCT]
    best_idx = valid_batch.groupby("PRODUCT_ID")["predicted_profit"].idxmax()
    best = valid_batch.loc[best_idx].copy()

    best["price_change_pct"] = round(
        100 * (best["candidate_price"] - best["current_price"]) / best["current_price"], 1
    )
    rec_df = best.rename(columns={
        "candidate_price": "recommended_price",
        "predicted_demand": "expected_demand",
        "predicted_profit": "expected_profit",
        "predicted_margin_pct": "expected_margin_pct",
    })[[
        "PRODUCT_ID", "current_price", "recommended_price", "price_change_pct",
        "expected_demand", "expected_profit", "expected_margin_pct",
    ]]
    rec_df["current_price"] = rec_df["current_price"].round(2)
    rec_df["recommended_price"] = rec_df["recommended_price"].round(2)

    rec_df = rec_df.merge(products[["PRODUCT_ID", "DEPARTMENT", "COMMODITY_DESC", "BRAND"]],
                           on="PRODUCT_ID", how="left")
    rec_df = rec_df.sort_values("expected_profit", ascending=False)

    print(f"\nGenerated price recommendations for {len(rec_df):,} products")
    print(rec_df.head(15).to_string(index=False))

    save_processed(rec_df, "price_recommendations.csv")


if __name__ == "__main__":
    main()