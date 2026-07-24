/**
 * app.js
 * -----------------------------------------------------------------------
 * The ONLY file that touches the DOM. It collects user input, calls
 * decisionEngine.runDecisionEngine() (and whatIfSimulator.simulate() for
 * the live sliders), and renders whatever comes back. No pricing math,
 * no elasticity formulas, no rule thresholds live in this file.
 * -----------------------------------------------------------------------
 */
import { DEPARTMENTS, WEEK_LABELS, totalWeeklyRevenue, GOVERNANCE, getProduct } from './data.js';
import { runDecisionEngine, listProducts } from './decisionEngine.js';
import { simulate } from './whatIfSimulator.js';

const $ = (id) => document.getElementById(id);
const fmtMoney = (n) => '$' + Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });
const fmtPct = (n) => `${n >= 0 ? '+' : ''}${n.toFixed(1)}%`;

let currentProductId = null;
let currentView = null; // cached last runDecisionEngine() result

// ---------------------------------------------------------------------
// Setup: selectors
// ---------------------------------------------------------------------
function initSelectors() {
  const products = listProducts();
  const productSelect = $('productSelect');
  products.forEach((p) => {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = `${p.commodity} (${p.brand}) — ${DEPARTMENTS[p.dept]?.label || p.dept}`;
    productSelect.appendChild(opt);
  });
  productSelect.addEventListener('change', (e) => selectProduct(Number(e.target.value)));

  currentProductId = products[0].id;
  productSelect.value = currentProductId;
}

function selectProduct(id) {
  currentProductId = id;
  currentView = runDecisionEngine(id);
  renderAll(currentView);
  resetWhatIfControls(currentView.product);
}

// ---------------------------------------------------------------------
// Render: Executive Overview
// ---------------------------------------------------------------------
function renderKpis(view) {
  const { product, primaryScenario, ruleResult } = view;
  const r = primaryScenario.result;
  const dept = DEPARTMENTS[product.dept] || { weekly: [1, 1] };
  const weeklySeries = dept.weekly;
  const growthPct = ((weeklySeries[weeklySeries.length - 1] - weeklySeries[0]) / weeklySeries[0]) * 100;
  const forecastTotal = weeklySeries.reduce((a, b) => a + b, 0) * (1 + growthPct / 100 / 4); // light 12-wk projection

  const kpis = [
    {
      label: 'Revenue Growth (12wk)', value: fmtPct(growthPct), target: 'Target: ≥ 0%',
      tag: growthPct >= 0 ? 'good' : 'bad',
    },
    {
      label: 'Gross Margin (recommended)', value: `${r.projectedMarginPct.toFixed(1)}%`, target: 'Target: ≥ 22%',
      tag: r.projectedMarginPct >= 22 ? 'good' : 'watch',
    },
    {
      label: 'Competitive Price Index', value: r.competitorGapPct != null ? `${r.competitorGapPct.toFixed(1)}%` : '—',
      target: 'Target: within ±15%',
      tag: r.competitorGapPct == null ? 'good' : Math.abs(r.competitorGapPct) <= 15 ? 'good' : 'watch',
    },
    {
      label: 'Pricing Health Score', value: `${r.pricingHealthScore}/100`, target: 'Target: ≥ 70',
      tag: r.pricingHealthScore >= 70 ? 'good' : r.pricingHealthScore >= 50 ? 'watch' : 'bad',
    },
    {
      label: 'Forecasted Revenue (12wk)', value: fmtMoney(forecastTotal), target: `Status: ${ruleResult.status.replace('_', ' ')}`,
      tag: ruleResult.status === 'approved' ? 'good' : ruleResult.status === 'rejected' ? 'bad' : 'watch',
    },
  ];

  $('kpiRow').innerHTML = kpis.map(k => `
    <div class="card kpi">
      <h3>${k.label}<span class="tag tag-${k.tag}">${k.tag === 'good' ? 'On target' : k.tag === 'bad' ? 'Off target' : 'Watch'}</span></h3>
      <div class="val">${k.value}</div>
      <div class="target">${k.target}</div>
    </div>
  `).join('');
}

function renderExecSummary(view) {
  const { product, primaryScenario, ruleResult, explanation } = view;
  const r = primaryScenario.result;
  const dept = DEPARTMENTS[product.dept];
  const topDept = Object.entries(DEPARTMENTS).sort((a, b) => b[1].weekly.at(-1) - a[1].weekly.at(-1))[0];

  const bullets = [
    `<b>Primary revenue driver:</b> ${topDept[1].label} produced the highest revenue last week (${fmtMoney(topDept[1].weekly.at(-1))}) among all departments.`,
    `<b>Biggest pricing risk:</b> ${ruleResult.violations.length ? ruleResult.violations[0] : `No active rule violations for ${product.commodity} at the recommended price.`}`,
    `<b>Recommended action:</b> ${explanation.summary}`,
  ];
  $('execSummaryList').innerHTML = bullets.map(b => `<li>${b}</li>`).join('');
}

// ---------------------------------------------------------------------
// Render: Business Drivers
// ---------------------------------------------------------------------
function renderDriverTree(view) {
  const { product, primaryScenario } = view;
  const r = primaryScenario.result;
  const nodes = [
    { label: 'Revenue', sub: fmtMoney(r.projectedRevenue) },
    { label: 'Volume', sub: `${r.projectedUnits.toFixed(0)} units (${fmtPct(r.demandChangePct)})` },
    { label: 'Avg. Selling Price', sub: `$${r.newPrice.toFixed(2)}` },
    { label: 'Promotion', sub: `${DEPARTMENTS[product.dept]?.promoShare ?? '—'}% of dept. sales on discount` },
    { label: 'Margin', sub: `${r.projectedMarginPct.toFixed(1)}% (cost basis: $${product.unitCost.toFixed(2)})` },
  ];
  $('driverTree').innerHTML = nodes.map((n, i) => `
    <div class="dt-row">
      ${i > 0 ? '<span class="arrow">→</span>' : ''}
      <div class="dt-node">${n.label}<div class="sub">${n.sub}</div></div>
    </div>
  `).join('');
}

function renderElasticity() {
  const entries = Object.entries(DEPARTMENTS);
  const maxAbs = Math.max(...entries.map(([, d]) => Math.min(8, Math.abs(d.elasticity))));
  $('elasticityBars').innerHTML = entries.map(([key, d]) => {
    const shown = Math.min(8, Math.abs(d.elasticity));
    return `
    <div class="bar-row" title="${d.note || ''}">
      <span class="lbl">${d.label}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(shown / maxAbs * 100).toFixed(0)}%"></div></div>
      <span class="bar-val">${d.elasticity.toFixed(2)}</span>
    </div>`;
  }).join('') + `<div style="font-size:11px;color:var(--ink-soft);margin-top:6px;">Gas &amp; Kiosk's true elasticity (-43.9) is capped at 8 for display and in the optimizer — see note on hover.</div>`;
}

function renderForecast(view) {
  const { product } = view;
  const dept = DEPARTMENTS[product.dept];
  const series = dept.weekly;
  // simple linear regression projection for the next 4 weeks
  const n = series.length;
  const xs = series.map((_, i) => i);
  const meanX = xs.reduce((a, b) => a + b, 0) / n;
  const meanY = series.reduce((a, b) => a + b, 0) / n;
  const slope = xs.reduce((s, x, i) => s + (x - meanX) * (series[i] - meanY), 0) / xs.reduce((s, x) => s + (x - meanX) ** 2, 0);
  const intercept = meanY - slope * meanX;
  const projected = [0, 1, 2, 3].map(k => intercept + slope * (n - 1 + k));
  const full = [...series, ...projected];

  const w = 640, h = 170, padX = 10, padY = 16, plotW = w - 2 * padX, plotH = h - padY - 24;
  const max = Math.max(...full), min = Math.min(...full);
  const pts = full.map((v, i) => {
    const x = padX + (i / (full.length - 1)) * plotW;
    const y = padY + (max === min ? plotH / 2 : (1 - (v - min) / (max - min)) * plotH);
    return [x, y];
  });
  const histPts = pts.slice(0, n).map(p => p.join(',')).join(' ');
  const fcPts = pts.slice(n - 1).map(p => p.join(',')).join(' ');

  const svg = document.querySelector('.forecast svg');
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  svg.innerHTML = `
    <polyline fill="none" stroke="#1E3A8A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="${histPts}"/>
    <polyline fill="none" stroke="#B45309" stroke-width="3" stroke-dasharray="5,5" stroke-linecap="round" stroke-linejoin="round" points="${fcPts}"/>
    <line x1="${padX}" y1="${padY + plotH}" x2="${w - padX}" y2="${padY + plotH}" stroke="#E3E6EC" stroke-width="1"/>
  `;
  $('forecastTitle').textContent = `12-Week Revenue Forecast — ${dept.label} (+4 wk projection)`;
  const trendDir = slope >= 0 ? 'trending up' : 'trending down';
  $('forecastNote').textContent = `Linear projection from the last 12 weeks: ${dept.label} revenue is ${trendDir} (~${fmtMoney(Math.abs(slope))}/week).`;
}

function renderCompetitive(view) {
  const { product } = view;
  const gap = product.priceGapPct;
  $('competitiveStats').innerHTML = `
    <div class="comp-stat"><span>Our price</span><b>$${product.currentPrice.toFixed(2)}</b></div>
    <div class="comp-stat"><span>Competitor price</span><b>$${product.competitorPrice.toFixed(2)}</b></div>
    <div class="comp-stat"><span>Price gap</span><b>${fmtPct(gap)}</b></div>
    <div class="comp-stat"><span>Market position</span><b>${product.position}</b></div>
  `;
}

// ---------------------------------------------------------------------
// Render: Strategic Actions
// ---------------------------------------------------------------------
function renderRecommendation(view) {
  const { explanation } = view;
  $('recSummary').textContent = explanation.summary;
  $('recDrivers').innerHTML = explanation.drivers.map(d => `• ${d}`).join('<br>');
  const statusTag = explanation.ruleStatus === 'approved' ? 'tag-good' : explanation.ruleStatus === 'rejected' ? 'tag-bad' : 'tag-watch';
  $('recBadges').innerHTML = `
    <span class="badge">Confidence: ${explanation.confidence.badge} (${explanation.confidence.confidenceScore}%)</span>
    <span class="badge">95% band: $${explanation.confidence.interval.low.toLocaleString()} – $${explanation.confidence.interval.high.toLocaleString()}</span>
    <span class="badge ${statusTag}">Rules: ${explanation.ruleStatus.replace('_', ' ')}</span>
  `;
}

function renderScenarios(view) {
  const { scenarios, primaryScenario } = view;
  $('scenarioBody').innerHTML = scenarios.map(s => `
    <tr class="${s.key === primaryScenario.key ? 'best' : ''}">
      <td>${s.label}</td>
      <td>$${s.result.newPrice.toFixed(2)}</td>
      <td>${fmtPct(s.result.demandChangePct)}</td>
      <td>${fmtMoney(s.result.projectedRevenue)}</td>
      <td>${fmtMoney(s.result.projectedProfit)}</td>
      <td>${s.result.projectedMarginPct.toFixed(1)}%</td>
    </tr>
  `).join('');
}

function renderRisks(view) {
  const { ruleResult, product } = view;
  const items = [];
  ruleResult.violations.forEach(v => items.push({ level: 'high', text: v }));
  if (Math.abs(product.priceGapPct) > 10 && product.priceGapPct > 0) {
    items.push({ level: 'med', text: `${product.commodity} is priced ${product.priceGapPct.toFixed(1)}% above the competitor — perception risk.` });
  }
  if (product.rSquared < 0.75) {
    items.push({ level: 'med', text: `Elasticity fit (R²=${product.rSquared.toFixed(2)}) is moderate — treat the recommendation as directional.` });
  }
  if (!items.length) items.push({ level: 'low', text: 'No material risks flagged for this SKU at the recommended price.' });

  $('riskList').innerHTML = items.map(i => `
    <div class="risk-row"><span class="risk-dot ${i.level}"></span><span>${i.text}</span></div>
  `).join('');
}

// ---------------------------------------------------------------------
// What-if sliders — live calls to whatIfSimulator.simulate() only
// ---------------------------------------------------------------------
function resetWhatIfControls(product) {
  $('priceChangeSlider').value = 0;
  $('priceChangeReadout').textContent = '0%';
  $('promoSlider').value = 0;
  $('promoReadout').textContent = '0';
  $('competitorSlider').min = 0;
  $('competitorSlider').max = (product.competitorPrice * 3).toFixed(2);
  $('competitorSlider').step = 0.05;
  $('competitorSlider').value = product.competitorPrice;
  $('competitorReadout').textContent = `$${product.competitorPrice.toFixed(2)}`;
  $('inventorySlider').value = 2000;
  $('inventoryReadout').textContent = 'Unlimited';
  runWhatIf();
}

function runWhatIf() {
  const product = getProduct(currentProductId);
  const priceChangePct = Number($('priceChangeSlider').value);
  const promoIntensity = Number($('promoSlider').value);
  const competitorPrice = Number($('competitorSlider').value);
  const inventoryRaw = Number($('inventorySlider').value);
  const inventoryAvailable = inventoryRaw >= 2000 ? null : inventoryRaw;

  $('priceChangeReadout').textContent = fmtPct(priceChangePct);
  $('promoReadout').textContent = promoIntensity;
  $('competitorReadout').textContent = `$${competitorPrice.toFixed(2)}`;
  $('inventoryReadout').textContent = inventoryAvailable == null ? 'Unlimited' : inventoryAvailable;

  const result = simulate({
    basePrice: product.currentPrice,
    baseDemand: 1000,
    elasticity: product.elasticity,
    unitCost: product.unitCost,
    priceChangePct,
    promoIntensity,
    competitorPrice,
    inventoryAvailable,
  });

  $('whatifResults').innerHTML = `
    <div class="stat"><div class="n">$${result.newPrice.toFixed(2)}</div><div class="l">New price</div></div>
    <div class="stat"><div class="n">${result.projectedUnits.toFixed(0)}</div><div class="l">Projected units</div></div>
    <div class="stat"><div class="n">${fmtMoney(result.projectedRevenue)}</div><div class="l">Revenue</div></div>
    <div class="stat"><div class="n">${fmtMoney(result.projectedProfit)}</div><div class="l">Profit</div></div>
    <div class="stat"><div class="n">${result.pricingHealthScore}/100</div><div class="l">Pricing health</div></div>
  `;
}

['priceChangeSlider', 'promoSlider', 'competitorSlider', 'inventorySlider'].forEach(id => {
  document.addEventListener('input', (e) => { if (e.target.id === id) runWhatIf(); });
});

// ---------------------------------------------------------------------
// Footer / governance
// ---------------------------------------------------------------------
function renderGovernance() {
  $('govSource').textContent = `Data: ${GOVERNANCE.dataSource}`;
  $('govQuality').textContent = `Quality: ${GOVERNANCE.dataQuality}`;
  $('govRefreshed').textContent = GOVERNANCE.lastRefreshed;
  $('govOwner').textContent = `Owner: ${GOVERNANCE.owner}`;
}

// ---------------------------------------------------------------------
function renderAll(view) {
  renderKpis(view);
  renderExecSummary(view);
  renderDriverTree(view);
  renderElasticity();
  renderForecast(view);
  renderCompetitive(view);
  renderRecommendation(view);
  renderScenarios(view);
  renderRisks(view);
}

initSelectors();
renderGovernance();
selectProduct(currentProductId);
