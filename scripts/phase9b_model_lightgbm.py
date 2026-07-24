"""
Phase 9b — Optional: LightGBM (speed/accuracy benchmark vs. XGBoost)
Not required by the pipeline, but worth running: LightGBM grows trees
leaf-wise instead of level-wise, which usually means faster training and
often better accuracy on large tabular data, plus native categorical
handling (no need to pre-encode department/product as we did for the
other models here).

If this script's RMSE beats phase9_model_xgboost.py's on your data, you
can promote it: just point Phase 11's optimizer loader at this .joblib
file instead of xgboost_demand.joblib.
"""
import os
import time
import joblib
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from utils.file_utils import load_processed, MODELS_DIR
from utils.modeling_prep import build_product_week_panel, train_test_split_panel, FEATURE_COLS


def main():
    transactions = load_processed("transactions_clean.csv")
    products = load_processed("products_clean.csv")
    panel = build_product_week_panel(transactions, products)

    X_train, X_test, y_train, y_test = train_test_split_panel(panel)

    # department_enc is already integer-encoded; tell LightGBM to treat it
    # as categorical natively rather than as an ordinal number
    categorical_features = ["department_enc"]

    model = lgb.LGBMRegressor(
        n_estimators=800,
        learning_rate=0.03,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )

    t0 = time.time()
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        eval_metric="rmse",
        categorical_feature=categorical_features,
        callbacks=[lgb.early_stopping(30, verbose=False)],
    )
    train_seconds = time.time() - t0

    preds = model.predict(X_test)

    print("=== LightGBM (benchmark) ===")
    print(f"Training time: {train_seconds:.2f}s")
    print(f"R2:   {r2_score(y_test, preds):.4f}")
    print(f"MAE:  {mean_absolute_error(y_test, preds):.2f}")
    print(f"RMSE: {mean_squared_error(y_test, preds) ** 0.5:.2f}")
    print("\nCompare these numbers to phase9_model_xgboost.py's output. "
          "Faster + similar/better RMSE => consider promoting this to production.")

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURE_COLS},
                os.path.join(MODELS_DIR, "lightgbm_demand.joblib"))
    print(f"[saved] {os.path.join(MODELS_DIR, 'lightgbm_demand.joblib')}")


if __name__ == "__main__":
    main()