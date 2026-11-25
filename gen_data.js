// Generates 30 days of FAKE canteen orders + insights. Run: node gen_data.js
const fs = require('fs');
const ITEMS = require('./items.json');
let seed = 42; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const pad = n => String(n).padStart(2, '0');
// order-time weights: lunch rush peaks ~12:45-13:30
const hourW = m => { const d = (m - 13 * 60 + 10) / 40; return 0.15 + Math.exp(-d * d); };
const mins = []; for (let m = 9 * 60; m < 17 * 60; m++) mins.push(m);
const tot = mins.reduce((a, m) => a + hourW(m), 0);
const pickMinute = () => { let r = rnd() * tot; for (const m of mins) { r -= hourW(m); if (r <= 0) return m; } return 780; };
const pickItem = day => { // weekday bias: biryani Fri, chole Tue, etc.
  const w = ITEMS.map(i => i.pop * (i.boost === day ? 1.8 : 1)); let r = rnd() * w.reduce((a, b) => a + b);
  for (let k = 0; k < w.length; k++) { r -= w[k]; if (r <= 0) return ITEMS[k]; } return ITEMS[0]; };
const rows = ['date,weekday,time,item,quantity,price'];
const slotCount = {}, dayItem = {}, slotDay = {};
const start = new Date(); start.setDate(start.getDate() - 30);
for (let d = 0; d < 30; d++) {
  const dt = new Date(start); dt.setDate(start.getDate() + d); const wd = DAYS[dt.getDay()];
  if (wd === 'Sun') continue;
  const n = Math.round((wd === 'Fri' ? 330 : 400) + rnd() * 80);
  for (let k = 0; k < n; k++) {
    const m = pickMinute(), it = pickItem(wd), q = 1 + (rnd() < 0.25 ? 1 : 0);
    const t = `${pad(Math.floor(m / 60))}:${pad(m % 60)}`;
    rows.push(`${dt.toISOString().slice(0, 10)},${wd},${t},${it.name},${q},${it.price}`);
    const s = `${pad(Math.floor(m / 60))}:${pad(Math.floor(m % 60 / 15) * 15)}`;
    slotCount[s] = (slotCount[s] || 0) + 1;
    (dayItem[wd] ??= {})[it.name] = (dayItem[wd][it.name] || 0) + q;
    ((slotDay[wd] ??= {})[s] ??= {})[it.name] = (slotDay[wd][s][it.name] || 0) + q;
  }
}
const activeDays = {}; rows.slice(1).forEach(r => { const [dt, wd] = r.split(','); (activeDays[wd] ??= new Set()).add(dt); });
const peakSlots = Object.entries(slotCount).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([slot, orders]) => ({ slot, orders }));
const topByDay = {}, cookAhead = {};
for (const wd of Object.keys(dayItem)) {
  const nd = activeDays[wd].size;
  topByDay[wd] = Object.entries(dayItem[wd]).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([item, qty]) => ({ item, avgPerDay: Math.round(qty / nd) }));
  cookAhead[wd] = {};
  for (const [s, o] of Object.entries(slotDay[wd])) cookAhead[wd][s] = Object.entries(o).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([item, q]) => ({ item, qty: Math.ceil(q / nd) }));
}
fs.writeFileSync('data/orders.csv', rows.join('\n'));
fs.writeFileSync('data/insights.json', JSON.stringify({ totalOrders: rows.length - 1, peakSlots, topByDay, cookAhead }, null, 1));
console.log('orders:', rows.length - 1, '| peak slot:', peakSlots[0]);
