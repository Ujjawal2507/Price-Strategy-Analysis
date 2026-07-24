/**
 * recommendationEngine.js
 * -----------------------------------------------------------------------
 * Builds the plain-language "why" behind a recommendation. Takes outputs
 * that other engines already computed and assembles them into a single
 * explanation object — it does not compute anything new itself.
 * -----------------------------------------------------------------------
 */

/**
 * @param {Object} product
 * @param {Object} scenario        the chosen scenario from scenarioEngine
 * @param {Object} ruleResult      from businessRules.evaluateRules()
 * @param {Object} confidenceResult from uncertainty.estimateConfidence()
 */
export function explainRecommendation(product, scenario, ruleResult, confidenceResult) {
  const r = scenario.result;
  const direction = scenario.priceChangePct > 0 ? 'increase' : scenario.priceChangePct < 0 ? 'decrease' : 'hold';

  const drivers = [
    `Elasticity of ${product.elasticity.toFixed(2)} means a ${Math.abs(scenario.priceChangePct).toFixed(1)}% price ${direction} is expected to move volume by ${r.demandChangePct.toFixed(1)}%.`,
    `Projected revenue: $${r.projectedRevenue.toLocaleString()}; projected margin: ${r.projectedMarginPct.toFixed(1)}%.`,
    r.competitorGapPct != null
      ? `Resulting competitor price gap: ${r.competitorGapPct.toFixed(1)}% (${product.position}).`
      : `No competitor benchmark available for this SKU.`,
    r.inventoryConstrained
      ? `Inventory is currently the binding constraint on volume.`
      : `Inventory is not a binding constraint at this volume.`,
  ];

  const assumptions = [
    `Unit cost is back-solved from a flat ${(product.marginAssumption * 100).toFixed(0)}% target margin (no direct cost feed in the source data).`,
    `Competitor prices are simulated placeholders, not a live feed (per competitor_price_comparison.csv).`,
    `Elasticity fit quality (R² = ${product.rSquared.toFixed(2)}, n = ${product.n}) drives the confidence badge below.`,
  ];

  return {
    productId: product.id,
    summary: `${direction === 'hold' ? 'Hold' : direction === 'increase' ? 'Increase' : 'Decrease'} ${product.commodity} price by ${Math.abs(scenario.priceChangePct).toFixed(1)}% — expected profit ${r.projectedProfit >= 0 ? 'of' : 'change of'} $${r.projectedProfit.toLocaleString()}, confidence: ${confidenceResult.badge} (${confidenceResult.confidenceScore}%).`,
    drivers,
    assumptions,
    ruleStatus: ruleResult.status,
    ruleReasons: ruleResult.reasons,
    ruleViolations: ruleResult.violations,
    confidence: confidenceResult,
  };
}
