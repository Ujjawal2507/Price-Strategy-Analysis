# Price Strategy Analysis — Dunnhumby "The Complete Journey"

An end-to-end retail pricing project, built phase by phase on purpose —
each stage is its own script, so any single piece can be re-run or swapped
out without dragging the rest of the pipeline down with it. It starts from
raw Dunnhumby transaction data and works its way up to pricing
recommendations, elasticity estimates, customer segments, and a dashboard
you can actually hand to someone who doesn't want to read code.

It's grown past a reporting dashboard into something closer to a decision
support tool: pick a product, and it tells you what price to charge, what
happens if you change it, whether that change clears the business's own
rules, and how confident you should be in any of it.

## Dashboard preview

**Live dashboard:** [price-strategy-analysis.onrender.com]((https://price-strategy-analysis.onrender.com))

## Why this exists

A grocery chain sits on years of receipt-level data and usually still
prices by gut feel — match the competitor down the street, round to a
familiar number, repeat. This project asks a simpler question: what does
the data actually say about where prices are working, where they're
leaking margin, and which few changes would move the needle most?

## Problems it's solving

- **No visibility into which categories actually drive the business.**
  The driver tree and revenue-mix views answer "where does the money come
  from" in one glance instead of a pivot table.
- **Promotions running on autopilot.** The promo-share and elasticity
  numbers show which departments are discounting heavily without any real
  lift in return.
- **Pricing decisions made without knowing how price-sensitive a product
  actually is.** The elasticity models put a real number next to "if we
  raise this price, what happens to demand" instead of a guess.
- **No structured way to prioritize price changes.** The recommendation
  engine ranks SKUs by expected profit impact so the highest-value moves
  surface first instead of getting buried in a spreadsheet.
- **Treating all customers the same.** The segmentation work splits
  households into groups with genuinely different spending behavior, so
  offers can be built around a segment instead of the whole customer base
  at once.
- **Recommendations nobody can act on.** A single "raise this price"
  number isn't enough for a pricing manager to sign off on. They want to
  see the trade-offs, stress-test the assumptions, and know why the tool
  is telling them what it's telling them — which is what the decision
  intelligence layer below is for.

## How it helps a retail store

This is the kind of thing a pricing or category team could walk into a
quarterly review with: which categories to test a price increase on,
which promotions to cut because they aren't earning their keep, which
products carry outsized margin risk, and which customer segment is worth
building a loyalty offer around. None of it replaces a pricing manager's
judgment — it just gives that judgment something solid to stand on.

## The decision intelligence layer

The original dashboard explained what happened and estimated what price
might work. This layer goes a step further and lets someone actually work
through a pricing decision — try prices, see the trade-offs, check the
result against real business constraints, and get a plain-language reason
for the final call.

- **Optimization engine** — sweeps a range of prices around the current
  one and, using the fitted elasticity, projects demand, revenue, profit,
  and margin at each point to find the profit-maximizing price rather
  than just reporting one static number.
- **What-if simulator** — lets you drag price, cost, promo intensity,
  competitor price, inventory, and market demand and see projected units,
  revenue, profit, margin, and a pricing health score update live.
- **Business rule engine** — checks every recommendation against real
  constraints (minimum margin, maximum demand loss, competitor gap,
  inventory limits) and classifies it as approved, conditionally
  approved, or rejected, with a plain-language reason either way.
- **Uncertainty engine** — turns each model's fit quality, sample size,
  and significance into a confidence badge (High / Medium / Low) and an
  approximate interval around the projected number, instead of presenting
  every estimate as if it were exact.
- **Scenario engine** — runs the standard set of alternatives a decision
  maker actually wants to compare side by side: hold, +5%, +10%, -5%, and
  the optimizer's own pick.
- **Recommendation engine** — assembles the "why" behind a recommendation
  from elasticity, projected demand and revenue change, competitor
  position, confidence, and any rule violations, so it isn't a black-box
  number.
- **Decision engine** — the one entry point the dashboard actually calls.
  It runs the optimizer, feeds the result through the rule engine and
  scenario engine, pulls a confidence estimate, generates the explanation,
  and hands back a single structured object for the UI to render.

`dashboard/index.html` is still a single self-contained file (this logic
lives inline there, organized to mirror the module split below), but the
`files/` folder has the real, separate ES modules if you want to extend
any one engine on its own:

```
files/
├── data.js                 # single source of truth for elasticity, products, rule thresholds
├── optimization.js          # price sweep + profit-maximizing point
├── whatIfSimulator.js       # recalculates outcomes as sliders move
├── businessRules.js         # approve / conditionally approve / reject + reasons
├── uncertainty.js           # confidence badges + approximate intervals
├── scenarioEngine.js        # hold / +5% / +10% / -5% / optimized, side by side
├── recommendationEngine.js  # plain-language explanation of the final call
├── decisionEngine.js        # orchestrates all of the above, returns one object
├── app.js                   # the only file that touches the DOM
└── styles.css
```

The rule of thumb throughout: nothing renders math it didn't get back
from one of these modules, and none of these modules know that a
dashboard exists.

## Technologies used

- **Python + pandas** for cleaning, feature engineering, and all the
  heavy lifting on the raw transaction data
- **MySQL** for structured storage once the data's cleaned
- **scikit-learn** (linear regression, random forest, K-Means) and
  **XGBoost / LightGBM** for the demand and segmentation models
- **statsmodels-style regression** for the price elasticity estimates
- **joblib** for saving trained models so they don't need retraining
  every time
- **HTML, CSS, and vanilla JavaScript (ES modules)** for the dashboard
  and decision intelligence layer — no framework, nothing to install

## Folder structure
```
price_strategy_analysis/
├── data/
│   ├── raw/            # original Dunnhumby CSVs go here
│   └── processed/      # cleaned / feature-engineered outputs, elasticity
│                       # tables, competitor comparisons, price recs, models/
├── reports/
│   ├── eda/             # exploratory charts from phase 6
│   ├── phase2_data_profiling_report.xlsx
│   └── phase3_data_quality_report.xlsx
├── sql/                 # schema.sql + queries.sql for MySQL
├── dashboard/           # the self-contained pricing dashboard (index.html)
├── files/               # decision intelligence layer as separate ES modules
├── docs/                # dashboard preview screenshots used in this README
├── requirements.txt
└── scripts/
    ├── utils/
    │   ├── file_utils.py
    │   ├── profiling.py
    │   ├── quality_checks.py
    │   ├── report_generator.py
    │   ├── modeling_prep.py
    │   └── validation.py
    ├── phase1_business_understanding.md
    ├── phase2_data_profiling.py
    ├── phase3_data_quality_assessment.py
    ├── phase4_data_cleaning_feature_engineering.py
    ├── phase5_load_to_mysql.py
    ├── phase6_eda.py
    ├── phase7_model_linear_regression.py
    ├── phase8_model_random_forest.py
    ├── phase9_model_xgboost.py
    ├── phase9b_model_lightgbm.py
    ├── phase10_price_elasticity.py
    ├── phase11_price_optimization.py
    ├── phase12_customer_segmentation_kmeans.py
    └── phase14_competitor_analysis.py
```

## Before you start: the Dunnhumby files you'll need

Grab the original Dunnhumby CSVs and drop them into `data/raw/`:

- `transaction_data.csv`
- `product.csv`
- `hh_demographic.csv`
- `campaign_table.csv`
- `campaign_desc.csv`
- `coupon.csv`
- `coupon_redempt.csv`
- `causal_data.csv`

The scripts stick to Dunnhumby's original column names throughout
(`household_key`, `PRODUCT_ID`, `SALES_VALUE`, `QUANTITY`, `RETAIL_DISC`,
`COUPON_DISC`, `WEEK_NO`, `STORE_ID`, and so on). If your copy of the
dataset has different casing or column names, update the `COLUMNS`
constants at the top of each script rather than hunting through the
logic itself.

## A note on the competitor pricing (phase 14)

Dunnhumby doesn't include competitor price data — no retailer gives that
away for free. Phase 14 builds a clearly-labeled **synthetic**
`competitor_prices_derived.csv` (your own prices plus some noise) instead
of skipping the step, so the whole comparison pipeline — price-gap %,
over/under-priced flags, cross-checks against elasticity — is fully wired
up and ready to go.

The day real competitor prices show up (scraped, licensed, whatever),
swap `build_synthetic_competitor_prices()` for
`load_real_competitor_prices(path)` inside that one script. Same output
schema, so nothing downstream needs to change.

## A few notes on how it's put together

- Every phase reads from and writes to `data/processed/`, keeping the
  phases loosely coupled — you could rewrite phase 9 (XGBoost) top to
  bottom without touching phase 10 (elasticity), as long as the output
  schema doesn't change.
- Profiling, quality checks, report generation, and validation live in
  `utils/`, so the phase scripts stay short and readable.
- Trained models are saved to `data/processed/models/` with `joblib`, so
  the optimization phase can load whichever one is "production" without
  retraining from scratch.
- The decision intelligence layer follows the same principle in
  JavaScript: each engine in `files/` does one job, exports plain
  functions, and has no idea the others exist except through
  `decisionEngine.js`.
