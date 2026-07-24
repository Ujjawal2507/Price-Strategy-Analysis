/**
 * businessRules.js
 * -----------------------------------------------------------------------
 * Applies governance constraints to a candidate recommendation. Nothing in
 * here is a "black box" number — every check returns a plain-language
 * reason so the dashboard can show why a price was approved or rejected.
 * -----------------------------------------------------------------------
 */

/**
 * @param {Object} candidate  a simulate()/optimizePrice() result, expects:
 *   { projectedMarginPct, demandChangePct, competitorGapPct, inventoryConstrained }
 * @param {Object} constraints  from data.js RULE_CONSTRAINTS
 */
export function evaluateRules(candidate, constraints) {
  const reasons = [];
  const violations = [];

  if (candidate.projectedMarginPct < constraints.minMarginPct) {
    violations.push(`Margin ${candidate.projectedMarginPct.toFixed(1)}% falls below the ${constraints.minMarginPct}% policy floor.`);
  } else {
    reasons.push(`Margin of ${candidate.projectedMarginPct.toFixed(1)}% clears the ${constraints.minMarginPct}% policy floor.`);
  }

  if (Math.abs(candidate.demandChangePct) > constraints.maxDemandLossPct && candidate.demandChangePct < 0) {
    violations.push(`Projected volume loss of ${Math.abs(candidate.demandChangePct).toFixed(1)}% exceeds the ${constraints.maxDemandLossPct}% tolerance.`);
  } else {
    reasons.push(`Projected demand change (${candidate.demandChangePct.toFixed(1)}%) is within tolerance.`);
  }

  if (candidate.competitorGapPct != null && candidate.competitorGapPct > constraints.maxCompetitorGapPct) {
    violations.push(`Priced ${candidate.competitorGapPct.toFixed(1)}% above the competitor, past the ${constraints.maxCompetitorGapPct}% ceiling.`);
  } else if (candidate.competitorGapPct != null) {
    reasons.push(`Competitor price gap (${candidate.competitorGapPct.toFixed(1)}%) is within the allowed band.`);
  }

  if (candidate.inventoryConstrained) {
    violations.push('Recommendation is currently capped by available inventory.');
  }

  let status = 'approved';
  if (violations.length >= 2) status = 'rejected';
  else if (violations.length === 1) status = 'conditionally_approved';

  return { status, reasons, violations };
}
