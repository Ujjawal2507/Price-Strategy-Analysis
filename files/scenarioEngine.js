/**
 * scenarioEngine.js
 * -----------------------------------------------------------------------
 * Generates the standard set of alternatives decision-makers want to see
 * side by side: hold, +5%, +10%, -5%, and the optimizer's own pick.
 * Delegates all math to whatIfSimulator.simulate() and optimization.js —
 * this file only defines *which* scenarios to run and packages the results.
 * -----------------------------------------------------------------------
 */
import { simulate } from './whatIfSimulator.js';

/**
 * @param {Object} product        a row from data.js PRODUCTS (with unitCost)
 * @param {number} baseDemand     demand index at current price
 * @param {Object} optimizerResult  result of optimization.optimizePrice()
 */
export function generateScenarios(product, baseDemand, optimizerResult) {
  const shared = {
    basePrice: product.currentPrice,
    baseDemand,
    elasticity: product.elasticity,
    unitCost: product.unitCost,
    competitorPrice: product.competitorPrice,
  };

  const scenarios = [
    { key: 'hold', label: 'Hold current price', priceChangePct: 0 },
    { key: 'up5', label: '+5% price', priceChangePct: 5 },
    { key: 'up10', label: '+10% price', priceChangePct: 10 },
    { key: 'down5', label: '-5% price', priceChangePct: -5 },
    {
      key: 'optimized',
      label: 'Optimizer recommendation',
      priceChangePct: +(((optimizerResult.optimal.price - product.currentPrice) / product.currentPrice) * 100).toFixed(2),
    },
  ];

  return scenarios.map(s => ({
    ...s,
    result: simulate({ ...shared, priceChangePct: s.priceChangePct }),
  }));
}
