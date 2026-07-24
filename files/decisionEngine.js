/**
 * decisionEngine.js
 * -----------------------------------------------------------------------
 * The one module app.js is allowed to call for anything analytical. It
 * orchestrates optimization -> scenarios -> business rules -> confidence
 * -> explanation, and hands back one structured object. app.js never talks
 * to optimization.js, businessRules.js, etc. directly.
 * -----------------------------------------------------------------------
 */
import { PRODUCTS, DEPARTMENTS, RULE_CONSTRAINTS, getProduct } from './data.js';
import { optimizePrice } from './optimization.js';
import { simulate } from './whatIfSimulator.js';
import { generateScenarios } from './scenarioEngine.js';
import { evaluateRules } from './businessRules.js';
import { estimateConfidence } from './uncertainty.js';
import { explainRecommendation } from './recommendationEngine.js';

const BASE_DEMAND_INDEX = 1000; // arbitrary shared index; only relative movement matters

/**
 * Run the full decision workflow for a single product.
 * @param {number} productId
 * @param {Object} [whatIf]  optional live overrides from the UI sliders
 */
export function runDecisionEngine(productId, whatIf = {}) {
  const product = getProduct(productId);
  if (!product) throw new Error(`Unknown product id: ${productId}`);

  const optimizerResult = optimizePrice({
    currentPrice: product.currentPrice,
    elasticity: product.elasticity,
    unitCost: product.unitCost,
    baseDemand: BASE_DEMAND_INDEX,
  });

  const scenarios = generateScenarios(product, BASE_DEMAND_INDEX, optimizerResult);

  // The optimizer's own pick is the "primary" recommendation shown up top
  const primaryScenario = scenarios.find(s => s.key === 'optimized');

  const ruleResult = evaluateRules(primaryScenario.result, RULE_CONSTRAINTS);

  const confidenceResult = estimateConfidence({
    rSquared: product.rSquared,
    pValue: product.pValue,
    n: product.n,
    pointEstimate: primaryScenario.result.projectedProfit,
  });

  const explanation = explainRecommendation(product, primaryScenario, ruleResult, confidenceResult);

  // Optional live what-if override (from sliders), evaluated the same way
  let liveResult = null;
  if (Object.keys(whatIf).length) {
    liveResult = simulate({
      basePrice: product.currentPrice,
      baseDemand: BASE_DEMAND_INDEX,
      elasticity: product.elasticity,
      unitCost: product.unitCost,
      competitorPrice: product.competitorPrice,
      ...whatIf,
    });
  }

  return {
    product,
    optimizerResult,
    scenarios,
    primaryScenario,
    ruleResult,
    confidenceResult,
    explanation,
    liveResult,
  };
}

export function listProducts() {
  return PRODUCTS.map(p => ({ id: p.id, dept: p.dept, commodity: p.commodity, brand: p.brand }));
}

export function listDepartments() {
  return Object.entries(DEPARTMENTS).map(([key, d]) => ({ key, ...d }));
}
