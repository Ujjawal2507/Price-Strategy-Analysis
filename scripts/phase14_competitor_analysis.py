"""
Phase 14 — Competitor Pricing Analysis
Dunnhumby has NO real competitor price data. This phase does two things:

1. Builds a DERIVED "competitor_prices" table you can later replace with
   real scraped/licensed competitor data (same schema, just swap the
   generator for a real loader).
2. Compares your own average selling price per product against that
   competitor benchmark to flag over/under-priced products and combine
   that with elasticity (Phase 10) to suggest where competitive
   positioning actually matters.

IMPORTANT: Until you plug in real competitor data, treat every output
here as illustrative/methodology-only, not a real business signal.
"""
import numpy as np
import pandas as pd

from utils.file_utils import load_processed, save_processed

RANDOM_SEED = 42
# Simulated competitor price = own avg price * random multiplier in this range.
# Replace this whole function with a real loader (e.g. read a scraped
# competitor_prices.csv into data/raw/) once you have actual data.
COMPETITOR_PRICE_NOISE_RANGE = (0.85, 1.15)


def build_synthetic_competitor_prices(own_prices: pd.DataFrame) -> pd.DataFrame:
    """
    own_prices: dataframe with PRODUCT_ID, own_avg_price
    Returns a competitor_prices table with the SAME schema you'd get from
    a real competitor feed: PRODUCT_ID, competitor_price, source.
    """
    rng = np.random.default_rng(RANDOM_SEED)
    multipliers = rng.uniform(*COMPETITOR_PRICE_NOISE_RANGE, size=len(own_prices))
    competitor_prices = own_prices.copy()
    competitor_prices["competitor_price"] = (own_prices["own_avg_price"] * multipliers).round(2)
    competitor_prices["source"] = "SIMULATED — replace with real competitor feed"
    return competitor_prices[["PRODUCT_ID", "competitor_price", "source"]]


def load_real_competitor_prices(path: str) -> pd.DataFrame:
    """
    Use this instead of build_synthetic_competitor_prices() once you have
    real data. Expected columns: PRODUCT_ID, competitor_price[, source].
    """
    df = pd.read_csv(path)
    if "source" not in df.columns:
        df["source"] = "real feed"
    return df[["PRODUCT_ID", "competitor_price", "source"]]


def main():
    transactions = load_processed("transactions_clean.csv")
    products = load_processed("products_clean.csv")

    own_prices = (
        transactions.groupby("PRODUCT_ID")["unit_price"].mean()
        .reset_index().rename(columns={"unit_price": "own_avg_price"})
    )

    # --- Swap this one line for load_real_competitor_prices(path) when you have real data ---
    competitor_prices = build_synthetic_competitor_prices(own_prices)

    comparison = own_prices.merge(competitor_prices, on="PRODUCT_ID", how="left")
    comparison["price_gap_pct"] = round(
        100 * (comparison["own_avg_price"] - comparison["competitor_price"]) / comparison["competitor_price"], 2
    )
    comparison["position"] = pd.cut(
        comparison["price_gap_pct"],
        bins=[-np.inf, -5, 5, np.inf],
        labels=["priced below market", "priced in line with market", "priced above market"],
    )

    comparison = comparison.merge(
        products[["PRODUCT_ID", "DEPARTMENT", "COMMODITY_DESC", "BRAND"]], on="PRODUCT_ID", how="left"
    )

    # Combine with elasticity if it's already been computed (Phase 10) —
    # this is the useful part: "priced above market AND highly elastic" =
    # actual volume risk, worth prioritizing for repricing
    try:
        elasticity = load_processed("price_elasticity_by_product.csv")[["PRODUCT_ID", "elasticity", "interpretation"]]
        comparison = comparison.merge(elasticity, on="PRODUCT_ID", how="left")
        at_risk = comparison[
            (comparison["position"] == "priced above market") & (comparison["elasticity"] < -0.5)
        ].sort_values("price_gap_pct", ascending=False)
        print(f"\nProducts priced above market AND price-sensitive (highest repricing priority): {len(at_risk)}")
        print(at_risk.head(10)[["PRODUCT_ID", "COMMODITY_DESC", "price_gap_pct", "elasticity"]].to_string(index=False))
    except FileNotFoundError:
        print("[note] Run Phase 10 (elasticity) first to get the combined risk view.")

    print("\nPricing position summary:")
    print(comparison["position"].value_counts().to_string())

    save_processed(competitor_prices, "competitor_prices_derived.csv")
    save_processed(comparison, "competitor_price_comparison.csv")


if __name__ == "__main__":
    main()
