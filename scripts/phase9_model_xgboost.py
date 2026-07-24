"""
Phase 9 — Model 3: XGBoost (PRIMARY / PRODUCTION MODEL)
This is the model Phase 11 (Optimization) loads by default. Retail data is
tabular with missing values, feature interactions, and nonlinearities —
XGBoost's strength. Early stopping is used to avoid overfitting.
"""
import os
import joblib
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from utils.file_utils import load_processed, MODELS_DIR
from utils.modeling_prep import build_product_week_panel, train_test_split_panel, FEATURE_COLS


def main():
    transactions = load_processed("transactions_clean.csv")
    products = load_processed("products_clean.csv")
    panel = build_product_week_panel(transactions, products)

    X_train, X_test, y_train, y_test = train_test_split_panel(panel)

    model = xgb.XGBRegressor(
        n_estimators=800,
        learning_rate=0.03,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=42,
        early_stopping_rounds=30,
        eval_metric="rmse",
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    preds = model.predict(X_test)

    print("=== XGBoost (primary production model) ===")
    print(f"R2:   {r2_score(y_test, preds):.4f}")
    print(f"MAE:  {mean_absolute_error(y_test, preds):.2f}")
    print(f"RMSE: {mean_squared_error(y_test, preds) ** 0.5:.2f}")
    print(f"Best iteration: {model.best_iteration}")

    importances = sorted(zip(FEATURE_COLS, model.feature_importances_), key=lambda x: -x[1])
    print("\nFeature importances:")
    for feat, imp in importances:
        print(f"  {feat:20s} {imp:.4f}")

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURE_COLS},
                os.path.join(MODELS_DIR, "xgboost_demand.joblib"))
    print(f"[saved] {os.path.join(MODELS_DIR, 'xgboost_demand.joblib')}  <-- used by Phase 11 optimizer")


if __name__ == "__main__":
    main()
