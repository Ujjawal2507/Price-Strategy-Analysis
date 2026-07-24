/**
 * data.js
 * -----------------------------------------------------------------------
 * Single source of truth for numbers used across every analytical engine.
 * Everything here comes from the project's processed CSVs:
 *   - data/processed/price_elasticity_by_department.csv
 *   - data/processed/price_elasticity_by_product.csv
 *   - data/processed/price_recommendations.csv
 *   - data/processed/competitor_price_comparison.csv
 * No component other than this file should hard-code a business number.
 * -----------------------------------------------------------------------
 */

// ---- Department-level elasticity (real regression output) --------------
// "OTHER" is the demand-weighted-free average of the 18 smallest departments
// (CHEF SHOPPE, PHOTO, SPIRITS, DELI, SEAFOOD, FLORAL, etc.) so the six
// buckets shown on the dashboard match the six used in the original report.
// weekly[]: revenue for weeks 91-102 (last 12 weeks of the 102-week history),
// the same figures used throughout the underlying project's EDA.
export const DEPARTMENTS = {
  GROCERY:    { label: 'Grocery',       elasticity: -0.954,  promoShare: 55.3, basket: 19.0,
                weekly: [44033,56044,42019,49413,47017,45401,46160,51999,52870,48329,42927,36956] },
  'DRUG GM':  { label: 'Drug & Health', elasticity: -0.433,  promoShare: 28.4, basket: 9.0,
                weekly: [12950,16224,11496,12127,11193,11576,11815,12121,13830,12949,11139,9281] },
  PRODUCE:    { label: 'Produce',       elasticity: -0.623,  promoShare: 22.9, basket: 6.3,
                weekly: [5262,7579,4828,6948,6420,5985,6254,6472,6651,5637,6411,4829] },
  MEAT:       { label: 'Meat',          elasticity: -0.485,  promoShare: 55.0, basket: 10.3,
                weekly: [5596,7693,5337,6550,5728,5548,5390,6317,6800,5579,5038,4181] },
  'KIOSK-GAS':{ label: 'Gas & Kiosk',   elasticity: -43.865, promoShare: 94.6, basket: 24.7,
                weekly: [5352,6082,4780,5945,5229,5186,5584,6208,5849,4648,6347,5247],
                note: 'Extreme, promo-driven elasticity — nearly all volume here is coupon/fuel-price triggered, so this number should be capped in any optimizer, not used at face value.' },
  OTHER:      { label: 'Everything else', elasticity: -0.198, promoShare: 47.8, basket: 10.2,
                weekly: [13730,19572,12372,15982,13308,13115,13637,15832,15363,15921,12545,11474] },
};

export const WEEK_LABELS = Array.from({ length: 12 }, (_, i) => 91 + i);
export function totalWeeklyRevenue() {
  return WEEK_LABELS.map((_, i) => Object.values(DEPARTMENTS).reduce((s, d) => s + d.weekly[i], 0));
}

// ---- Representative SKUs (real rows from price_elasticity_by_product.csv,
// price_recommendations.csv and competitor_price_comparison.csv) ----------
// marginAssumption: the source model (phase11_price_optimization.py) targets
// a flat 30% margin for every SKU rather than deriving cost per product, so
// unit cost here is back-solved as currentPrice * (1 - 0.30). This is called
// out explicitly wherever cost is used.
const MARGIN_ASSUMPTION = 0.30;

export const PRODUCTS = [
  { id: 909769, dept: 'DRUG GM', commodity: 'Sewing', brand: 'National',
    elasticity: -1.002, rSquared: 1.00, pValue: 0.0, n: 15,
    currentPrice: 1.00, competitorPrice: 1.95, priceGapPct: -8.15, position: 'priced below market' },

  { id: 1036785, dept: 'DELI', commodity: 'Sandwiches', brand: 'Private',
    elasticity: -0.797, rSquared: 1.00, pValue: 0.0, n: 18,
    currentPrice: 3.99, competitorPrice: 4.24, priceGapPct: -10.84, position: 'priced below market' },

  { id: 15571171, dept: 'MEAT-PCKGD', commodity: 'Bacon', brand: 'National',
    elasticity: -4.042, rSquared: 0.912, pValue: 0.0, n: 22,
    currentPrice: 4.39, competitorPrice: 2.55, priceGapPct: 12.04, position: 'priced above market' },

  { id: 13876940, dept: 'GROCERY', commodity: 'Refrigerated Juices/Drinks', brand: 'National',
    elasticity: -3.923, rSquared: 0.899, pValue: 0.0, n: 20,
    currentPrice: 1.69, competitorPrice: 1.15, priceGapPct: -0.57, position: 'priced in line with market' },

  { id: 12778508, dept: 'PASTRY', commodity: 'Rolls', brand: 'National',
    elasticity: -3.513, rSquared: 0.827, pValue: 0.0, n: 17,
    currentPrice: 1.00, competitorPrice: 1.32, priceGapPct: 1.80, position: 'priced in line with market' },

  { id: 961172, dept: 'NUTRITION', commodity: 'Rice Cakes', brand: 'National',
    elasticity: -2.636, rSquared: 0.724, pValue: 0.0, n: 40,
    currentPrice: 1.00, competitorPrice: 1.20, priceGapPct: 8.67, position: 'priced above market' },

  { id: 13512828, dept: 'MEAT', commodity: 'Smoked Meats', brand: 'Private',
    elasticity: -5.228, rSquared: 0.707, pValue: 0.0, n: 21,
    currentPrice: 1.99, competitorPrice: 1.82, priceGapPct: -3.83, position: 'priced in line with market' },

  { id: 13416285, dept: 'SEAFOOD-PCKGD', commodity: 'Seafood - Fresh', brand: 'National',
    elasticity: -1.519, rSquared: 0.699, pValue: 0.0, n: 18,
    currentPrice: 2.99, competitorPrice: 2.22, priceGapPct: 0.18, position: 'priced in line with market' },
].map(p => ({ ...p, unitCost: +(p.currentPrice * (1 - MARGIN_ASSUMPTION)).toFixed(4), marginAssumption: MARGIN_ASSUMPTION }));

// ---- Business rule thresholds (governance / policy layer) ---------------
export const RULE_CONSTRAINTS = {
  minMarginPct: 22,          // below this, margin is considered unacceptable
  maxDemandLossPct: 25,      // recommendations that cost more than this in volume get flagged
  maxCompetitorGapPct: 15,   // being priced more than this far above market gets flagged
  minInventoryBufferPct: 10, // simulated inventory-availability guardrail
};

// ---- Governance / footer metadata ---------------------------------------
export const GOVERNANCE = {
  dataSource: 'dunnhumby "The Complete Journey" — 2,500 households, 2.58M transactions, weeks 1–102',
  lastRefreshed: 'Static build — regenerate via scripts/phase10_price_elasticity.py + phase11_price_optimization.py',
  dataQuality: 'Elasticity fit varies by SKU (see R² per product) — competitor prices are simulated, not a live feed',
  owner: 'Pricing Strategy Analysis — student project',
};

export function getProduct(id) {
  return PRODUCTS.find(p => p.id === Number(id));
}

export function getDepartment(key) {
  return DEPARTMENTS[key];
}
