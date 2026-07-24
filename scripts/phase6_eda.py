"""
Phase 6 — Exploratory Data Analysis
Generates the core charts: sales trend, category performance, promo
effectiveness, price distribution, correlation heatmap. Saves PNGs to
reports/eda/ so they can be dropped straight into a slide deck.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from utils.file_utils import load_processed, REPORTS_DIR

EDA_DIR = os.path.join(REPORTS_DIR, "eda")
os.makedirs(EDA_DIR, exist_ok=True)
sns.set_style("whitegrid")


def savefig(name):
    path = os.path.join(EDA_DIR, name)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[saved] {path}")


def main():
    txn = load_processed("transactions_clean.csv")
    products = load_processed("products_clean.csv")
    df = txn.merge(products, on="PRODUCT_ID", how="left")

    # 1. Weekly revenue trend
    weekly = df.groupby("WEEK_NO")["SALES_VALUE"].sum().reset_index()
    plt.figure(figsize=(10, 4))
    sns.lineplot(data=weekly, x="WEEK_NO", y="SALES_VALUE")
    plt.title("Weekly Revenue Trend")
    savefig("01_weekly_revenue_trend.png")

    # 2. Department performance
    dept = df.groupby("DEPARTMENT")["SALES_VALUE"].sum().sort_values(ascending=False).head(15)
    plt.figure(figsize=(10, 5))
    sns.barplot(x=dept.values, y=dept.index)
    plt.title("Top 15 Departments by Revenue")
    savefig("02_department_revenue.png")

    # 3. Promo vs non-promo revenue
    promo = df.groupby("is_promo")["SALES_VALUE"].sum()
    plt.figure(figsize=(5, 4))
    sns.barplot(x=promo.index.map({0: "Non-promo", 1: "Promo"}), y=promo.values)
    plt.title("Revenue: Promo vs Non-Promo")
    savefig("03_promo_vs_nonpromo_revenue.png")

    # 4. Unit price distribution (capped for readability)
    plt.figure(figsize=(8, 4))
    sns.histplot(df["unit_price"].clip(upper=df["unit_price"].quantile(0.99)), bins=50)
    plt.title("Unit Price Distribution (99th pct capped)")
    savefig("04_unit_price_distribution.png")

    # 5. Basket value box plot by promo flag
    plt.figure(figsize=(6, 5))
    sns.boxplot(data=df, x="is_promo", y="basket_value")
    plt.ylim(0, df["basket_value"].quantile(0.95))
    plt.title("Basket Value by Promo Flag")
    savefig("05_basket_value_by_promo.png")

    # 6. Correlation heatmap of numeric features
    numeric_cols = ["QUANTITY", "SALES_VALUE", "unit_price", "total_discount",
                     "estimated_profit", "profit_margin_pct", "basket_value"]
    corr = df[numeric_cols].corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm")
    plt.title("Correlation Heatmap")
    savefig("06_correlation_heatmap.png")

    print("EDA complete. Charts saved to reports/eda/")


if __name__ == "__main__":
    main()
