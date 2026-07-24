"""
Phase 10 — Price Elasticity of Demand
Answers: "How sensitive is demand to price?" per product/category, using
the classic log-log regression: elasticity = % change in demand for a 1%
change in price. This is computed directly (not read off the ML models),
because elasticity needs a clean causal-style estimate, ideally per
product, with enough price variation to be meaningful.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from utils.file_utils import load_processed, save_processed
from utils.modeling_prep import build_product_week_panel

MIN_WEEKS_OF_DATA = 8
MIN_PRICE_VARIATION_PCT = 5  # skip products whose price barely moves


def compute_elasticity_for_product(product_panel: pd.DataFrame) -> dict:
    price_range_pct = 100 * (product_panel["unit_price"].max() - product_panel["unit_price"].min()) / product_panel["unit_price"].mean()
    if len(product_panel) < MIN_WEEKS_OF_DATA or price_range_pct < MIN_PRICE_VARIATION_PCT:
        return None

    X = sm.add_constant(np.log1p(product_panel["unit_price"]))
    y = np.log1p(product_panel["total_quantity"])
    model = sm.OLS(y, X).fit()

    elasticity = model.params.get("unit_price", np.nan)
    return {
        "elasticity": round(elasticity, 3),
        "p_value": round(model.pvalues.get("unit_price", np.nan), 4),
        "r_squared": round(model.rsquared, 3),
        "n_observations": len(product_panel),
    }


def classify_elasticity(e: float) -> str:
    if pd.isna(e):
        return "insufficient data"
    if e > -0.5:
        return "inelastic (can sustain premium pricing)"
    elif e > -1.0:
        return "moderately elastic"
    else:
        return "highly elastic (price-sensitive, discount-driven volume)"


def main():
    transactions = load_processed("transactions_clean.csv")
    products = load_processed("products_clean.csv")
    panel = build_product_week_panel(transactions, products)

    results = []
    for product_id, group in panel.groupby("PRODUCT_ID"):
        stats = compute_elasticity_for_product(group)
        if stats is None:
            continue
        stats["PRODUCT_ID"] = product_id
        results.append(stats)

    elasticity_df = pd.DataFrame(results)
    elasticity_df["interpretation"] = elasticity_df["elasticity"].apply(classify_elasticity)
    elasticity_df = elasticity_df.merge(
        products[["PRODUCT_ID", "DEPARTMENT", "COMMODITY_DESC", "BRAND"]], on="PRODUCT_ID", how="left"
    )
    elasticity_df = elasticity_df.sort_values("elasticity")

    print(f"Computed elasticity for {len(elasticity_df)} products "
          f"(skipped products with <{MIN_WEEKS_OF_DATA} weeks or <{MIN_PRICE_VARIATION_PCT}% price variation)")
    print("\nMost price-sensitive products (most negative elasticity):")
    print(elasticity_df.head(10)[["PRODUCT_ID", "COMMODITY_DESC", "elasticity", "interpretation"]].to_string(index=False))
    print("\nLeast price-sensitive products (can sustain premium pricing):")
    print(elasticity_df.tail(10)[["PRODUCT_ID", "COMMODITY_DESC", "elasticity", "interpretation"]].to_string(index=False))

    save_processed(elasticity_df, "price_elasticity_by_product.csv")

    # Category-level rollup (average elasticity per department)
    category_elasticity = elasticity_df.groupby("DEPARTMENT")["elasticity"].mean().sort_values()
    print("\nAverage elasticity by department:")
    print(category_elasticity.to_string())
    save_processed(category_elasticity.reset_index(), "price_elasticity_by_department.csv")


if __name__ == "__main__":
    main()
