"""
Phase 12 — Customer Segmentation (K-Means)
Segments households so pricing/promotion strategy can differ by segment:
e.g. price-sensitive shoppers get targeted discounts, premium shoppers get
less discounting, coupon lovers get coupon-led campaigns instead of
across-the-board price cuts.
"""
import os
import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from utils.file_utils import load_processed, save_processed, MODELS_DIR

N_CLUSTERS = 3  # start at 3 (price-sensitive / premium / coupon lovers) per Phase 1 spec; tune with silhouette score


def build_household_features(transactions: pd.DataFrame) -> pd.DataFrame:
    agg = transactions.groupby("household_key").agg(
        total_spend=("SALES_VALUE", "sum"),
        avg_basket_value=("basket_value", "mean"),
        purchase_frequency=("household_purchase_frequency", "max"),
        avg_unit_price_paid=("unit_price", "mean"),
        promo_purchase_rate=("is_promo", "mean"),
        coupon_discount_total=("COUPON_DISC", lambda x: x.abs().sum()),
    ).reset_index()
    return agg


def main():
    transactions = load_processed("transactions_clean.csv")
    household_features = build_household_features(transactions)

    feature_cols = ["total_spend", "avg_basket_value", "purchase_frequency",
                     "avg_unit_price_paid", "promo_purchase_rate", "coupon_discount_total"]
    X = household_features[feature_cols].fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Quick check across a small range of k, in case 3 isn't the best fit for your data
    print("Silhouette scores by k (informational — default k stays at N_CLUSTERS):")
    for k in range(2, 6):
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X_scaled)
        score = silhouette_score(X_scaled, km.labels_)
        print(f"  k={k}: silhouette={score:.3f}")

    model = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    household_features["cluster"] = model.fit_predict(X_scaled)

    cluster_profile = household_features.groupby("cluster")[feature_cols].mean().round(2)
    print("\nCluster profiles (mean feature values):")
    print(cluster_profile.to_string())

    # Heuristic labeling based on relative feature levels — inspect and relabel manually if needed
    labels = {}
    for cluster_id, row in cluster_profile.iterrows():
        if row["promo_purchase_rate"] == cluster_profile["promo_purchase_rate"].max():
            labels[cluster_id] = "price-sensitive / promo-driven"
        elif row["coupon_discount_total"] == cluster_profile["coupon_discount_total"].max():
            labels[cluster_id] = "coupon lovers"
        else:
            labels[cluster_id] = "premium / low price-sensitivity"
    household_features["segment_label"] = household_features["cluster"].map(labels)

    print("\nSegment sizes:")
    print(household_features["segment_label"].value_counts().to_string())

    save_processed(household_features, "household_segments.csv")
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump({"model": model, "scaler": scaler, "features": feature_cols, "labels": labels},
                os.path.join(MODELS_DIR, "kmeans_segmentation.joblib"))
    print(f"[saved] {os.path.join(MODELS_DIR, 'kmeans_segmentation.joblib')}")


if __name__ == "__main__":
    main()
