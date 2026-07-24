# Phase 1 — Business Understanding & Descriptive Analytics

No code in this phase — it's the framing that every later phase is judged
against. Fill this in before writing a line of modelling code; interviewers
and stakeholders will ask about this before they ask about XGBoost.

## Business questions this project must answer
1. Which products/categories are most price-sensitive (high elasticity)?
2. Which products can sustain premium pricing (low elasticity)?
3. Are current promotions/discounts profitable, or just moving volume?
4. What price should we set per product/segment to maximize profit,
   subject to demand and inventory constraints?
5. Which customer segments respond to price vs. promotions vs. coupons?

## Descriptive analytics to compute before any modelling (feeds Phase 6 EDA)
- Total revenue, total profit, profit margin, basket value trends over time
- Revenue/profit by department, commodity, brand, store
- Promotion frequency and average discount depth by category
- Coupon redemption rate overall and by campaign
- Household-level purchase frequency and spend distribution

## Success criteria
- A price recommendation per product (or product-segment) with expected
  profit uplift vs. current pricing, validated against a holdout period.
- Elasticity estimates that are directionally sane (elastic where you'd
  expect substitutes to exist, inelastic for staples/necessities).
- A dashboard a category manager can act on without reading the model code.

## Constraints to respect in Phase 11 (Optimization)
- Don't recommend prices outside the observed historical range (extrapolation risk).
- Respect a minimum margin floor per category (set with the business).
- Cap week-over-week price change % to avoid unrealistic swings.
