// Browser controller: the server supplies MCU snapshots and the archive;
// this file formats responses and posts only experiment start/stop requests.
const $ = (selector) => document.querySelector(selector);
const historyPoints = [];
let state = null;
let feedbackTimer = null;

function showNotice(message, isError = false) {
  const el = $('#operator-feedback');
  el.textContent = message;
  el.classList.toggle('error', isError);
  el.classList.toggle('pending', !isError && /starting|saving|refreshing/i.test(message));
  el.classList.remove('hidden');
  clearTimeout(feedbackTimer);
  if (!isError && !/starting|saving|refreshing/i.test(message)) {
    feedbackTimer = setTimeout(() => el.classList.add('hidden'), 6500);
  }
}
function showConnectionNotice(message) {
  const el = $('#notice');
  el.textContent = message;
  el.classList.add('error');
  el.classList.remove('hidden');
}
function clearNotice() { $('#notice').classList.add('hidden'); }
function valueText(value, digits = 3) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—';
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 });
}
function stateBadge(el, text) {
  const safe = String(text || 'UNKNOWN').toUpperCase();
  el.textContent = safe;
  el.className = `state-badge ${safe.toLowerCase()}`;
}
function renderTelemetry(next) {
  state = next;
  const latest = next.latest;
  const connected = next.connected && latest?.data;
  $('#connection-dot').classList.toggle('online', Boolean(connected));
  $('#connection-dot').classList.toggle('offline', !connected);
  $('#connection-label').textContent = connected ? 'Board connected' : 'Board unavailable';
  $('#connection-detail').textContent = connected ? 'Router Bridge · telemetry active' : (next.last_error || 'Waiting for Router Bridge');
  $('#start-run').disabled = !connected || next.recording;
  renderRecording(next.active_run, next.recording);
  if (!connected) {
    $('#mode-chip').textContent = 'OFFLINE';
    $('#mode-chip').className = 'mode-chip';
    showConnectionNotice(next.last_error ? `Bridge connection issue: ${next.last_error}` : 'Waiting for the MCU telemetry connection.');
    return;
  }
  clearNotice();
  const data = latest.data;
  const mode = String(data.mode || 'unknown').toLowerCase();
  $('#mode-chip').textContent = mode.toUpperCase();
  $('#mode-chip').className = `mode-chip ${mode}`;
  const source = mode === 'synthetic' ? 'Synthetic simulation' : 'Live sensor inputs';
  $('#source-value').textContent = source;
  $('#experiment-source').textContent = source;
  $('#loop-ticks').textContent = valueText(data.loop_ticks, 0);
  $('#updated-at').textContent = new Date(latest.timestamp_utc).toLocaleTimeString();

  const temp = data.temp_c || {};
  const hx = data.hx711_counts || {};
  const distance = data.distance_cm || {};
  const spectral = data.spectral || {};
  stateBadge($('#temp-state'), temp.state);
  stateBadge($('#hx-state'), hx.state);
  stateBadge($('#distance-state'), distance.state);
  stateBadge($('#spectral-state'), spectral.state);
  $('#temp-value').textContent = valueText(temp.value, 3);
  $('#hx-value').textContent = valueText(hx.value, 0);
  $('#hx-foot').textContent = data.hx711_calibrated ? `HX711 · ${valueText(data.hx711_grams, 2)} g calibrated` : (mode === 'synthetic' ? 'HX711 · simulated counts' : 'HX711 · not calibrated');
  $('#distance-value').textContent = valueText(distance.value, 2);
  $('#spectral-gain').textContent = spectral.gain_code ?? '—';
  renderSpectrum(spectral.channels || []);

  const uptime = Number(data.uptime_ms);
  if (Number.isFinite(uptime) && (!historyPoints.length || historyPoints[historyPoints.length - 1].uptime !== uptime)) {
    historyPoints.push({time: Date.parse(latest.timestamp_utc), uptime, value: temp.value, state: temp.state});
    while (historyPoints.length > 300) historyPoints.shift();
  }
  drawChart();
}
function renderSpectrum(channels) {
  const holder = $('#spectral-bars');
  if (holder.childElementCount !== channels.length) {
    holder.replaceChildren(...channels.map((_, i) => {
      const bar = document.createElement('span');
      bar.className = 'spectral-bar';
      bar.setAttribute('aria-label', `Channel ${i + 1}`);
      return bar;
    }));
  }
  const max = Math.max(1, ...channels.map(Number));
  [...holder.children].forEach((bar, i) => {
    const amount = Number(channels[i]) || 0;
    bar.style.height = `${Math.max(4, amount / max * 100)}%`;
    bar.title = `Slot ${i + 1}: ${amount.toLocaleString()} counts`;
  });
}
function drawChart() {
  const canvas = $('#temperature-chart');
  const wrap = canvas.parentElement;
  const dpr = window.devicePixelRatio || 1;
  const width = wrap.clientWidth;
  const height = wrap.clientHeight;
  if (!width || !height) return;
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  const now = Date.now();
  // Show the last five minutes and omit missing/faulted readings instead of
  // drawing them as genuine zero-degree measurements.
  const points = historyPoints.filter(p => p.time > now - 300000 && Number.isFinite(Number(p.value)) && ['OK', 'SYNTH'].includes(p.state));
  $('#chart-empty').textContent = points.length ? 'Collecting temperature points…' : 'Waiting for telemetry…';
  $('#chart-empty').classList.toggle('hidden', points.length >= 2);
  if (points.length < 2) return;
  const pad = {left: 42, right: 13, top: 14, bottom: 27};
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  let min = Math.min(...points.map(p => Number(p.value)));
  let max = Math.max(...points.map(p => Number(p.value)));
  if (max - min < .2) { min -= .1; max += .1; }
  const margin = (max - min) * .18;
  min -= margin; max += margin;
  ctx.font = '10px Manrope, sans-serif';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 3; i++) {
    const y = pad.top + plotH * i / 3;
    const value = max - (max - min) * i / 3;
    ctx.strokeStyle = '#3a485e'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(width - pad.right, y); ctx.stroke();
    ctx.fillStyle = '#aab8ca'; ctx.fillText(value.toFixed(1), pad.left - 8, y + 3);
  }
  const first = points[0].time, last = points[points.length - 1].time;
  ctx.textAlign = 'center'; ctx.fillStyle = '#aab8ca';
  for (let i = 0; i <= 3; i++) {
    const x = pad.left + plotW * i / 3;
    const t = first + (last - first) * i / 3;
    ctx.fillText(new Date(t).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', second: '2-digit'}), x, height - 7);
  }
  const coords = points.map(p => ({
    x: pad.left + (last === first ? .5 : (p.time - first) / (last - first)) * plotW,
    y: pad.top + (max - Number(p.value)) / (max - min) * plotH,
  }));
  const gradient = ctx.createLinearGradient(0, pad.top, 0, pad.top + plotH);
  gradient.addColorStop(0, 'rgba(139,219,231,.22)'); gradient.addColorStop(1, 'rgba(139,219,231,0)');
  ctx.beginPath(); coords.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y));
  ctx.lineTo(coords[coords.length - 1].x, pad.top + plotH); ctx.lineTo(coords[0].x, pad.top + plotH); ctx.closePath();
  ctx.fillStyle = gradient; ctx.fill();
  ctx.beginPath(); coords.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y));
  ctx.strokeStyle = '#8bdbe7'; ctx.lineWidth = 2; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke();
  const tail = coords[coords.length - 1];
  ctx.beginPath(); ctx.arc(tail.x, tail.y, 3.5, 0, Math.PI * 2); ctx.fillStyle = '#202d42'; ctx.fill();
  ctx.lineWidth = 2; ctx.strokeStyle = '#b9edf0'; ctx.stroke();
}
function renderRecording(run, active) {
  const chip = $('#recording-chip');
  chip.classList.toggle('active', Boolean(active));
  chip.innerHTML = `<i></i> ${active ? 'RECORDING' : 'NOT RECORDING'}`;
  $('#run-name').disabled = Boolean(active);
  $('#sample-interval').disabled = Boolean(active);
  $('#run-notes').disabled = Boolean(active);
  $('#start-run').classList.toggle('hidden', Boolean(active));
  $('#stop-run').classList.toggle('hidden', !active);
  $('#tab-recording-badge').classList.toggle('hidden', !active);
  $('#run-summary-chip').textContent = active ? 'RECORDING' : 'NO ACTIVE RUN';
  $('#run-summary-chip').classList.toggle('active', Boolean(active));
  $('#monitor-run-title').textContent = active && run ? run.name : 'Ready to record';
  $('#monitor-run-copy').textContent = active && run
    ? `${run.sample_count} samples captured · ${valueText(run.sample_interval_s, 0)} second interval`
    : 'Create a named run to store timestamped MCU snapshots on the Linux side.';
  const activeBox = $('#active-run');
  activeBox.classList.toggle('hidden', !active || !run);
  if (active && run) activeBox.innerHTML = `<span>“${escapeHtml(run.name)}” · started ${new Date(run.started_at_utc).toLocaleTimeString()}</span><strong>${run.sample_count} samples</strong>`;
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
async function refreshState() {
  try {
    const response = await fetch('/api/state', {cache: 'no-store'});
    const data = await response.json();
    renderTelemetry(data);
  } catch (error) {
    renderTelemetry({connected: false, last_error: 'Dashboard API unavailable', latest: null, recording: false});
  }
}
async function refreshRuns() {
  // Run names are untrusted input; construct their table cells with textContent.
  try {
    const response = await fetch('/api/runs', {cache: 'no-store'});
    const data = await response.json();
    const body = $('#runs-body');
    if (!data.runs.length) {
      body.innerHTML = '<tr><td colspan="6" class="table-empty">No recorded experiments yet.</td></tr>';
      $('#archive-count').textContent = '0 RUNS';
      return true;
    }
    $('#archive-count').textContent = `${data.runs.length} RUN${data.runs.length === 1 ? '' : 'S'}`;
    body.replaceChildren(...data.runs.map(run => {
      const tr = document.createElement('tr');
      const name = document.createElement('td'); name.textContent = run.name;
      const started = document.createElement('td'); started.textContent = new Date(run.started_at_utc).toLocaleString();
      const mode = document.createElement('td'); mode.textContent = run.mode_at_start;
      const count = document.createElement('td'); count.textContent = run.sample_count;
      const status = document.createElement('td');
      const active = !run.ended_at_utc;
      status.innerHTML = `<span class="table-status ${active ? 'active' : ''}">${active ? '● Recording' : 'Complete'}</span>`;
      const action = document.createElement('td');
      if (!active) {
        const link = document.createElement('a');
        link.className = 'download-link'; link.href = `/api/runs/${encodeURIComponent(run.run_id)}/csv`;
        link.textContent = 'Download CSV'; action.append(link);
      }
      tr.append(name, started, mode, count, status, action);
      return tr;
    }));
    return true;
  } catch (error) { return false; /* keep the last rendered archive */ }
}
$('#run-form').addEventListener('submit', async event => {
  event.preventDefault();
  const button = $('#start-run'); button.disabled = true;
  const label = button.querySelector('span');
  label.textContent = 'Starting…';
  showNotice('Starting experiment recording…');
  try {
    const response = await fetch('/api/runs', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: $('#run-name').value, interval_s: Number($('#sample-interval').value), notes: $('#run-notes').value}),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not start experiment.');
    await refreshState(); await refreshRuns();
    showNotice(`Recording “${result.run.name}” started. Samples will be saved every ${result.run.sample_interval_s} seconds.`);
  } catch (error) {
    showNotice(error.message, true);
    button.disabled = !state?.connected;
  } finally {
    label.textContent = 'Start recording';
  }
});
$('#stop-run').addEventListener('click', async () => {
  const button = $('#stop-run');
  button.disabled = true;
  button.textContent = 'Saving…';
  showNotice('Saving experiment and finalizing its CSV…');
  try {
    const response = await fetch('/api/runs/stop', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not stop experiment.');
    await refreshState(); await refreshRuns();
    showNotice(`Run “${result.run.name}” saved with ${result.run.sample_count} samples. Download it from Archive.`);
  } catch (error) { showNotice(error.message, true); }
  finally { button.disabled = false; button.textContent = 'Stop run'; }
});
$('#refresh-runs').addEventListener('click', async () => {
  const button = $('#refresh-runs');
  button.disabled = true;
  button.innerHTML = 'Refreshing archive… <span>↻</span>';
  showNotice('Refreshing experiment archive…');
  const refreshed = await refreshRuns();
  if (!refreshed) {
    button.innerHTML = 'Retry archive <span>↻</span>';
    showNotice('Could not refresh the experiment archive. Try again.', true);
    setTimeout(() => { button.innerHTML = 'Refresh archive <span>↻</span>'; button.disabled = false; }, 1400);
    return;
  }
  button.innerHTML = 'Archive updated <span>✓</span>';
  showNotice('Experiment archive is up to date.');
  setTimeout(() => { button.innerHTML = 'Refresh archive <span>↻</span>'; button.disabled = false; }, 1400);
});

const tabButtons = [...document.querySelectorAll('[role="tab"]')];
// Follow the ARIA tabs keyboard model: one tab stop plus arrow/Home/End
// navigation, with panel visibility tied to the selected tab.
function activateTab(tabId, moveFocus = false) {
  for (const tab of tabButtons) {
    const selected = tab.id === tabId;
    tab.classList.toggle('active', selected);
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
    const panel = document.getElementById(tab.getAttribute('aria-controls'));
    panel.classList.toggle('hidden', !selected);
    if (selected && moveFocus) tab.focus();
  }
  try { localStorage.setItem('spirit-dashboard-tab', tabId); } catch (error) { /* storage may be disabled */ }
  if (tabId === 'tab-monitor') requestAnimationFrame(drawChart);
  window.scrollTo({top: 0, behavior: 'smooth'});
}
tabButtons.forEach((tab, index) => {
  tab.addEventListener('click', () => activateTab(tab.id));
  tab.addEventListener('keydown', event => {
    let nextIndex = null;
    if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabButtons.length;
    if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabButtons.length) % tabButtons.length;
    if (event.key === 'Home') nextIndex = 0;
    if (event.key === 'End') nextIndex = tabButtons.length - 1;
    if (nextIndex !== null) { event.preventDefault(); activateTab(tabButtons[nextIndex].id, true); }
  });
});
document.querySelectorAll('[data-open-tab]').forEach(button => button.addEventListener('click', () => activateTab(`tab-${button.dataset.openTab}`, true)));
try {
  const savedTab = localStorage.getItem('spirit-dashboard-tab');
  if (tabButtons.some(tab => tab.id === savedTab)) activateTab(savedTab);
} catch (error) { /* storage may be disabled */ }
window.addEventListener('resize', drawChart);
refreshState(); refreshRuns();
setInterval(refreshState, 1500);
setInterval(() => { if (state?.recording) refreshRuns(); }, 5000);

const fontSizeSelect = $('#font-size-select');
// Scale authored CSS type only; saved preference is local to this browser.
function setFontSize(size) {
  const allowed = ['normal', 'large', 'largest'];
  const selected = allowed.includes(size) ? size : 'normal';
  document.documentElement.dataset.fontSize = selected;
  fontSizeSelect.value = selected;
  try { localStorage.setItem('spirit-dashboard-font-size', selected); } catch (error) { /* storage may be disabled */ }
}
fontSizeSelect.addEventListener('change', () => setFontSize(fontSizeSelect.value));
try { setFontSize(localStorage.getItem('spirit-dashboard-font-size') || 'normal'); }
catch (error) { setFontSize('normal'); }
