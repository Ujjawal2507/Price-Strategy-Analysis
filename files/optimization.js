/**
 * optimization.js
 * -----------------------------------------------------------------------
 * The analytical core of the platform. Pure functions only — this module
 * never touches the DOM and never gets imported by anything that does
 * rendering directly. It receives numbers, returns numbers.
 *
 * Demand model: constant-elasticity curve
 *     demand(p) = demand0 * (p / p0) ^ elasticity
 * This is the standard functional form implied by a log-log elasticity
 * regression (which is what price_elasticity_by_*.csv were fit with).
 * -----------------------------------------------------------------------
 */

/**
 * Build the full price-response landscape around a current price and
 * return the profit-maximizing point on it.
 *
 * @param {Object} params
 * @param {number} params.currentPrice
 * @param {number} params.elasticity        negative = normal good
 * @param {number} params.unitCost
 * @param {number} [params.baseDemand=1000] arbitrary demand index at currentPrice
 * @param {number} [params.minPriceMult=0.85]
 * @param {number} [params.maxPriceMult=1.25]
 * @param {number} [params.steps=25]
 * @returns {{ landscape: Array, optimal: Object, current: Object }}
 */
export function optimizePrice({
  currentPrice,
  elasticity,
  unitCost,
  baseDemand = 1000,
  minPriceMult = 0.85,
  maxPriceMult = 1.25,
  steps = 25,
}) {
  // Cap pathological elasticities (e.g. Gas & Kiosk's -43.9) so the curve
  // stays interpretable — this mirrors the businessRules guardrail but is
  // applied here too since an unbounded exponent makes the grid useless.
  const e = Math.max(-8, Math.min(8, elasticity));

  const landscape = [];
  for (let i = 0; i < steps; i++) {
    const mult = minPriceMult + ((maxPriceMult - minPriceMult) * i) / (steps - 1);
    const price = +(currentPrice * mult).toFixed(4);
    const demand = baseDemand * Math.pow(price / currentPrice, e);
    const revenue = price * demand;
    const profit = (price - unitCost) * demand;
    const marginPct = price > 0 ? ((price - unitCost) / price) * 100 : 0;
    landscape.push({ priceMult: +mult.toFixed(3), price, demand: +demand.toFixed(2), revenue: +revenue.toFixed(2), profit: +profit.toFixed(2), marginPct: +marginPct.toFixed(2) });
  }

  const optimal = landscape.reduce((best, pt) => (pt.profit > best.profit ? pt : best), landscape[0]);
  const current = landscape.reduce((closest, pt) =>
    Math.abs(pt.priceMult - 1) < Math.abs(closest.priceMult - 1) ? pt : closest, landscape[0]);

  return { landscape, optimal, current, elasticityUsed: e };
}
