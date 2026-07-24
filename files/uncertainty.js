/**
 * uncertainty.js
 * -----------------------------------------------------------------------
 * Turns model-fit statistics (R², p-value, sample size) into a confidence
 * badge and an approximate interval around a projected number. This is a
 * transparent heuristic, not a formal bootstrap — it is explicitly labeled
 * as approximate everywhere it is displayed.
 * -----------------------------------------------------------------------
 */

/**
 * @param {Object} p
 * @param {number} p.rSquared        0-1, regression fit quality
 * @param {number} p.pValue          statistical significance of elasticity
 * @param {number} p.n               observations used to fit elasticity
 * @param {number} p.pointEstimate   the number to wrap an interval around (e.g. profit)
 */
export function estimateConfidence({ rSquared, pValue, n, pointEstimate }) {
  // Composite confidence score (0-100): fit quality + significance + sample size
  const fitScore = Math.max(0, Math.min(1, rSquared)) * 55;
  const sigScore = (pValue <= 0.05 ? 1 : Math.max(0, 1 - pValue)) * 25;
  const sampleScore = Math.min(1, n / 50) * 20;
  const confidenceScore = Math.round(fitScore + sigScore + sampleScore);

  const badge = confidenceScore >= 75 ? 'High' : confidenceScore >= 50 ? 'Medium' : 'Low';

  // Wider interval when fit is weaker or sample is small
  const uncertaintyFactor = (1 - Math.max(0, Math.min(1, rSquared))) * (1 / Math.sqrt(Math.max(1, n))) * 4;
  const halfWidth = Math.abs(pointEstimate) * Math.max(0.03, Math.min(0.6, uncertaintyFactor));

  return {
    confidenceScore,
    badge,
    interval: {
      low: +(pointEstimate - halfWidth).toFixed(2),
      high: +(pointEstimate + halfWidth).toFixed(2),
    },
  };
}
