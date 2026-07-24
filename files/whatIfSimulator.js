/**
 * whatIfSimulator.js
 * -----------------------------------------------------------------------
 * Recalculates business outcomes when the user drags a slider or edits an
 * input box. No HTML, no event listeners — app.js owns the UI and simply
 * calls simulate() with whatever the current control values are.
 * -----------------------------------------------------------------------
 */

/**
 * @param {Object} p
 * @param {number} p.basePrice
 * @param {number} p.baseDemand
 * @param {number} p.elasticity
 * @param {number} p.unitCost
 * @param {number} [p.priceChangePct=0]      e.g. 5 means +5%
 * @param {number} [p.promoIntensity=0]      0-100, % of a standard promo lift
 * @param {number} [p.competitorPrice]       used for gap + a small cross-price effect
 * @param {number} [p.inventoryAvailable]    caps units sold if provided
 * @param {number} [p.marketDemandIndex=100] 100 = normal market conditions
 */
export function simulate({
  basePrice,
  baseDemand,
  elasticity,
  unitCost,
  priceChangePct = 0,
  promoIntensity = 0,
  competitorPrice = null,
  inventoryAvailable = null,
  marketDemandIndex = 100,
}) {
  const e = Math.max(-8, Math.min(8, elasticity));
  const newPrice = +(basePrice * (1 + priceChangePct / 100)).toFixed(4);

  // Own-price effect
  let demand = baseDemand * Math.pow(newPrice / basePrice, e);

  // Promotion lift: each 10 points of intensity adds ~4% volume, diminishing
  demand *= 1 + (Math.log1p(promoIntensity / 10) * 0.04);

  // Cross-price effect vs. competitor: if we're priced further above the
  // competitor than before, shave a little demand; if further below, add a
  // little — small assumed cross-elasticity of 0.3.
  let competitorGapPct = null;
  if (competitorPrice) {
    competitorGapPct = +(((newPrice - competitorPrice) / competitorPrice) * 100).toFixed(2);
    const baseGapPct = ((basePrice - competitorPrice) / competitorPrice) * 100;
    const gapDelta = (competitorGapPct - baseGapPct) / 100;
    demand *= 1 - gapDelta * 0.3;
  }

  // Broader market conditions
  demand *= marketDemandIndex / 100;

  // Inventory ceiling
  let inventoryConstrained = false;
  if (inventoryAvailable != null && demand > inventoryAvailable) {
    demand = inventoryAvailable;
    inventoryConstrained = true;
  }

  demand = Math.max(0, demand);
  const revenue = newPrice * demand;
  const profit = (newPrice - unitCost) * demand;
  const marginPct = newPrice > 0 ? ((newPrice - unitCost) / newPrice) * 100 : 0;
  const demandChangePct = +(((demand - baseDemand) / baseDemand) * 100).toFixed(2);

  // Composite pricing health score (0-100): rewards margin health, penalizes
  // large demand loss and large competitor gaps. Purely a heuristic index
  // for the dashboard, not a statistical estimate.
  const marginScore = Math.max(0, Math.min(100, marginPct * 2.2));
  const demandScore = Math.max(0, 100 - Math.abs(demandChangePct) * 1.5);
  const gapScore = competitorGapPct == null ? 80 : Math.max(0, 100 - Math.abs(competitorGapPct) * 3);
  const pricingHealthScore = Math.round(marginScore * 0.4 + demandScore * 0.35 + gapScore * 0.25);

  return {
    newPrice,
    projectedUnits: +demand.toFixed(2),
    projectedRevenue: +revenue.toFixed(2),
    projectedProfit: +profit.toFixed(2),
    projectedMarginPct: +marginPct.toFixed(2),
    demandChangePct,
    competitorGapPct,
    inventoryConstrained,
    pricingHealthScore,
  };
}
