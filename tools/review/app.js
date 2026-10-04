'use strict';

const TOOL = 'inkraft-pruefung 1.1';
const REVIEWER = 'Niklas Wichter';
const STORE_KEY = 'inkraft-pruefung-v1';
const DATA_KEY = 'inkraft-pruefung-data-v1';
const LANGS = ['de', 'fr', 'it'];
const LANG_LABEL = { de: 'Deutsch', fr: 'Französisch', it: 'Italienisch' };
const IDLE_MS = 120000;

// Single place that maps dataset field names to the tool's vocabulary. First existing path wins.
const FIELD_MAP = {
  id: ['id', 'item_id'],
  core: ['core_id'],
  lang: ['lang', 'language'],
  question: ['question'],
  answer: ['answer', 'gold_answer'],
  aliases: ['answer_aliases', 'answer_variants', 'aliases'],
  answerCore: ['answer_core'],
  outdated: ['outdated_answers', 'outdated'],
  nearMiss: ['near_miss_answers', 'near_miss'],
  quote: ['source.quote', 'quote'],
  evidence: ['source.evidence', 'evidence'],
  act: ['source.act', 'act'],
  article: ['source.article_id', 'article_id'],
  articleNo: ['source.article', 'article'],
  paragraph: ['source.paragraph', 'paragraph'],
  versionDate: ['source.version_date', 'version_date'],
  articleUrl: ['source.article_url', 'article_url'],
  eliUrl: ['source.eli_url', 'eli_url'],
  generator: ['generator', 'author'],
  generatorModel: ['generator_model'],
  author: ['author'],
  status: ['status'],
  needsReview: ['needs_human_review'],
  qtype: ['question_type'],
  domain: ['domain'],
  register: ['register'],
  answerType: ['answer_type'],
  answerNorm: ['answer_normalized'],
  calc: ['calc'],
  calcEvidence: ['calc_evidence', 'source.calc_evidence'],
  bucket: ['temporal.bucket'],
  changedOn: ['temporal.changed_on'],
  prevVersion: ['temporal.previous_version_date'],
  prevUrl: ['temporal.previous_eli_url'],
  prevParagraph: ['temporal.previous_paragraph'],
  prevQuote: ['temporal.previous_quote'],
  prevEvidence: ['temporal.previous_evidence'],
  futureChange: ['future_change'],
  manualCorrection: ['authoring.manual_correction'],
};

const EDITABLE = [
  { key: 'question', label: 'Frage', kind: 'text' },
  { key: 'answer', label: 'Antwort', kind: 'line', cls: 'answer' },
  { key: 'answerCore', label: 'Antwortkern (wörtlich)', kind: 'line', optional: true },
  { key: 'aliases', label: 'Antwortvarianten', kind: 'list' },
  { key: 'nearMiss', label: 'Near-Miss (plausibel falsch)', kind: 'list' },
  { key: 'outdated', label: 'Veraltete Antworten', kind: 'list' },
  { key: 'evidence', label: 'Evidenz (wörtlich)', kind: 'text' },
  { key: 'calcEvidence', label: 'Rechen-Evidenz', kind: 'list', optional: true },
  { key: 'prevEvidence', label: 'Evidenz Vorfassung', kind: 'text', optional: true },
  { key: 'quote', label: 'Zitat (Absatz)', kind: 'text', collapsed: true },
  { key: 'paragraph', label: 'Absatz', kind: 'line', collapsed: true },
  { key: 'article', label: 'Artikel-ID', kind: 'line', collapsed: true },
];

const REJECT_REASONS = [
  ['wrong_answer', 'Antwort widerspricht dem Gesetz'],
  ['ambiguous', 'Mehr als eine vertretbare Antwort'],
  ['quote_mismatch', 'Zitat/Evidenz nicht wörtlich belegt'],
  ['unclear_question', 'Frage ohne Artikel nicht verständlich'],
  ['excluded_topic', 'Ausschlussregel (kantonal, politisch offen, Bundesrat)'],
  ['lang_mismatch', 'FR/IT nicht gleichwertig'],
  ['outdated_unsupported', 'Veraltete Antwort nicht belegt'],
  ['duplicate', 'Doppelung'],
  ['other', 'Anderer Grund'],
];

const DECISION_LABEL = { accept: 'korrekt', correct: 'korrigiert', reject: 'verworfen', later: 'später', reset: 'zurückgenommen' };

const NUM_WORDS = {
  de: { null: 0, ein: 1, eine: 1, einen: 1, einem: 1, einer: 1, eines: 1, zwei: 2, drei: 3, vier: 4, fünf: 5, sechs: 6, sieben: 7, acht: 8, neun: 9, zehn: 10, elf: 11, zwölf: 12, fünfzehn: 15, zwanzig: 20, dreissig: 30, vierzig: 40, fünfzig: 50, sechzig: 60, neunzig: 90, hundert: 100, erste: 1, ersten: 1, zweite: 2, zweiten: 2, dritte: 3, dritten: 3, vierte: 4, vierten: 4, fünfte: 5, fünften: 5, sechste: 6, sechsten: 6, siebte: 7, siebten: 7, achte: 8, zehnte: 10, zehnten: 10, fünftel: 5 },
  fr: { un: 1, une: 1, deux: 2, trois: 3, quatre: 4, cinq: 5, six: 6, sept: 7, huit: 8, neuf: 9, dix: 10, onze: 11, douze: 12, quatorze: 14, quinze: 15, vingt: 20, trente: 30, quarante: 40, cinquante: 50, soixante: 60, cent: 100, premier: 1, première: 1, deuxième: 2, troisième: 3, quatrième: 4, cinquième: 5, cinquièmes: 5, sixième: 6, dixième: 10 },
  it: { un: 1, uno: 1, una: 1, due: 2, tre: 3, quattro: 4, cinque: 5, sei: 6, sette: 7, otto: 8, nove: 9, dieci: 10, undici: 11, dodici: 12, quattordici: 14, quindici: 15, venti: 20, trenta: 30, quaranta: 40, cinquanta: 50, sessanta: 60, novanta: 90, cento: 100, primo: 1, prima: 1, secondo: 2, seconda: 2, terzo: 3, terza: 3, quarto: 4, quinto: 5, quinti: 5, sesto: 6, decimo: 10 },
};

const FEDLEX = window.FEDLEX_DATA || null;

const S = {
  rows: new Map(),
  order: [],
  cores: [],
  coreById: new Map(),
  files: [],
  sample: [],
  log: [],
  edits: {},
  handwritten: [],
  labels: {},
  time: {},
  agentSeen: {},
  settings: { annotator: 'niklas', autoAdvance: true, hwPrefix: 'hw', showFullArticle: false },
  ui: {
    mode: 'review',
    current: null,
    filters: { act: '', lang: '', gen: '', status: '', decision: '', qtype: '', block: '', prio: '', onlyOpen: false, onlyWarn: false, q: '' },
    panel: null,
    reject: { code: '', text: '' },
    note: '',
    blindIdx: 0,
    uncertain: false,
    hwEdit: null,
  },
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const clone = (x) => (x === undefined ? undefined : JSON.parse(JSON.stringify(x)));
const same = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);

function getPath(obj, path) {
  let cur = obj;
  for (const p of path.split('.')) {
    if (cur == null || typeof cur !== 'object') return undefined;
    cur = cur[p];
  }
  return cur;
}
function setPath(obj, path, value) {
  const parts = path.split('.');
  let cur = obj;
  for (const p of parts.slice(0, -1)) {
    if (cur[p] == null || typeof cur[p] !== 'object') cur[p] = {};
    cur = cur[p];
  }
  cur[parts.at(-1)] = value;
}
function pathOf(row, key) {
  const paths = FIELD_MAP[key];
  return paths.find((p) => getPath(row, p) !== undefined) || paths[0];
}
function rawGet(row, key) {
  for (const p of FIELD_MAP[key]) {
    const v = getPath(row, p);
    if (v !== undefined) return v;
  }
  return undefined;
}
function eff(row) {
  const id = rawGet(row, 'id');
  const e = S.edits[coreIdOf(row)]?.[id];
  if (!e) return row;
  const r = clone(row);
  for (const [p, v] of Object.entries(e)) setPath(r, p, v);
  return r;
}
const F = (row, key) => rawGet(eff(row), key);
const langOf = (row) => String(rawGet(row, 'lang') || '').slice(0, 2).toLowerCase() || (String(rawGet(row, 'id')).match(/-(de|fr|it)$/) || [])[1] || 'de';
function coreIdOf(row) {
  return rawGet(row, 'core') || String(rawGet(row, 'id') || '').replace(/-(de|fr|it)$/, '');
}
const asList = (v) => (Array.isArray(v) ? v : v == null || v === '' ? [] : [v]);

function nowIso() {
  const d = new Date();
  const off = -d.getTimezoneOffset();
  const pad = (n) => String(Math.floor(Math.abs(n))).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}${off >= 0 ? '+' : '-'}${pad(off / 60)}:${pad(off % 60)}`;
}
const today = () => nowIso().slice(0, 10);

/* ---------- persistence ---------- */

let storageOk = true;
function save() {
  try {
    localStorage.setItem(
      STORE_KEY,
      JSON.stringify({
        log: S.log,
        edits: S.edits,
        handwritten: S.handwritten,
        labels: S.labels,
        time: S.time,
        agentSeen: S.agentSeen,
        settings: S.settings,
        filters: S.ui.filters,
        current: S.ui.current,
        mode: S.ui.mode,
        blindIdx: S.ui.blindIdx,
      }),
    );
    storageOk = true;
  } catch (e) {
    if (storageOk) notice('Browser-Speicher nicht verfügbar – bitte regelmäßig exportieren.', 'warn');
    storageOk = false;
  }
}
function saveData() {
  try {
    localStorage.setItem(DATA_KEY, JSON.stringify({ files: S.files, rows: [...S.rows.values()], sample: S.sample }));
  } catch (e) {
    try { localStorage.removeItem(DATA_KEY); } catch (_) { /* ignore */ }
  }
}
function load() {
  try {
    const st = JSON.parse(localStorage.getItem(STORE_KEY) || 'null');
    if (st) {
      S.log = st.log || [];
      S.edits = st.edits || {};
      S.handwritten = st.handwritten || [];
      S.labels = st.labels || {};
      S.time = st.time || {};
      S.agentSeen = st.agentSeen || {};
      Object.assign(S.settings, st.settings || {});
      Object.assign(S.ui.filters, st.filters || {});
      S.ui.current = st.current || null;
      S.ui.mode = st.mode || 'review';
      S.ui.blindIdx = st.blindIdx || 0;
    }
    const d = JSON.parse(localStorage.getItem(DATA_KEY) || 'null');
    if (d && d.rows) {
      S.files = d.files || [];
      for (const r of d.rows) S.rows.set(rawGet(r, 'id'), r);
      S.sample = d.sample || [];
      rebuild();
    }
  } catch (e) {
    notice('Gespeicherter Stand konnte nicht gelesen werden.', 'warn');
  }
  try {
    const th = localStorage.getItem('inkraft-theme');
    if (th) document.documentElement.dataset.theme = th;
  } catch (_) { /* ignore */ }
}

/* ---------- file loading ---------- */

function parseJsonl(text, name) {
  const t = text.trim();
  if (t.startsWith('{') && !t.includes('\n{')) {
    try { return { rows: [JSON.parse(t)], errors: [] }; } catch (_) { /* fall through */ }
  }
  const rows = [];
  const errors = [];
  text.split(/\r?\n/).forEach((line, i) => {
    if (!line.trim()) return;
    try { rows.push(JSON.parse(line)); } catch (e) { errors.push(`${name}:${i + 1}`); }
  });
  return { rows, errors };
}

const JUDGE_KEYS = ['grade', 'incorrect_subtype', 'judge_model', 'judge', 'judgement', 'judge_grade', 'rationale', 'pregrade'];

function classify(rows) {
  const r = rows[0] || {};
  if (r.decisions && Array.isArray(r.decisions)) return 'decisions';
  if ('decision' in r && ('core_id' in r || 'item_id' in r)) return 'log';
  if ('human_grade' in r) return 'labels';
  if ('response' in r && 'id' in r) return 'responses';
  if ('grade' in r && 'examinee' in r) return 'judgements';
  if (!('id' in r) && r.de && r.act) return 'handwritten';
  if ('id' in r) return 'items';
  return 'unknown';
}

async function loadFiles(fileList) {
  const msgs = [];
  for (const file of fileList) {
    const text = await file.text();
    const { rows, errors } = parseJsonl(text, file.name);
    if (errors.length) msgs.push(`${file.name}: ${errors.length} unlesbare Zeilen (${errors.slice(0, 3).join(', ')})`);
    const kind = classify(rows);
    if (kind === 'items') {
      let added = 0;
      for (const r of rows) {
        const id = rawGet(r, 'id');
        if (!id) continue;
        const prev = S.rows.get(id);
        S.rows.set(id, prev ? { ...prev, ...r } : r);
        if (!prev) added++;
      }
      S.files = [...new Set([...S.files, file.name])];
      msgs.push(`${file.name}: ${rows.length} Zeilen (${added} neu)`);
    } else if (kind === 'log') {
      msgs.push(`${file.name}: ${importLog(rows)}`);
    } else if (kind === 'labels') {
      let n = 0;
      for (const r of rows) {
        S.labels[labelKey(r)] = r;
        n++;
      }
      msgs.push(`${file.name}: ${n} Blind-Labels übernommen`);
    } else if (kind === 'responses') {
      let hidden = 0;
      const clean = rows.map((r) => {
        const c = { ...r };
        for (const k of JUDGE_KEYS) if (k in c) { delete c[k]; hidden++; }
        return c;
      });
      const have = new Set(S.sample.map(labelKey));
      for (const r of clean) if (!have.has(labelKey(r))) S.sample.push(r);
      msgs.push(`${file.name}: ${clean.length} Antworten für die Blind-Stichprobe${hidden ? ` (Judge-Felder ausgeblendet)` : ''}`);
    } else if (kind === 'judgements') {
      msgs.push(`${file.name}: Judge-Urteile werden bewusst nicht geladen (Blindprüfung).`);
    } else if (kind === 'handwritten') {
      let n = 0;
      for (const r of rows) {
        const id = r._id || nextHwId();
        if (!S.handwritten.some((h) => h._id === id)) {
          S.handwritten.push({ ...r, _id: id });
          n++;
        }
      }
      msgs.push(`${file.name}: ${n} handgeschriebene Kerne übernommen`);
    } else if (kind === 'decisions') {
      msgs.push(`${file.name}: review_decisions.json ist ein Exportformat – bitte review_log.jsonl importieren.`);
    } else {
      msgs.push(`${file.name}: Format nicht erkannt`);
    }
  }
  rebuild();
  saveData();
  save();
  notice(msgs.join(' · '), msgs.some((m) => /unlesbar|nicht erkannt/.test(m)) ? 'warn' : '');
  render();
}

function importLog(rows) {
  const have = new Set(S.log.map((e) => `${e.core_id}|${e.timestamp}|${e.decision}`));
  let n = 0;
  let remapped = 0;
  let unknown = 0;
  for (const e of rows) {
    const ev = { ...e, core_id: e.core_id || e.item_id };
    if (S.cores.length && !S.coreById.has(ev.core_id) && ev.fingerprint) {
      const hit = S.cores.find((c) => fingerprint(c).question_de === ev.fingerprint.question_de && fingerprint(c).article_id === ev.fingerprint.article_id);
      if (hit) {
        ev.previous_core_id = ev.core_id;
        ev.core_id = hit.id;
        ev.item_id = hit.id;
        remapped++;
      } else unknown++;
    }
    const k = `${ev.core_id}|${ev.timestamp}|${ev.decision}`;
    if (have.has(k)) continue;
    have.add(k);
    S.log.push(ev);
    if (ev.duration_s && !S.time[ev.core_id]) S.time[ev.core_id] = ev.duration_s * 1000;
    n++;
  }
  S.log.sort((a, b) => String(a.timestamp).localeCompare(String(b.timestamp)));
  return `${n} Protokolleinträge übernommen${remapped ? `, ${remapped} über Fingerabdruck neuen IDs zugeordnet` : ''}${unknown ? `, ${unknown} ohne passenden Kern` : ''}`;
}

function rebuild() {
  const byCore = new Map();
  S.order = [...S.rows.keys()].sort();
  for (const id of S.order) {
    const r = S.rows.get(id);
    const cid = coreIdOf(r);
    if (!byCore.has(cid)) byCore.set(cid, { id: cid, rows: {} });
    byCore.get(cid).rows[langOf(r)] = r;
  }
  const rank = (c) => {
    const r = hintOf(c)?.rank;
    return typeof r === 'number' && Number.isFinite(r) ? r : Infinity;
  };
  S.cores = [...byCore.values()].sort((a, b) => rank(a) - rank(b) || a.id.localeCompare(b.id, 'de', { numeric: true }));
  S.coreById = new Map(S.cores.map((c) => [c.id, c]));
  checkCache.clear();
  if (!S.coreById.has(S.ui.current)) S.ui.current = S.cores[0]?.id || null;
}

const primary = (core) => core.rows.de || core.rows[Object.keys(core.rows)[0]];
const coreLangs = (core) => LANGS.filter((l) => core.rows[l]).concat(Object.keys(core.rows).filter((l) => !LANGS.includes(l)));

/* ---------- review package ---------- */

const PRIOS = ['hoch', 'mittel', 'niedrig'];
const CANDIDATE_RE = /^(nmu|nmv|nms)-/;

function hintOf(core) {
  for (const l of coreLangs(core)) {
    const h = core.rows[l]?.review_hint;
    if (h && typeof h === 'object') return h;
  }
  return null;
}
const hasHints = () => S.cores.some(hintOf);
const blockOf = (core) => hintOf(core)?.block ?? null;
function blockLabels() {
  const out = new Map();
  for (const c of S.cores) {
    const h = hintOf(c);
    if (h?.block != null && !out.has(String(h.block))) out.set(String(h.block), h.block_label || '');
  }
  return new Map([...out].sort((a, b) => a[0].localeCompare(b[0], 'de', { numeric: true })));
}
function blockStats() {
  const out = new Map();
  for (const c of S.cores) {
    const h = hintOf(c);
    if (!h) continue;
    const k = h.block == null ? '–' : String(h.block);
    const s = out.get(k) || { label: h.block_label || '', total: 0, done: 0, restMin: 0 };
    s.total++;
    if (isFinal(decisionOf(c.id))) s.done++;
    else s.restMin += Number(h.est_minutes) || 0;
    out.set(k, s);
  }
  return new Map([...out].sort((a, b) => a[0].localeCompare(b[0], 'de', { numeric: true })));
}

// Maps a proposal path onto the dataset path the editor uses for the same field, so edits, diffs and export agree.
function editPathFor(row, path) {
  for (const def of EDITABLE) if (FIELD_MAP[def.key].includes(path)) return pathOf(row, def.key);
  return path;
}
const editableKeyOf = (row, path) => EDITABLE.find((def) => pathOf(row, def.key) === path)?.key || null;

// Returns [{lang, itemId, path, old, new}] for every proposed field that differs from the loaded row.
function proposalChanges(core) {
  const p = hintOf(core)?.proposal;
  if (!p) return [];
  const out = [];
  const seen = new Map();
  const add = (l, fields) => {
    const row = core.rows[l];
    if (!row || !fields || typeof fields !== 'object') return;
    for (const [rawPath, val] of Object.entries(fields)) {
      const path = editPathFor(row, rawPath);
      seen.set(`${l}|${path}`, { lang: l, itemId: rawGet(row, 'id'), path, old: getPath(row, path) ?? null, new: val });
    }
  };
  for (const l of coreLangs(core)) add(l, p.all);
  for (const l of coreLangs(core)) add(l, p[l]);
  for (const c of seen.values()) if (!same(c.old, c.new)) out.push(c);
  return out;
}
const missingProposalLangs = (core) => {
  const p = hintOf(core)?.proposal;
  return p ? LANGS.filter((l) => p[l] && !core.rows[l]) : [];
};

function applyProposal() {
  const core = S.coreById.get(S.ui.current);
  const h = core && hintOf(core);
  const p = h?.proposal;
  if (!p) return notice('Für diesen Kern gibt es keinen Vorschlag.', 'warn');
  if (p.action === 'drop') {
    S.ui.panel = 'reject';
    S.ui.reject = { code: 'other', text: p.summary || '' };
    render();
    $('#rjText')?.focus();
    return;
  }
  const changes = proposalChanges(core);
  if (!changes.length) return notice('Der Vorschlag ändert nichts gegenüber dem geladenen Datensatz.', 'warn');
  S.edits[core.id] = S.edits[core.id] || {};
  for (const c of changes) (S.edits[core.id][c.itemId] = S.edits[core.id][c.itemId] || {})[c.path] = clone(c.new);
  if (p.summary && !S.ui.note.trim()) S.ui.note = p.summary;
  S.ui.panel = 'correct';
  save();
  render();
  const miss = missingProposalLangs(core);
  notice(`Vorschlag übernommen: ${changes.length} Feld(er). Bitte prüfen, ggf. weiter bearbeiten und mit Begründung speichern.${miss.length ? ` Sprache(n) ${miss.join(', ')} fehlen im Datensatz und wurden übersprungen.` : ''}`, miss.length ? 'warn' : '');
  $('#corrReason')?.focus();
}

function fingerprint(core) {
  const p = primary(core);
  return { act: rawGet(p, 'act'), article_id: rawGet(p, 'article'), paragraph: rawGet(p, 'paragraph'), question_de: rawGet(core.rows.de || p, 'question') };
}

/* ---------- decisions ---------- */

function decisionOf(coreId) {
  for (let i = S.log.length - 1; i >= 0; i--) {
    const e = S.log[i];
    if (e.core_id === coreId) return e.decision === 'reset' ? null : e;
  }
  return null;
}
const isFinal = (d) => d && d.decision !== 'later';

function collectChanges(core) {
  const out = [];
  const edits = S.edits[core.id] || {};
  for (const [itemId, fields] of Object.entries(edits)) {
    const row = S.rows.get(itemId);
    if (!row) continue;
    for (const [path, val] of Object.entries(fields)) {
      const old = getPath(row, path);
      if (!same(old, val)) out.push({ item_id: itemId, field: path, old: old ?? null, new: val });
    }
  }
  return out;
}

function decide(decision, extra = {}) {
  const core = S.coreById.get(S.ui.current);
  if (!core) return;
  const checks = coreChecks(core);
  const ev = {
    item_id: core.id,
    core_id: core.id,
    item_ids: coreLangs(core).map((l) => rawGet(core.rows[l], 'id')),
    decision,
    reason_code: extra.reason_code ?? null,
    reason: extra.reason ?? (S.ui.note.trim() || null),
    changes: decision === 'correct' ? collectChanges(core) : [],
    checks: { errors: checks.filter((c) => c.level === 'err').length, warnings: checks.filter((c) => c.level === 'warn').length },
    reviewer: REVIEWER,
    timestamp: nowIso(),
    duration_s: Math.round((S.time[core.id] || 0) / 1000),
    fingerprint: fingerprint(core),
    agent_revealed_before_decision: !!S.agentSeen[core.id],
    tool: TOOL,
  };
  if (blockOf(core) != null) ev.block = blockOf(core);
  if (decision !== 'correct' && decision !== 'reset') delete S.edits[core.id];
  S.log.push(ev);
  S.ui.panel = null;
  S.ui.note = '';
  S.ui.reject = { code: '', text: '' };
  save();
  if (S.settings.autoAdvance && decision !== 'reset') gotoNextOpen(true);
  else render();
}

function undoDecision() {
  const core = S.coreById.get(S.ui.current);
  if (!core || !decisionOf(core.id)) return;
  decide('reset', { reason: 'Entscheidung zurückgenommen' });
  notice(`Entscheidung für ${core.id} zurückgenommen (bleibt im Protokoll sichtbar).`);
}

/* ---------- checks ---------- */

function normIdx(s) {
  const map = [];
  let out = '';
  let prevSpace = true;
  const src = String(s ?? '').normalize('NFC');
  for (let i = 0; i < src.length; i++) {
    let c = src[i];
    if (/[\s   ​]/.test(c)) {
      if (prevSpace) continue;
      c = ' ';
      prevSpace = true;
    } else {
      prevSpace = false;
      if (/[’‘‛`´']/.test(c)) c = "'";
      else if (/[“”„«»"]/.test(c)) c = '"';
      else if (/[–—‑]/.test(c)) c = '-';
    }
    out += c;
    map.push(i);
  }
  while (out.endsWith(' ')) { out = out.slice(0, -1); map.pop(); }
  return { n: out, map };
}
const norm = (s) => normIdx(s).n;

function findSpan(hay, needle) {
  if (!needle || !hay) return null;
  const exact = hay.indexOf(needle);
  if (exact >= 0) return { start: exact, end: exact + needle.length, exact: true };
  const h = normIdx(hay);
  const n = norm(needle);
  if (!n) return null;
  let i = h.n.indexOf(n);
  let ci = false;
  if (i < 0) {
    i = h.n.toLowerCase().indexOf(n.toLowerCase());
    ci = i >= 0;
  }
  if (i < 0) return null;
  return { start: h.map[i], end: h.map[i + n.length - 1] + 1, exact: false, caseInsensitive: ci };
}

const ARTICLES = new Set(['ein', 'eine', 'einen', 'einem', 'einer', 'eines', 'un', 'une', 'una', 'uno']);
function numbers(s, lang, skipArticles = false) {
  const out = new Set();
  if (!s) return out;
  let t = String(s).replace(/\b(per|pour)\s+cent[oi]?\b/gi, '%');
  for (let k = 0; k < 3; k++) t = t.replace(/(\d)['’   ](?=\d{3}(?!\d))/g, '$1');
  for (const m of t.matchAll(/\d+(?:[.,]\d+)?/g)) out.add(parseFloat(m[0].replace(',', '.')));
  const words = NUM_WORDS[lang] || {};
  for (const w of t.toLowerCase().match(/[a-zàâçéèêëîïôûùüÿäöß]+/g) || []) if (w in words && !(skipArticles && ARTICLES.has(w))) out.add(words[w]);
  return out;
}
const digitNumbers = (s) => {
  const out = new Set();
  let t = String(s ?? '');
  for (let k = 0; k < 3; k++) t = t.replace(/(\d)['’   ](?=\d{3}(?!\d))/g, '$1');
  for (const m of t.matchAll(/\d+(?:[.,]\d+)?/g)) out.add(parseFloat(m[0].replace(',', '.')));
  return out;
};

function lawArticle(act, versionDate, lang, articleId) {
  if (!FEDLEX) return { status: 'nobundle' };
  const a = FEDLEX.acts[act];
  if (!a) return { status: 'noact' };
  const v = a.versions[versionDate];
  if (!v) return { status: 'noversion', current: Object.entries(a.versions).find(([, x]) => x.role === 'current')?.[0] };
  const arts = v.langs[lang];
  if (!arts) return { status: 'nolang' };
  const art = arts[articleId];
  if (!art) return { status: 'noarticle', role: v.role };
  return { status: 'ok', art, role: v.role, act: a };
}
const articleText = (art) => (art.p.length ? art.p.map(([n, t]) => (n ? `${n} ${t}` : t)).join('\n') : art.t || '');
const paraText = (art, p) => {
  const hit = art.p.find(([n]) => n === (p || ''));
  return hit ? hit[1] : null;
};
const currentVersionOf = (act) => {
  const a = FEDLEX?.acts[act];
  return a ? Object.entries(a.versions).find(([, x]) => x.role === 'current')?.[0] : null;
};

const checkCache = new Map();
function rowChecks(row) {
  const key = rawGet(row, 'id') + '|' + JSON.stringify(S.edits[coreIdOf(row)]?.[rawGet(row, 'id')] || null);
  if (checkCache.has(key)) return checkCache.get(key);
  const out = [];
  const add = (level, code, msg) => out.push({ level, code, msg });
  const lang = langOf(row);
  const act = F(row, 'act');
  const ver = F(row, 'versionDate');
  const artId = F(row, 'article');
  const para = F(row, 'paragraph');
  const quote = F(row, 'quote');
  const evidence = F(row, 'evidence');
  const answer = F(row, 'answer');
  const qtype = F(row, 'qtype');

  for (const k of ['question', 'answer', 'quote', 'evidence', 'act', 'article', 'versionDate']) {
    const v = F(row, k);
    if (v == null || v === '') add('err', 'missing', `Feld fehlt: ${FIELD_MAP[k][0]}`);
  }

  const law = lawArticle(act, ver, lang, artId);
  const cur = currentVersionOf(act);
  if (cur && ver && cur !== ver) add('warn', 'version', `Fassung ${ver} ≠ am Stichtag geltende ${cur}`);
  if (law.status === 'ok') {
    const pt = paraText(law.art, para);
    const full = articleText(law.art);
    if (quote) {
      if (pt != null && pt === quote) add('ok', 'quote', 'Zitat = Absatz wörtlich');
      else if (pt != null && norm(pt) === norm(quote)) add('warn', 'quote', 'Zitat = Absatz nur nach Normalisierung (Leerzeichen/Apostroph)');
      else if (findSpan(pt || '', quote)) add('ok', 'quote', 'Zitat wörtlich im Absatz enthalten');
      else if (findSpan(full, quote)?.exact === true || findSpan(full, quote)) add('warn', 'quote', `Zitat im Artikel, aber nicht in Abs. ${para || '–'}`);
      else add('err', 'quote', 'Zitat nicht im Artikel gefunden');
    }
    if (pt == null && law.art.p.length && para) add('err', 'paragraph', `Abs. ${para} existiert in dieser Fassung nicht`);
  } else if (law.status === 'nobundle') add('info', 'law', 'Gesetzestexte nicht lokal (build_fedlex.py)');
  else if (law.status === 'noversion') add('info', 'law', `Fassung ${ver} nicht im lokalen Paket`);
  else if (law.status === 'noarticle') add('err', 'law', `Artikel ${artId} nicht in ${act} ${ver}`);
  else if (law.status === 'noact') add('info', 'law', `${act} nicht im lokalen Paket`);

  if (evidence && quote) {
    const sp = findSpan(quote, evidence);
    if (!sp) add('err', 'evidence', 'Evidenz nicht im Zitat');
    else if (!sp.exact) add('warn', 'evidence', 'Evidenz nur nach Normalisierung im Zitat');
    else add('ok', 'evidence', 'Evidenz wörtlich im Zitat');
  }

  const ansNums = numbers(qtype === 'false_premise' ? F(row, 'answerCore') : answer, lang, true);
  if (ansNums.size && qtype !== 'calc') {
    const evN = numbers(evidence, lang);
    const qN = numbers(quote, lang);
    const inEv = [...ansNums].some((n) => evN.has(n));
    const inQ = [...ansNums].some((n) => qN.has(n));
    if (inEv) add('ok', 'number', 'Zahl der Antwort in der Evidenz');
    else if (inQ) add('warn', 'number', 'Zahl der Antwort nur im Zitat, nicht in der Evidenz');
    else add('warn', 'number', `Zahl der Antwort (${[...ansNums].join(', ')}) nicht im Zitat – Zahlwort/Umrechnung prüfen`);
  }
  const an = F(row, 'answerNorm');
  if (an && typeof an === 'object' && an.value != null && ansNums.size && !ansNums.has(Number(an.value)) && qtype !== 'calc' && an.unit !== 'percent')
    add('info', 'norm', `answer_normalized ${an.value} ${an.unit || ''} nicht wörtlich in der Antwort`);

  if (qtype === 'calc') {
    const calc = F(row, 'calc');
    if (calc?.formula && an?.value != null) {
      const res = evalFormula(calc.formula);
      if (res == null) add('warn', 'calc', 'Formel nicht auswertbar');
      else if (Math.abs(res - Number(an.value)) < 0.01) add('ok', 'calc', `Formel ergibt ${res}`);
      else add('err', 'calc', `Formel ergibt ${res}, Gold ${an.value}`);
    }
    for (const ce of asList(F(row, 'calcEvidence'))) {
      const inputs = asList(calc?.inputs);
      const found = inputs.some((inp) => {
        const l = lawArticle(inp.act, currentVersionOf(inp.act), lang, inp.article_id);
        return l.status === 'ok' && findSpan(articleText(l.art), ce);
      }) || (quote && findSpan(quote, ce));
      if (!found && FEDLEX) add('warn', 'calc_ev', `Rechen-Evidenz nicht gefunden: „${String(ce).slice(0, 40)}…“`);
    }
  }

  const aliases = asList(F(row, 'aliases')).map(norm);
  const outdated = asList(F(row, 'outdated')).map(norm);
  const near = asList(F(row, 'nearMiss')).map(norm);
  const golds = [norm(answer), ...aliases];
  if (outdated.some((o) => golds.includes(o))) add('err', 'outdated', 'Veraltete Antwort = Gold/Variante');
  if (near.some((o) => golds.includes(o))) add('err', 'near', 'Near-Miss = Gold/Variante');
  if (near.some((o) => outdated.includes(o))) add('warn', 'near', 'Near-Miss = veraltete Antwort');
  if (qtype === 'temporal' && !outdated.length) add('warn', 'outdated', 'temporal ohne veraltete Antwort');

  const prevQuote = F(row, 'prevQuote');
  const prevEv = F(row, 'prevEvidence');
  if (prevQuote || prevEv) {
    const pv = F(row, 'prevVersion');
    const pl = lawArticle(act, pv, lang, artId);
    if (pl.status === 'ok' && prevQuote) {
      if (findSpan(articleText(pl.art), prevQuote)) add('ok', 'prev', `Vorfassung ${pv}: Zitat gefunden`);
      else add('err', 'prev', `Vorfassung ${pv}: Zitat nicht gefunden`);
    }
    if (prevEv && prevQuote && !findSpan(prevQuote, prevEv)) add('err', 'prev_ev', 'Evidenz der Vorfassung nicht im Vorfassungs-Zitat');
    const oldNums = new Set(asList(F(row, 'outdated')).flatMap((o) => [...numbers(o, lang)]));
    if (oldNums.size && prevEv && ![...oldNums].some((n) => numbers(prevEv, lang).has(n))) add('warn', 'prev_ev', 'Zahl der veralteten Antwort nicht in Evidenz der Vorfassung');
  }

  const q = F(row, 'question') || '';
  if (/\b(Art\.|Artikel|article|articolo)\s*\d/i.test(q)) add('warn', 'style', 'Frage nennt eine Artikelnummer');
  const fut = asList(F(row, 'futureChange'));
  if (fut.length) add('warn', 'future', `Änderung nach Stichtag publiziert: ${fut.join(', ')}`);
  checkCache.set(key, out);
  return out;
}

function evalFormula(f) {
  const s = String(f).replace(/[’']/g, '');
  if (!/^[\d\s+\-*/().,%]+$/.test(s)) return null;
  try {
    const v = Function(`"use strict";return (${s.replace(/,/g, '.')});`)();
    return Number.isFinite(v) ? Math.round(v * 100) / 100 : null;
  } catch (_) {
    return null;
  }
}

function crossChecks(core) {
  const out = [];
  const add = (level, code, msg) => out.push({ level, code, msg, lang: 'alle' });
  const langs = coreLangs(core);
  const missing = LANGS.filter((l) => !core.rows[l]);
  if (missing.length) add('warn', 'langs', `Sprache fehlt: ${missing.join(', ')}`);
  else add('ok', 'langs', 'DE/FR/IT vorhanden');
  if (langs.length < 2) return out;
  const rows = langs.map((l) => core.rows[l]);
  for (const k of ['act', 'article', 'paragraph', 'versionDate', 'qtype', 'answerType']) {
    const vals = new Set(rows.map((r) => JSON.stringify(F(r, k) ?? null)));
    if (vals.size > 1) add('warn', 'consistent', `${FIELD_MAP[k][0]} unterscheidet sich zwischen den Sprachen`);
  }
  const norms = new Set(rows.map((r) => JSON.stringify(F(r, 'answerNorm') ?? null)));
  if (norms.size > 1) add('err', 'consistent', 'answer_normalized unterscheidet sich zwischen den Sprachen');
  const qt = F(primary(core), 'qtype');
  const numSets = qt === 'false_premise' ? [] : langs.map((l) => [...numbers(F(core.rows[l], 'answer'), l, true)].sort((a, b) => a - b).join(', '));
  if (new Set(numSets).size > 1) add('warn', 'consistent', `Zahlen der Antworten verschieden (${langs.map((l, i) => `${l}: ${numSets[i] || '–'}`).join('; ')})`);
  else if (numSets[0]) add('ok', 'consistent', 'Antwortzahl in allen Sprachen gleich');
  const yn = langs.map((l) => {
    const a = norm(F(core.rows[l], 'answer')).toLowerCase();
    if (/^(ja|oui|sì|si)(?![a-zà-ÿ])/.test(a)) return 'yes';
    if (/^(nein|non|no)(?![a-zà-ÿ])/.test(a)) return 'no';
    return null;
  });
  if (qt === 'yes_no' && new Set(yn).size > 1) add('err', 'consistent', `Ja/Nein verschieden: ${langs.map((l, i) => `${l}=${yn[i] || '?'}`).join(', ')}`);
  const counts = (k) => new Set(rows.map((r) => asList(F(r, k)).length)).size > 1;
  if (counts('outdated')) add('warn', 'consistent', 'Anzahl veralteter Antworten unterscheidet sich');
  return out;
}

function coreChecks(core) {
  const all = [];
  for (const l of coreLangs(core)) for (const c of rowChecks(core.rows[l])) all.push({ ...c, lang: l });
  return all.concat(crossChecks(core));
}
const problemCount = (core) => coreChecks(core).filter((c) => c.level === 'err' || c.level === 'warn').length;

/* ---------- diff ---------- */

function diffHtml(a, b) {
  const ta = String(a ?? '').split(/(\s+)/);
  const tb = String(b ?? '').split(/(\s+)/);
  if (ta.length * tb.length > 250000) return `<del>${esc(a)}</del> <ins>${esc(b)}</ins>`;
  const m = ta.length;
  const n = tb.length;
  const dp = Array.from({ length: m + 1 }, () => new Uint16Array(n + 1));
  for (let i = m - 1; i >= 0; i--) for (let j = n - 1; j >= 0; j--) dp[i][j] = ta[i] === tb[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  let i = 0;
  let j = 0;
  let html = '';
  while (i < m && j < n) {
    if (ta[i] === tb[j]) { html += esc(ta[i]); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) { html += `<del>${esc(ta[i])}</del>`; i++; }
    else { html += `<ins>${esc(tb[j])}</ins>`; j++; }
  }
  while (i < m) html += `<del>${esc(ta[i++])}</del>`;
  while (j < n) html += `<ins>${esc(tb[j++])}</ins>`;
  return html;
}
const listText = (v) => asList(v).join('\n');

/* ---------- filters ---------- */

function filteredCores() {
  const f = S.ui.filters;
  const q = f.q.trim().toLowerCase();
  const hints = (f.block || f.prio) && hasHints();
  return S.cores.filter((c) => {
    const p = primary(c);
    if (f.act && rawGet(p, 'act') !== f.act) return false;
    if (f.lang && !c.rows[f.lang]) return false;
    if (f.gen && genOf(p) !== f.gen) return false;
    if (f.status && String(rawGet(p, 'status')) !== f.status) return false;
    if (f.qtype && rawGet(p, 'qtype') !== f.qtype) return false;
    if (hints && f.block && String(blockOf(c) ?? '') !== f.block) return false;
    if (hints && f.prio && hintOf(c)?.priority !== f.prio) return false;
    const d = decisionOf(c.id);
    if (f.onlyOpen && isFinal(d)) return false;
    if (f.decision) {
      if (f.decision === 'open' ? isFinal(d) : (d?.decision || 'none') !== f.decision) return false;
    }
    if (f.onlyWarn && !problemCount(c)) return false;
    if (q) {
      const hay = [c.id, ...Object.values(c.rows).flatMap((r) => [rawGet(r, 'id'), F(r, 'question'), F(r, 'answer'), F(r, 'quote'), listText(F(r, 'aliases'))])].join(' ').toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}
const genOf = (row) => String(rawGet(row, 'generator') || rawGet(row, 'generatorModel') || '–');

function gotoNextOpen(after = false) {
  const list = filteredCores();
  const idx = list.findIndex((c) => c.id === S.ui.current);
  const order = after && idx >= 0 ? list.slice(idx + 1).concat(list.slice(0, idx + 1)) : list;
  const next = order.find((c) => !isFinal(decisionOf(c.id)) && c.id !== S.ui.current) || order.find((c) => !isFinal(decisionOf(c.id)));
  if (next) select(next.id);
  else {
    notice('Keine offenen Kerne mehr in dieser Auswahl.');
    render();
  }
}
function move(delta) {
  const list = filteredCores();
  if (!list.length) return;
  const idx = list.findIndex((c) => c.id === S.ui.current);
  const n = list[Math.max(0, Math.min(list.length - 1, (idx < 0 ? 0 : idx) + delta))];
  select(n.id);
}
function select(id) {
  if (S.ui.current !== id) {
    S.ui.panel = null;
    S.ui.note = '';
  }
  S.ui.current = id;
  save();
  render();
  $('.core-list li.current')?.scrollIntoView({ block: 'nearest' });
  $('.scroll')?.scrollTo(0, 0);
}
function jumpTo(raw) {
  const id = raw.trim().replace(/-(de|fr|it)$/, '');
  const hit = S.coreById.get(id) || S.cores.find((c) => c.id.endsWith(id) || Object.values(c.rows).some((r) => rawGet(r, 'id') === raw.trim()));
  if (hit) {
    if (!filteredCores().includes(hit)) {
      Object.assign(S.ui.filters, { act: '', lang: '', gen: '', status: '', decision: '', qtype: '', block: '', prio: '', onlyOpen: false, onlyWarn: false, q: '' });
      notice('Filter zurückgesetzt, damit der Kern sichtbar ist.');
    }
    select(hit.id);
  } else notice(`ID „${raw}“ nicht gefunden.`, 'warn');
}

/* ---------- rendering ---------- */

let noticeTimer = null;
function notice(msg, level = '') {
  const n = $('#notice');
  n.className = `notice ${level}`;
  n.innerHTML = `<span>${esc(msg)}</span><button aria-label="Schließen">×</button>`;
  n.hidden = !msg;
  n.querySelector('button').onclick = () => (n.hidden = true);
  clearTimeout(noticeTimer);
  if (!level) noticeTimer = setTimeout(() => (n.hidden = true), 8000);
}

let rendering = false;
function render() {
  if (rendering) return;
  rendering = true;
  try {
    renderInner();
  } finally {
    rendering = false;
  }
}

function renderInner() {
  const hasData = S.cores.length > 0 || S.ui.mode === 'handwritten' || (S.ui.mode === 'blind' && S.sample.length);
  $('#dropzone').hidden = hasData;
  $('#view').hidden = !hasData;
  $$('.mode').forEach((b) => b.classList.toggle('active', b.dataset.mode === S.ui.mode));
  const nItems = S.rows.size;
  $('#datasetInfo').textContent = nItems ? `${S.cores.length} Kerne · ${nItems} Zeilen · ${S.files.join(', ')}` : 'kein Datensatz geladen';
  $('#fedlexStatus').textContent = FEDLEX ? `Gesetzestexte lokal: ${Object.keys(FEDLEX.acts).length} Erlasse (Stand ${FEDLEX.as_of}).` : 'Gesetzestexte nicht lokal – fedlex_texte.js fehlt (python build_fedlex.py). Prüfung läuft trotzdem, nur ohne Zitatabgleich.';
  renderProgress();
  if (!hasData) return;
  if (S.ui.mode === 'review') renderReview();
  else if (S.ui.mode === 'handwritten') renderHandwritten();
  else renderBlind();
}

function renderProgress() {
  let done = 0;
  let total = 0;
  if (S.ui.mode === 'blind') {
    total = S.sample.length;
    done = S.sample.filter((r) => S.labels[labelKey(r)]).length;
  } else if (S.ui.mode === 'handwritten') {
    total = S.handwritten.length;
    done = total;
  } else {
    total = S.cores.length;
    done = S.cores.filter((c) => isFinal(decisionOf(c.id))).length;
  }
  const pct = total ? (100 * done) / total : 0;
  $('#progressBar').style.width = `${pct}%`;
  let rest = '';
  if (S.ui.mode === 'review' && hasHints()) {
    const min = [...blockStats().values()].reduce((a, s) => a + s.restMin, 0);
    rest = ` · Rest ≈ ${fmtDur(min * 60)}`;
  }
  $('#progressText').textContent = S.ui.mode === 'handwritten' ? `${total} neue Kerne` : `${done} / ${total} (${pct.toFixed(0)} %)${rest}`;
}

function options(values, sel, empty) {
  return `<option value="">${esc(empty)}</option>` + values.map((v) => `<option value="${esc(v)}" ${v === sel ? 'selected' : ''}>${esc(v)}</option>`).join('');
}
const uniq = (arr) => [...new Set(arr.filter((x) => x != null && x !== ''))].sort();

function renderSidebar() {
  const f = S.ui.filters;
  const list = filteredCores();
  const prims = S.cores.map(primary);
  const hints = hasHints();
  const blocks = hints ? blockLabels() : new Map();
  const stats = hints ? blockStats() : new Map();
  const restMin = [...stats.values()].reduce((a, s) => a + s.restMin, 0);
  const pkgFilters = hints
    ? `<select id="fBlock" title="Block im Review-Paket"><option value="">alle Blöcke</option>${[...blocks].map(([b, l]) => `<option value="${esc(b)}" ${b === f.block ? 'selected' : ''}>${esc(b)}${l ? ` – ${esc(l)}` : ''}</option>`).join('')}</select>
      <select id="fPrio" title="Priorität im Review-Paket">${options(PRIOS, f.prio, 'alle Prioritäten')}</select>`
    : '';
  const blockHtml = hints
    ? `<div class="block-progress">${[...stats]
        .map(([b, s]) => `<div title="${esc(s.label)}"><span class="blk">${esc(b)}</span> <span class="lbl">${esc(s.label)}</span> <span class="mono">${s.done}/${s.total}</span></div>`)
        .join('')}<div class="muted">Rest ≈ ${fmtDur(restMin * 60)} (Schätzung)</div></div>`
    : '';
  return `<aside class="sidebar">
    <div class="filters">
      <input type="search" id="fSearch" placeholder="Suche (/) – Frage, Antwort, Zitat, ID" value="${esc(f.q)}">
      ${pkgFilters}
      <select id="fAct" title="Gesetz">${options(uniq(prims.map((r) => rawGet(r, 'act'))), f.act, 'alle Gesetze')}</select>
      <select id="fLang" title="Sprache">${options(LANGS, f.lang, 'alle Sprachen')}</select>
      <select id="fGen" title="Generator">${options(uniq(prims.map(genOf)), f.gen, 'alle Generatoren')}</select>
      <select id="fQtype" title="Fragetyp">${options(uniq(prims.map((r) => rawGet(r, 'qtype'))), f.qtype, 'alle Fragetypen')}</select>
      <select id="fStatus" title="Status im Datensatz">${options(uniq(prims.map((r) => String(rawGet(r, 'status') ?? ''))), f.status, 'alle Status')}</select>
      <select id="fDecision" title="Prüfentscheidung">
        ${[['', 'alle Entscheidungen'], ['open', 'offen (inkl. später)'], ['none', 'unbearbeitet'], ['accept', 'korrekt'], ['correct', 'korrigiert'], ['reject', 'verworfen'], ['later', 'später']].map(([v, l]) => `<option value="${v}" ${v === f.decision ? 'selected' : ''}>${l}</option>`).join('')}
      </select>
      <label class="chk"><input type="checkbox" id="fOpen" ${f.onlyOpen ? 'checked' : ''}> nur offene</label>
      <label class="chk"><input type="checkbox" id="fWarn" ${f.onlyWarn ? 'checked' : ''}> nur mit Warnungen</label>
      <input type="text" class="full" id="fJump" placeholder="Sprung zu ID (G), z. B. cl-0035">
    </div>
    ${blockHtml}
    <div class="list-count">${list.length} von ${S.cores.length} Kernen</div>
    <ul class="core-list" id="coreList">
      ${list
        .map((c) => {
          const d = decisionOf(c.id);
          const pc = problemCount(c);
          const b = blockOf(c);
          return `<li data-core="${esc(c.id)}" class="${c.id === S.ui.current ? 'current' : ''}" title="${esc(F(primary(c), 'question'))}">
            <span class="dot ${d ? d.decision : ''}"></span>
            <span class="q">${b != null ? `<span class="blk">${esc(b)}</span> ` : ''}<span class="id">${esc(c.id)}</span> ${esc(F(primary(c), 'question'))}</span>
            <span class="small ${pc ? 'danger' : 'muted'}">${pc ? `⚠ ${pc}` : ''}</span></li>`;
        })
        .join('')}
    </ul>
  </aside>`;
}

function fieldView(row, def, editing) {
  const val = F(row, def.key);
  const orig = rawGet(row, def.key);
  if (def.optional && (val == null || (Array.isArray(val) && !val.length)) && !editing) return '';
  if (def.collapsed && !editing) return '';
  if (def.key === 'prevEvidence' && !F(row, 'prevQuote') && val == null) return '';
  const changed = !same(val, orig);
  const id = rawGet(row, 'id');
  let body;
  if (editing) {
    const text = def.kind === 'list' ? listText(val) : val ?? '';
    const rows = def.kind === 'line' ? 1 : def.kind === 'list' ? Math.max(2, asList(val).length + 1) : Math.min(8, Math.max(2, Math.ceil(String(text).length / 60)));
    body = `<textarea data-edit="${esc(id)}" data-key="${def.key}" rows="${rows}" spellcheck="false">${esc(text)}</textarea>${def.kind === 'list' ? '<div class="small muted">eine Variante pro Zeile</div>' : ''}`;
  } else if (def.kind === 'list') {
    const l = asList(val);
    body = l.length ? `<ul>${l.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>` : '<span class="muted">–</span>';
  } else body = `<div class="val ${def.cls || ''}">${esc(val ?? '–')}</div>`;
  const diff = changed ? `<div class="diff">${diffHtml(def.kind === 'list' ? listText(orig) : orig, def.kind === 'list' ? listText(val) : val)}</div>` : '';
  return `<div class="field ${changed ? 'changed' : ''}" data-field="${esc(id)}|${def.key}"><div class="lbl">${esc(def.label)}</div>${body}<div class="diff-slot">${diff}</div></div>`;
}

function highlight(text, quote, evidence) {
  const q = findSpan(text, quote);
  const e = findSpan(text, evidence);
  const marks = [];
  if (q) marks.push([q.start, 'o', '<mark>'], [q.end, 'c', '</mark>']);
  if (e) marks.push([e.start, 'o', '<mark class="ev">'], [e.end, 'c', '</mark>']);
  if (q && e && !(e.start >= q.start && e.end <= q.end)) {
    marks.length = 0;
    marks.push([e.start, 'o', '<mark class="ev">'], [e.end, 'c', '</mark>']);
  }
  marks.sort((a, b) => a[0] - b[0] || (a[1] === 'c' ? -1 : 1));
  let out = '';
  let pos = 0;
  for (const [i, , tag] of marks) {
    out += esc(text.slice(pos, i)) + tag;
    pos = i;
  }
  return out + esc(text.slice(pos));
}

function lawView(row, opts = {}) {
  const lang = langOf(row);
  const act = F(row, opts.prev ? 'act' : 'act');
  const ver = opts.prev ? F(row, 'prevVersion') : F(row, 'versionDate');
  const artId = F(row, 'article');
  const para = opts.prev ? F(row, 'prevParagraph') : F(row, 'paragraph');
  const quote = opts.prev ? F(row, 'prevQuote') : F(row, 'quote');
  const evidence = opts.prev ? F(row, 'prevEvidence') : F(row, 'evidence');
  const url = opts.prev ? F(row, 'prevUrl') : F(row, 'articleUrl') || (F(row, 'eliUrl') ? `${F(row, 'eliUrl')}#${artId}` : null);
  const law = lawArticle(act, ver, lang, artId);
  const link = url ? `<a href="${esc(url)}" target="_blank" rel="noopener">Fedlex ${esc(ver || '')} ↗</a>` : '<span class="muted">kein Link</span>';
  let body;
  if (law.status === 'ok') {
    const full = S.settings.showFullArticle || opts.prev;
    const paras = law.art.p.length ? law.art.p : [['', law.art.t]];
    const target = paras.some(([n]) => n === (para || '')) ? para || '' : null;
    body = paras
      .filter(([n]) => full || target == null || n === target)
      .map(([n, t]) => {
        const isT = target != null && n === target;
        const h = isT || target == null ? highlight(t, quote, evidence) : esc(t);
        return `<p class="${isT ? 'target' : full && target != null ? 'dim' : ''}">${n ? `<span class="pn">${esc(n)}</span>` : ''}${h}</p>`;
      })
      .join('');
    if (!full && paras.length > 1) body += `<div class="small muted">${paras.length - 1} weitere Absätze – <kbd>T</kbd> zeigt den ganzen Artikel</div>`;
  } else {
    const why = { nobundle: 'Gesetzestexte nicht lokal', noversion: `Fassung ${ver} nicht lokal`, noarticle: 'Artikel nicht gefunden', noact: 'Erlass nicht lokal', nolang: 'Sprache nicht lokal' }[law.status];
    body = `<p class="muted small">${esc(why)} – Zitat aus dem Datensatz:</p><p>${highlight(quote || '', quote, evidence)}</p>`;
  }
  const head = law.status === 'ok' ? esc(law.art.h || '') : `${esc(act)} ${esc(artId)}`;
  return `<div class="law-head"><strong>${opts.prev ? 'Vorfassung: ' : ''}${head}${para ? ` · Abs. ${esc(para)}` : ''}</strong>${link}</div><div class="law-text" lang="${lang}">${body}</div>`;
}

function checksHtml(list) {
  if (!list.length) return '';
  const order = { err: 0, warn: 1, ok: 2, info: 3 };
  return `<div class="checks">${list
    .slice()
    .sort((a, b) => order[a.level] - order[b.level])
    .map((c) => `<span class="chk-item ${c.level}">${c.level === 'ok' ? '✓' : c.level === 'err' ? '✗' : c.level === 'warn' ? '!' : 'i'} ${esc(c.msg)}</span>`)
    .join('')}</div>`;
}

function renderReview() {
  const view = $('#view');
  const core = S.coreById.get(S.ui.current);
  let main = '<div class="empty">Kein Kern ausgewählt.</div>';
  if (core) {
    const p = primary(core);
    const d = decisionOf(core.id);
    const editing = S.ui.panel === 'correct';
    const langs = coreLangs(core).filter((l) => !S.ui.filters.lang || l === S.ui.filters.lang || l === 'de');
    const temporal = F(p, 'bucket');
    const head = `<div class="core-head">
      <h2>${esc(core.id)}</h2>
      ${CANDIDATE_RE.test(core.id) ? '<span class="tag cand" title="Kandidat aus der Nachgenerierung (nmu-/nmv-/nms-)">Kandidat</span>' : ''}
      <span><strong>${esc(F(p, 'act'))}</strong> Art. ${esc(F(p, 'articleNo') || String(F(p, 'article') || '').replace(/^art_/, ''))}${F(p, 'paragraph') ? ` Abs. ${esc(F(p, 'paragraph'))}` : ''} · Fassung ${esc(F(p, 'versionDate') || '–')}</span>
      <span class="tag">${esc(F(p, 'qtype') || '–')}</span>
      ${F(p, 'domain') ? `<span class="tag">${esc(F(p, 'domain'))}</span>` : ''}
      ${temporal ? `<span class="tag">${esc(temporal)}</span>` : ''}
      <span class="tag" title="${esc(F(p, 'generatorModel') || '')}">${esc(genOf(p))}</span>
      <span class="tag">${esc(F(p, 'status') ?? '–')}${F(p, 'needsReview') ? ' · needs_human_review' : ''}</span>
      ${d ? `<span class="tag ${d.decision}">${DECISION_LABEL[d.decision]}${d.reason ? `: ${esc(d.reason)}` : ''}</span>` : ''}
      <span class="muted small">Zeit: ${fmtDur((S.time[core.id] || 0) / 1000)}</span>
    </div>`;
    const cross = checksHtml(crossChecks(core));
    const calc = F(p, 'calc');
    const calcHtml = calc ? `<div class="card" style="margin-bottom:12px"><h3>Rechnung</h3><code>${esc(calc.formula || '')}</code> = <strong>${esc(F(p, 'answerNorm')?.value ?? '?')}</strong> ${esc(F(p, 'answerNorm')?.unit || '')}<div class="small muted">${asList(calc.inputs).map((i) => `${esc(i.value)} aus ${esc(i.act)} ${esc(i.article_id)} Abs. ${esc(i.paragraph)}`).join(' · ')}</div></div>` : '';
    const prevMc = asList(F(p, 'manualCorrection'));
    const mcHtml = prevMc.length ? `<details class="small" style="margin-bottom:10px"><summary>${prevMc.length} frühere Korrektur(en) im Datensatz</summary>${prevMc.map((m) => `<div class="diff">${esc(m.by || '')}: ${esc(m.reason || JSON.stringify(m))}</div>`).join('')}</details>` : '';
    const cards = langs
      .map((l) => {
        const r = core.rows[l];
        return `<div class="card" lang="${l}">
          <h3><span>${LANG_LABEL[l] || l} <span class="muted mono small">${esc(rawGet(r, 'id'))}</span></span></h3>
          <div id="chk-${esc(rawGet(r, 'id'))}">${checksHtml(rowChecks(r))}</div>
          ${EDITABLE.map((def) => fieldView(r, def, editing)).join('')}
          <div class="law">${lawView(r)}${F(r, 'prevQuote') || F(r, 'prevVersion') ? `<details class="prev-law"><summary>Vorfassung ${esc(F(r, 'prevVersion') || '')} anzeigen</summary>${lawView(r, { prev: true })}</details>` : ''}</div>
        </div>`;
      })
      .join('');
    main = `<div class="scroll">${head}${hintHtml(core)}${proposalHtml(core)}${cross}${mcHtml}${calcHtml}<div class="langs" style="--cols:${langs.length}">${cards}</div></div>${panelHtml(core)}${decisionBar(core)}`;
  }
  view.innerHTML = renderSidebar() + `<section class="content">${main}</section>`;
  if (core && hintOf(core)?.agent_assessment && !S.agentSeen[core.id] && decisionOf(core.id)) {
    S.agentSeen[core.id] = true;
    save();
  }
  bindReview();
}

const VERDICT_LABEL = { accept: 'übernehmen', minor_fix: 'kleine Korrektur', revise: 'überarbeiten', reject: 'verwerfen' };
const VERDICT_CLS = { accept: 'accept', minor_fix: 'correct', revise: 'later', reject: 'reject' };
const valText = (v) => (Array.isArray(v) ? listText(v) : v != null && typeof v === 'object' ? JSON.stringify(v) : v ?? '');

function autoCheckChip(key, val) {
  if (val === true) return `<span class="chk-item ok">✓ ${esc(key)}</span>`;
  if (val === false) return `<span class="chk-item err">✗ ${esc(key)}</span>`;
  if (val == null) return key.endsWith('_of') ? `<span class="chk-item ok">✓ ${esc(key)}: keins</span>` : `<span class="chk-item info">i ${esc(key)}: –</span>`;
  return `<span class="chk-item err">✗ ${esc(key)}: ${esc(valText(val))}</span>`;
}

function hintHtml(core) {
  const h = hintOf(core);
  if (!h) return '';
  const reasons = asList(h.reasons);
  const checks = h.auto_checks && typeof h.auto_checks === 'object' ? Object.entries(h.auto_checks) : [];
  const a = h.agent_assessment;
  let agent = '';
  if (a) {
    const visible = !!decisionOf(core.id) || !!S.agentSeen[core.id];
    agent = visible
      ? `<div class="agent"><span class="lbl">Agenten-Einschätzung</span> <span class="tag ${VERDICT_CLS[a.verdict] || ''}">${esc(VERDICT_LABEL[a.verdict] || a.verdict || '–')}</span> ${esc(a.note || '')}</div>`
      : '<div class="agent"><button class="btn small" id="agentReveal" title="Erst eigenes Urteil bilden. Aufdecken wird im Protokoll vermerkt.">Agenten-Einschätzung aufdecken</button> <span class="muted small">verborgen, bis du entschieden hast</span></div>';
  }
  return `<div class="card hint">
    <h3><span>Review-Paket${h.package ? ` <span class="muted small mono">${esc(h.package)}</span>` : ''}</span><span class="muted small">${h.rank != null ? `Rang ${esc(h.rank)}` : ''}</span></h3>
    <div class="row">
      ${h.block != null ? `<span class="tag"><span class="blk">${esc(h.block)}</span> ${esc(h.block_label || '')}</span>` : ''}
      ${h.priority ? `<span class="tag prio-${esc(h.priority)}">Priorität ${esc(h.priority)}</span>` : ''}
      ${h.est_minutes != null ? `<span class="tag">≈ ${esc(h.est_minutes)} min</span>` : ''}
    </div>
    ${reasons.length ? `<ul class="reasons-list">${reasons.map((r) => `<li>${esc(r)}</li>`).join('')}</ul>` : ''}
    ${checks.length ? `<div class="checks">${checks.map(([k, v]) => autoCheckChip(k, v)).join('')}</div>` : ''}
    ${agent}
  </div>`;
}

function proposalHtml(core) {
  const p = hintOf(core)?.proposal;
  if (!p) return '';
  let body;
  if (p.action === 'drop') {
    body = `<p><span class="tag reject">Kern verwerfen</span> ${esc(p.summary || '')}</p>`;
  } else {
    const ch = proposalChanges(core);
    const byLang = LANGS.concat(coreLangs(core).filter((l) => !LANGS.includes(l)))
      .map((l) => [l, ch.filter((c) => c.lang === l)])
      .filter(([, list]) => list.length);
    body = `${p.summary ? `<p>${esc(p.summary)}</p>` : ''}${
      byLang.length
        ? `<div class="prop-grid">${byLang
            .map(([l, list]) => `<div><div class="lbl">${esc(LANG_LABEL[l] || l)}</div>${list
              .map((c) => {
                const def = EDITABLE.find((d) => d.key === editableKeyOf(core.rows[l], c.path));
                return `<div class="field"><div class="lbl">${esc(def ? def.label : c.path)} <span class="mono">${esc(c.path)}</span></div><div class="diff">${diffHtml(valText(c.old), valText(c.new))}</div></div>`;
              })
              .join('')}</div>`)
            .join('')}</div>`
        : '<p class="muted small">Keine Abweichung zum geladenen Datensatz.</p>'
    }`;
    const miss = missingProposalLangs(core);
    if (miss.length) body += `<p class="small danger">Vorschlag für ${esc(miss.join(', '))}, aber Sprache fehlt im Datensatz.</p>`;
  }
  const btn = p.action === 'drop' ? 'Vorschlag übernehmen: verwerfen' : 'Vorschlag als Korrektur übernehmen';
  return `<div class="card proposal">
    <h3><span>Vorschlag (vom Agenten, nicht geprüft)${p.action ? ` <span class="tag">${esc(p.action)}</span>` : ''}</span>${p.action === 'patch' || p.action === 'drop' ? `<button class="btn small" id="propApply" title="P">${btn} <kbd>P</kbd></button>` : ''}</h3>
    ${body}
  </div>`;
}

function panelHtml(core) {
  if (S.ui.panel === 'correct') {
    const ch = collectChanges(core);
    const hidden = ch.filter((c) => {
      const row = S.rows.get(c.item_id);
      return !row || !editableKeyOf(row, c.field);
    });
    return `<div class="panel-form">
      <div><strong>Korrigieren:</strong> <span id="corrCount">${ch.length ? `${ch.length} Feld(er) geändert` : 'Felder oben bearbeiten'}</span> – Begründung ist Pflicht.</div>
      ${hidden.length ? `<div class="small">Zusätzlich geändert (oben nicht editierbar): ${hidden.map((c) => `<span class="mono">${esc(c.item_id)} ${esc(c.field)}</span>: ${esc(valText(c.old))} → <strong>${esc(valText(c.new))}</strong>`).join(' · ')}</div>` : ''}
      <input type="text" id="corrReason" placeholder="Begründung (z. B. „Evidenz auf wörtlichen Gesetzestext gekürzt“)" value="${esc(S.ui.note)}">
      <div class="row"><button class="btn primary" id="corrSave" ${ch.length ? '' : 'disabled'}>Korrektur speichern (Strg+Enter)</button><button class="btn" id="corrDiscard">Änderungen verwerfen (Esc)</button></div>
    </div>`;
  }
  if (S.ui.panel === 'reject') {
    const r = S.ui.reject;
    return `<div class="panel-form">
      <div><strong>Verwerfen:</strong> Grund wählen (<kbd>1</kbd>–<kbd>9</kbd>), optional ergänzen, mit Strg+Enter bestätigen.</div>
      <div class="reasons">${REJECT_REASONS.map(([code, label], i) => `<label class="${r.code === code ? 'sel' : ''}"><input type="radio" name="rj" value="${code}" hidden ${r.code === code ? 'checked' : ''}><kbd>${i + 1}</kbd> ${esc(label)}</label>`).join('')}</div>
      <input type="text" id="rjText" placeholder="Freitext (bei „Anderer Grund“ Pflicht)" value="${esc(r.text)}">
      <div class="row"><button class="btn primary" id="rjSave">Verwerfen bestätigen (Strg+Enter)</button><button class="btn" id="rjCancel">Abbrechen (Esc)</button></div>
    </div>`;
  }
  return '';
}

function decisionBar(core) {
  const d = decisionOf(core.id);
  return `<div class="decision-bar">
    <button class="btn" id="prevBtn" title="vorheriger Kern (←)">←</button>
    <button class="btn" id="nextBtn" title="nächster Kern (→)">→</button>
    <button class="btn dec accept" data-dec="accept" title="A">✓ korrekt <kbd>A</kbd></button>
    <button class="btn dec correct" data-dec="correct" title="K">✎ korrigieren <kbd>K</kbd></button>
    <button class="btn dec reject" data-dec="reject" title="V">✗ verwerfen <kbd>V</kbd></button>
    <button class="btn dec later" data-dec="later" title="S">? später <kbd>S</kbd></button>
    <input type="text" id="noteInput" placeholder="Notiz zur Entscheidung (optional)" value="${esc(S.ui.panel ? '' : S.ui.note)}" style="flex:1;min-width:160px" ${S.ui.panel ? 'disabled' : ''}>
    ${d ? '<button class="btn" id="undoBtn" title="Strg+Z">zurücknehmen</button>' : ''}
    <label class="small"><input type="checkbox" id="autoAdv" ${S.settings.autoAdvance ? 'checked' : ''}> danach weiter</label>
  </div>`;
}

function bindReview() {
  const f = S.ui.filters;
  const bindF = (id, key, prop = 'value') => {
    const el = $(id);
    if (!el) return;
    el.addEventListener(prop === 'checked' ? 'change' : el.tagName === 'SELECT' ? 'change' : 'input', () => {
      f[key] = el[prop];
      save();
      if (id === '#fSearch') {
        const pos = el.selectionStart;
        render();
        const n = $('#fSearch');
        n.focus();
        n.setSelectionRange(pos, pos);
      } else render();
    });
  };
  bindF('#fSearch', 'q');
  bindF('#fAct', 'act');
  bindF('#fLang', 'lang');
  bindF('#fGen', 'gen');
  bindF('#fQtype', 'qtype');
  bindF('#fStatus', 'status');
  bindF('#fDecision', 'decision');
  bindF('#fBlock', 'block');
  bindF('#fPrio', 'prio');
  bindF('#fOpen', 'onlyOpen', 'checked');
  bindF('#fWarn', 'onlyWarn', 'checked');
  $('#fJump')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') jumpTo(e.target.value);
  });
  $('#coreList')?.addEventListener('click', (e) => {
    const li = e.target.closest('li[data-core]');
    if (li) select(li.dataset.core);
  });
  $('#prevBtn')?.addEventListener('click', () => move(-1));
  $('#nextBtn')?.addEventListener('click', () => move(1));
  $$('[data-dec]').forEach((b) => b.addEventListener('click', () => startDecision(b.dataset.dec)));
  $('#undoBtn')?.addEventListener('click', undoDecision);
  $('#propApply')?.addEventListener('click', applyProposal);
  $('#agentReveal')?.addEventListener('click', () => {
    S.agentSeen[S.ui.current] = true;
    save();
    render();
  });
  $('#autoAdv')?.addEventListener('change', (e) => {
    S.settings.autoAdvance = e.target.checked;
    save();
  });
  $('#noteInput')?.addEventListener('input', (e) => (S.ui.note = e.target.value));
  $$('textarea[data-edit]').forEach((t) => t.addEventListener('input', () => refreshField(t)));
  $('#corrReason')?.addEventListener('input', (e) => (S.ui.note = e.target.value));
  $('#corrSave')?.addEventListener('click', saveCorrection);
  $('#corrDiscard')?.addEventListener('click', discardCorrection);
  $$('input[name="rj"]').forEach((r) =>
    r.addEventListener('change', () => {
      S.ui.reject.code = r.value;
      render();
    }),
  );
  $('#rjText')?.addEventListener('input', (e) => (S.ui.reject.text = e.target.value));
  $('#rjSave')?.addEventListener('click', confirmReject);
  $('#rjCancel')?.addEventListener('click', () => {
    S.ui.panel = null;
    render();
  });
}

function applyEdit(itemId, key, text) {
  const row = S.rows.get(itemId);
  if (!row) return;
  const def = EDITABLE.find((d) => d.key === key);
  const path = pathOf(row, key);
  let val = def.kind === 'list' ? text.split('\n').map((s) => s.trim()).filter(Boolean) : def.kind === 'line' ? text.trim() : text.replace(/\s+$/, '');
  const orig = getPath(row, path);
  const empty = def.kind === 'list' ? !val.length : val === '';
  if (empty && (orig === null || orig === undefined)) val = orig;
  const cid = coreIdOf(row);
  S.edits[cid] = S.edits[cid] || {};
  S.edits[cid][itemId] = S.edits[cid][itemId] || {};
  if (same(orig, val)) delete S.edits[cid][itemId][path];
  else S.edits[cid][itemId][path] = val;
  if (!Object.keys(S.edits[cid][itemId]).length) delete S.edits[cid][itemId];
  if (!Object.keys(S.edits[cid]).length) delete S.edits[cid];
  save();
}

function refreshField(t) {
  const itemId = t.dataset.edit;
  const key = t.dataset.key;
  applyEdit(itemId, key, t.value);
  const row = S.rows.get(itemId);
  const def = EDITABLE.find((d) => d.key === key);
  const box = t.closest('.field');
  const val = F(row, key);
  const orig = rawGet(row, key);
  const changed = !same(val, orig);
  box.classList.toggle('changed', changed);
  box.querySelector('.diff-slot').innerHTML = changed ? `<div class="diff">${diffHtml(def.kind === 'list' ? listText(orig) : orig, def.kind === 'list' ? listText(val) : val)}</div>` : '';
  const chk = document.getElementById(`chk-${itemId}`);
  if (chk) chk.innerHTML = checksHtml(rowChecks(row));
  const n = collectChanges(S.coreById.get(S.ui.current)).length;
  const cnt = $('#corrCount');
  if (cnt) cnt.textContent = n ? `${n} Feld(er) geändert` : 'Felder oben bearbeiten';
  const btn = $('#corrSave');
  if (btn) btn.disabled = !n;
}

function flushEditors() {
  $$('textarea[data-edit]').forEach((t) => applyEdit(t.dataset.edit, t.dataset.key, t.value));
}

function startDecision(dec) {
  const core = S.coreById.get(S.ui.current);
  if (!core) return;
  if (dec === 'accept') {
    if (collectChanges(core).length) {
      notice('Es gibt ungespeicherte Änderungen – erst speichern (Korrektur) oder verwerfen (Esc).', 'warn');
      return;
    }
    decide('accept');
  } else if (dec === 'later') decide('later');
  else if (dec === 'correct') {
    S.ui.panel = 'correct';
    render();
    $('textarea[data-edit]')?.focus();
  } else if (dec === 'reject') {
    S.ui.panel = 'reject';
    render();
  }
}

function saveCorrection() {
  flushEditors();
  const core = S.coreById.get(S.ui.current);
  const reason = ($('#corrReason')?.value || S.ui.note).trim();
  if (!collectChanges(core).length) return notice('Keine Änderung erkannt.', 'warn');
  if (!reason) {
    notice('Bitte eine Begründung für die Korrektur angeben.', 'warn');
    $('#corrReason')?.focus();
    return;
  }
  decide('correct', { reason });
}
function discardCorrection() {
  delete S.edits[S.ui.current];
  S.ui.panel = null;
  save();
  render();
}
function confirmReject() {
  const r = S.ui.reject;
  r.text = ($('#rjText')?.value || r.text).trim();
  if (!r.code) return notice('Bitte einen Grund wählen (1–9).', 'warn');
  if (r.code === 'other' && !r.text) return notice('Bei „Anderer Grund“ bitte Freitext angeben.', 'warn');
  const label = REJECT_REASONS.find(([c]) => c === r.code)[1];
  decide('reject', { reason_code: r.code, reason: r.text ? `${label}: ${r.text}` : label });
}

const fmtDur = (s) => {
  s = Math.round(s);
  if (s < 60) return `${s} s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m} min ${s % 60} s`;
  return `${Math.floor(m / 60)} h ${m % 60} min`;
};

/* ---------- handwritten ---------- */

const HW_DOMAINS = ['kvg_insured', 'kvg_billing', 'ahv', 'iv_el', 'uvg_atsg', 'eo_alv', 'bvg_3a', 'or_illness'];
const HW_QTYPES = ['numeric', 'procedural', 'yes_no', 'term', 'temporal', 'calc', 'false_premise'];
const HW_ATYPES = ['currency_chf', 'number', 'percent', 'duration', 'age', 'date', 'text', 'yes_no'];
const HW_UNITS = ['', 'CHF', 'percent', 'days', 'weeks', 'months', 'years', 'hours', 'age', 'count'];

function nextHwId() {
  const prefix = S.settings.hwPrefix || 'hw';
  const re = new RegExp(`^${prefix}-(\\d+)`);
  let max = 0;
  for (const c of S.cores) {
    const m = c.id.match(re);
    if (m) max = Math.max(max, +m[1]);
  }
  for (const h of S.handwritten) {
    const m = String(h._id).match(re);
    if (m) max = Math.max(max, +m[1]);
  }
  return `${prefix}-${String(max + 1).padStart(4, '0')}`;
}

function blankHw() {
  return {
    _id: nextHwId(),
    act: '', article_id: '', paragraph: '', domain: '', question_type: 'numeric', register: 'lay', difficulty_prior: 1,
    answer_type: '', answer_normalized: null,
    de: { question: '', answer: '', answer_aliases: [], near_miss_answers: [], evidence: '' },
    fr: null, it: null, temporal: null,
  };
}

function hwChecks(h) {
  const out = [];
  const add = (level, msg) => out.push({ level, msg });
  for (const k of ['act', 'article_id', 'domain', 'question_type', 'register', 'answer_type']) if (!h[k]) add('err', `Pflichtfeld fehlt: ${k}`);
  for (const l of LANGS) {
    const lv = h[l];
    if (!lv) {
      if (l === 'de') add('err', 'DE fehlt');
      continue;
    }
    for (const k of ['question', 'answer', 'evidence']) if (!lv[k]) add('err', `${l}.${k} fehlt`);
    const law = lawArticle(h.act, currentVersionOf(h.act), l, h.article_id);
    if (law.status === 'ok') {
      const pt = paraText(law.art, h.paragraph) ?? (law.art.p.length ? null : law.art.t);
      if (pt == null) add('err', `${l}: Abs. ${h.paragraph || '–'} nicht im Artikel`);
      else if (lv.evidence) {
        const sp = findSpan(pt, lv.evidence);
        if (!sp) add('err', `${l}: Evidenz nicht wörtlich im Absatz`);
        else if (!sp.exact) add('warn', `${l}: Evidenz nur nach Normalisierung gefunden (Apostroph ’ prüfen)`);
        else add('ok', `${l}: Evidenz wörtlich im Absatz`);
      }
    } else if (h.act && h.article_id) add('warn', `${l}: Artikel lokal nicht gefunden`);
    const an = numbers(lv.answer, l);
    if (an.size && h.question_type !== 'calc' && lv.evidence && ![...an].some((n) => numbers(lv.evidence, l).has(n))) add('err', `${l}: Zahl der Antwort nicht in der Evidenz`);
    if (/\b(Art\.|Artikel|article|articolo)\s*\d/i.test(lv.question || '')) add('warn', `${l}: Frage nennt Artikelnummer`);
    if (h.question_type === 'false_premise' && !lv.answer_core) add('err', `${l}: answer_core fehlt (false_premise)`);
    if (h.question_type === 'calc' && !asList(lv.calc_evidence).length) add('err', `${l}: calc_evidence fehlt`);
    const g = [lv.answer, ...asList(lv.answer_aliases)].map(norm);
    if (asList(lv.near_miss_answers).map(norm).some((x) => g.includes(x))) add('err', `${l}: Near-Miss = Gold`);
  }
  if (['currency_chf', 'number', 'percent', 'duration', 'age'].includes(h.answer_type) && (!h.answer_normalized || h.answer_normalized.value == null)) add('err', 'answer_normalized fehlt (Zahl)');
  if (h.question_type === 'calc') {
    if (!h.calc?.formula) add('err', 'calc.formula fehlt');
    else {
      const v = evalFormula(h.calc.formula);
      if (v == null) add('err', 'Formel nicht auswertbar');
      else if (h.answer_normalized?.value != null && Math.abs(v - h.answer_normalized.value) > 0.01) add('err', `Formel ergibt ${v}, nicht ${h.answer_normalized.value}`);
      else add('ok', `Formel ergibt ${v}`);
    }
  }
  if (h.question_type === 'temporal') {
    const t = h.temporal || {};
    if (!t.de?.outdated_answer || !t.de?.evidence) add('err', 'temporal.de: veraltete Antwort + Evidenz der Vorfassung fehlen');
    else {
      const prevVer = FEDLEX ? Object.entries(FEDLEX.acts[h.act]?.versions || {}).find(([, x]) => x.role === 'previous')?.[0] : null;
      const law = lawArticle(h.act, prevVer, 'de', h.article_id);
      if (law.status === 'ok') {
        const pt = paraText(law.art, t.previous_paragraph ?? h.paragraph) ?? articleText(law.art);
        if (!findSpan(pt, t.de.evidence)) add('err', `Evidenz der Vorfassung (${prevVer}) nicht gefunden`);
        else add('ok', `Evidenz in Vorfassung ${prevVer} gefunden`);
      }
    }
  }
  return out;
}

function hwLawHtml(h, l) {
  const curVer = currentVersionOf(h.act);
  const lawL = lawArticle(h.act, curVer, l, h.article_id);
  const pt = lawL.status === 'ok' ? paraText(lawL.art, h.paragraph) ?? (lawL.art.p.length ? null : lawL.art.t) : null;
  if (pt == null) return '';
  return `<div class="law"><div class="law-head"><strong>${esc(lawL.art.h)} · Abs. ${esc(h.paragraph || '–')}</strong><span class="muted small">Fassung ${esc(curVer)}</span></div><div class="law-text"><p class="target">${highlight(pt, null, h[l]?.evidence)}</p></div></div>`;
}

function hwStatusHtml(h) {
  const checks = hwChecks(h);
  const errs = checks.filter((c) => c.level === 'err').length;
  return {
    checks: checksHtml(checks),
    errs: errs ? `<span class="small danger">${errs} Fehler offen</span>` : '<span class="small" style="color:var(--ok)">keine Fehler</span>',
  };
}

function refreshHw() {
  const h = S.ui.hwEdit;
  const st = hwStatusHtml(h);
  const c = $('#hwChecks');
  if (c) c.innerHTML = st.checks;
  const e = $('#hwErrs');
  if (e) e.innerHTML = st.errs;
  $$('[data-hwlaw]').forEach((el) => (el.innerHTML = hwLawHtml(h, el.dataset.hwlaw)));
  save();
}

function renderHandwritten() {
  const view = $('#view');
  const h = S.ui.hwEdit || (S.ui.hwEdit = blankHw());
  const acts = FEDLEX ? Object.keys(FEDLEX.acts) : uniq(S.cores.map((c) => rawGet(primary(c), 'act')));
  const curVer = currentVersionOf(h.act);
  const artOpts = FEDLEX && h.act ? Object.keys(FEDLEX.acts[h.act].versions[curVer].langs.de) : [];
  const law = lawArticle(h.act, curVer, 'de', h.article_id);
  const paraOpts = law.status === 'ok' ? law.art.p.map(([n]) => n) : [];
  const sel = (name, vals, v, req = true) => `<label><span class="${req ? 'req' : ''}">${name}</span><select data-hw="${name}">${options(vals, v ?? '', '–')}</select></label>`;
  const inp = (name, v, req = true, ph = '') => `<label><span class="${req ? 'req' : ''}">${name}</span><input data-hw="${name}" value="${esc(v ?? '')}" placeholder="${esc(ph)}"></label>`;
  const langBlock = (l) => {
    const lv = h[l];
    if (!lv) return `<div class="card"><h3>${LANG_LABEL[l]}</h3><button class="btn" data-hw-add="${l}">${LANG_LABEL[l]}e Fassung hinzufügen</button></div>`;
    const ta = (k, label, req, rows = 2) => `<label><span class="${req ? 'req' : ''}">${label}</span><textarea data-hwl="${l}.${k}" rows="${rows}">${esc(Array.isArray(lv[k]) ? lv[k].join('\n') : lv[k] ?? '')}</textarea></label>`;
    return `<div class="card" lang="${l}"><h3>${LANG_LABEL[l]}${l !== 'de' ? ` <button class="btn small" data-hw-del="${l}">entfernen</button>` : ''}</h3><div class="hw-lang">
      ${ta('question', 'Frage', true, 3)}${ta('answer', 'Antwort (kurz)', true, 1)}${ta('answer_aliases', 'Antwortvarianten (eine pro Zeile)', false)}${ta('near_miss_answers', 'Near-Miss (eine pro Zeile)', false)}${ta('evidence', 'Evidenz (wörtlich aus dem Absatz kopieren)', true)}
      ${h.question_type === 'false_premise' ? ta('answer_core', 'answer_core (wörtlich)', true, 1) : ''}
      ${h.question_type === 'calc' ? ta('calc_evidence', 'calc_evidence (eine pro Zeile, wörtlich)', true) : ''}
      ${h.question_type === 'temporal' ? `<label><span class="${l === 'de' ? 'req' : ''}">Veraltete Antwort</span><input data-hwt="${l}.outdated_answer" value="${esc(h.temporal?.[l]?.outdated_answer ?? '')}"></label><label><span class="${l === 'de' ? 'req' : ''}">Evidenz Vorfassung (wörtlich)</span><textarea data-hwt="${l}.evidence" rows="2">${esc(h.temporal?.[l]?.evidence ?? '')}</textarea></label>` : ''}
      </div><div data-hwlaw="${l}">${hwLawHtml(h, l)}</div></div>`;
  };
  const st = hwStatusHtml(h);
  view.innerHTML = `<section class="content"><div class="scroll">
    <div class="core-head"><h2>Handschrift: ${esc(h._id)}</h2><span class="tag">author: human</span><span class="tag">generator_model: none</span><span class="muted small">Zeit: ${fmtDur((S.time['hw:' + h._id] || 0) / 1000)}</span>
    <label class="small">Präfix <input id="hwPrefix" value="${esc(S.settings.hwPrefix)}" size="4"></label></div>
    <p class="small muted">Regeln: Wahrheit nur aus Fedlex (Stichtag 01.10.2026), selbst formulieren ohne KI, eine Frage – eine Kurzantwort, Evidenz Zeichen für Zeichen kopieren, keine Artikelnummer in der Frage, Versicherungszweig nennen, Schweizer Schreibweise, keine Personendaten.</p>
    <div class="card"><div class="hw-grid">
      ${sel('act', acts, h.act)}
      ${artOpts.length ? `<label><span class="req">article_id</span><input list="artList" data-hw="article_id" value="${esc(h.article_id)}"><datalist id="artList">${artOpts.map((a) => `<option value="${esc(a)}">`).join('')}</datalist></label>` : inp('article_id', h.article_id, true, 'art_64')}
      ${paraOpts.length ? sel('paragraph', paraOpts, h.paragraph, false) : inp('paragraph', h.paragraph, false, '1, 1bis oder leer')}
      ${sel('domain', HW_DOMAINS, h.domain)}
      ${sel('question_type', HW_QTYPES, h.question_type)}
      ${sel('register', ['lay', 'professional'], h.register)}
      ${sel('difficulty_prior', ['1', '2', '3'], String(h.difficulty_prior))}
      ${sel('answer_type', HW_ATYPES, h.answer_type)}
      <label>answer_normalized.value<input data-hwn="value" value="${esc(h.answer_normalized?.value ?? '')}" inputmode="decimal"></label>
      <label>answer_normalized.unit<select data-hwn="unit">${options(HW_UNITS.filter(Boolean), h.answer_normalized?.unit ?? '', '–')}</select></label>
      ${h.question_type === 'calc' ? `<label><span class="req">calc.formula</span><input data-hwc="formula" value="${esc(h.calc?.formula ?? '')}" placeholder="300 + 10/100 * (1300 - 300)"></label><label style="grid-column:span 2"><span class="req">calc.inputs (JSON)</span><input data-hwc="inputs" value="${esc(JSON.stringify(h.calc?.inputs ?? []))}"></label>` : ''}
      ${h.question_type === 'temporal' ? inp('previous_paragraph', h.temporal?.previous_paragraph ?? h.paragraph, false) : ''}
    </div></div>
    <div id="hwChecks">${st.checks}</div>
    <div class="langs" style="--cols:3;margin-top:10px">${LANGS.map(langBlock).join('')}</div>
    <div class="row" style="margin:12px 0">
      <button class="btn primary" id="hwSave">Kern speichern (Strg+Enter)</button>
      <button class="btn" id="hwNew">Neu / leeren</button>
      <span id="hwErrs">${st.errs}</span>
    </div>
    <h3>Gespeicherte handgeschriebene Kerne (${S.handwritten.length})</h3>
    <ul class="hw-list">${S.handwritten.map((x, i) => `<li><span class="mono">${esc(x._id)}</span><span class="q">${esc(x.de?.question || '')} → <strong>${esc(x.de?.answer || '')}</strong></span><span class="small muted">${esc(x.act)} ${esc(x.article_id)}</span><button class="btn small" data-hw-open="${i}">bearbeiten</button><button class="btn small danger" data-hw-rm="${i}">löschen</button></li>`).join('') || '<li class="muted">noch keine</li>'}</ul>
  </div></section>`;
  bindHandwritten();
}

function bindHandwritten() {
  const h = S.ui.hwEdit;
  const rerender = () => {
    save();
    render();
  };
  $$('[data-hw]').forEach((el) => {
    const apply = () => {
      const k = el.dataset.hw;
      if (k === 'previous_paragraph') {
        h.temporal = h.temporal || {};
        h.temporal.previous_paragraph = el.value.trim();
        return;
      }
      h[k] = k === 'difficulty_prior' ? Number(el.value) : el.value.trim();
      if (k === 'act') { h.article_id = ''; h.paragraph = ''; }
      if (k === 'question_type' && el.value === 'temporal' && !h.temporal) h.temporal = { previous_paragraph: h.paragraph, de: { outdated_answer: '', evidence: '' }, fr: null, it: null };
    };
    if (el.tagName === 'SELECT') el.addEventListener('change', () => { apply(); rerender(); });
    else {
      el.addEventListener('input', () => { apply(); refreshHw(); });
      if (el.dataset.hw === 'article_id') el.addEventListener('change', rerender);
    }
  });
  $$('[data-hwl]').forEach((el) =>
    el.addEventListener('input', () => {
      const [l, k] = el.dataset.hwl.split('.');
      const listKeys = ['answer_aliases', 'near_miss_answers', 'calc_evidence'];
      h[l][k] = listKeys.includes(k) ? el.value.split('\n').map((s) => s.trim()).filter(Boolean) : el.value.trim();
      refreshHw();
    }),
  );
  $$('[data-hwt]').forEach((el) =>
    el.addEventListener('input', () => {
      const [l, k] = el.dataset.hwt.split('.');
      h.temporal = h.temporal || { previous_paragraph: h.paragraph };
      h.temporal[l] = h.temporal[l] || {};
      h.temporal[l][k] = el.value.trim();
      refreshHw();
    }),
  );
  $$('[data-hwn]').forEach((el) =>
    el.addEventListener(el.tagName === 'SELECT' ? 'change' : 'input', () => {
      h.answer_normalized = h.answer_normalized || { value: null, unit: '' };
      const v = el.value.trim();
      h.answer_normalized[el.dataset.hwn] = el.dataset.hwn === 'value' ? (v === '' ? null : Number(v.replace(/['’]/g, '').replace(',', '.'))) : v;
      if (h.answer_normalized.value == null && !h.answer_normalized.unit) h.answer_normalized = null;
      refreshHw();
    }),
  );
  $$('[data-hwc]').forEach((el) =>
    el.addEventListener('input', () => {
      h.calc = h.calc || { formula: '', inputs: [] };
      if (el.dataset.hwc === 'inputs') {
        try { h.calc.inputs = JSON.parse(el.value || '[]'); } catch (_) { return; }
      } else h.calc.formula = el.value.trim();
      refreshHw();
    }),
  );
  $$('[data-hw-add]').forEach((b) => b.addEventListener('click', () => { h[b.dataset.hwAdd] = { question: '', answer: '', answer_aliases: [], near_miss_answers: [], evidence: '' }; rerender(); }));
  $$('[data-hw-del]').forEach((b) => b.addEventListener('click', () => { h[b.dataset.hwDel] = null; rerender(); }));
  $('#hwPrefix')?.addEventListener('change', (e) => {
    S.settings.hwPrefix = e.target.value.trim() || 'hw';
    if (!S.handwritten.some((x) => x._id === h._id)) h._id = nextHwId();
    rerender();
  });
  $('#hwSave')?.addEventListener('click', saveHandwritten);
  $('#hwNew')?.addEventListener('click', () => { S.ui.hwEdit = blankHw(); rerender(); });
  $$('[data-hw-open]').forEach((b) => b.addEventListener('click', () => { S.ui.hwEdit = clone(S.handwritten[+b.dataset.hwOpen]); rerender(); }));
  $$('[data-hw-rm]').forEach((b) =>
    b.addEventListener('click', () => {
      const x = S.handwritten[+b.dataset.hwRm];
      if (confirm(`Kern ${x._id} löschen?`)) { S.handwritten.splice(+b.dataset.hwRm, 1); rerender(); }
    }),
  );
}

function saveHandwritten() {
  const h = S.ui.hwEdit;
  if (!h.act || !h.article_id || !h.de?.question || !h.de?.answer || !h.de?.evidence) return notice('Pflichtfelder fehlen (Gesetz, Artikel, DE-Frage, DE-Antwort, DE-Evidenz).', 'warn');
  const errs = hwChecks(h).filter((c) => c.level === 'err');
  if (errs.length && !confirm(`${errs.length} Fehler offen (${errs.map((e) => e.msg).join('; ')}). Trotzdem speichern?`)) return;
  const rec = {
    ...clone(h),
    author: 'human',
    generator_model: 'none',
    _written_by: REVIEWER,
    _written_at: nowIso(),
    _duration_s: Math.round((S.time['hw:' + h._id] || 0) / 1000),
  };
  if (rec.question_type !== 'temporal') rec.temporal = null;
  if (rec.question_type !== 'calc') delete rec.calc;
  const i = S.handwritten.findIndex((x) => x._id === h._id);
  if (i >= 0) S.handwritten[i] = rec;
  else S.handwritten.push(rec);
  S.ui.hwEdit = blankHw();
  save();
  notice(`${rec._id} gespeichert.`);
  render();
}

/* ---------- blind sample ---------- */

const GRADE = { c: ['CORRECT', null], n: ['NOT_ATTEMPTED', null], i: ['INCORRECT', 'OTHER'], s: ['INCORRECT', 'STALE'], m: ['INCORRECT', 'NEAR_MISS'], o: ['INCORRECT', 'OTHER'] };
const labelKey = (r) => `${r.id}|${r.model}|${r.condition}`;

function renderBlind() {
  const view = $('#view');
  if (!S.sample.length) {
    view.innerHTML = `<section class="content"><div class="empty">Keine Stichprobe geladen. <code>human_labels/sample_20pct.jsonl</code> (aus <code>inkraft sample-human</code>) oder Antwortdateien aus <code>responses/</code> laden.</div></section>`;
    return;
  }
  const idx = Math.max(0, Math.min(S.sample.length - 1, S.ui.blindIdx));
  S.ui.blindIdx = idx;
  const r = S.sample[idx];
  const item = S.rows.get(r.id);
  const lab = S.labels[labelKey(r)];
  const unc = lab ? lab.uncertain : S.ui.uncertain;
  const itemHtml = item
    ? `<div class="field"><div class="lbl">Frage (${esc(langOf(item))}, Stichtag ${esc(item.as_of || '2026-10-01')})</div><div class="val">${esc(F(item, 'question'))}</div></div>
       <div class="field"><div class="lbl">Gold</div><div class="val answer">${esc(F(item, 'answer'))}</div></div>
       <div class="field"><div class="lbl">Varianten</div><div class="val">${esc(asList(F(item, 'aliases')).join('; ') || '–')}</div></div>
       <div class="field"><div class="lbl">Veraltet</div><div class="val">${esc(asList(F(item, 'outdated')).join('; ') || '–')}</div></div>
       <div class="field"><div class="lbl">Near-Miss</div><div class="val">${esc(asList(F(item, 'nearMiss')).join('; ') || '–')}</div></div>`
    : `<div class="empty">Item ${esc(r.id)} ist nicht im geladenen Datensatz – bitte test.jsonl laden.</div>`;
  const done = S.sample.filter((x) => S.labels[labelKey(x)]).length;
  view.innerHTML = `<section class="content"><div class="scroll" style="max-width:900px;margin:0 auto;width:100%">
    <div class="core-head"><h2>${idx + 1} / ${S.sample.length}</h2><span class="mono small muted">${esc(r.id)}</span><span class="muted small">${done} bewertet · Annotator <input id="annot" value="${esc(S.settings.annotator)}" size="10"></span>
    ${lab ? `<span class="tag ${lab.human_grade === 'CORRECT' ? 'accept' : lab.human_grade === 'INCORRECT' ? 'reject' : 'later'}">${esc(lab.human_grade)}${lab.human_subtype ? ' / ' + esc(lab.human_subtype) : ''}${lab.uncertain ? ' ?' : ''}</span>` : ''}</div>
    <p class="small muted">Blind: Modellname und Judge-Urteil sind ausgeblendet. Eigenes Wissen überstimmt das Gold nicht – wirkt das Gold falsch, Item-ID notieren.</p>
    <div class="card">${itemHtml}</div>
    <div class="card" style="margin-top:12px"><h3>Antwort des Modells</h3><div class="blind-resp">${esc(r.response)}</div></div>
    <div class="row grade-bar" style="margin-top:12px">
      <button class="btn dec accept ${lab?.human_grade === 'CORRECT' ? 'sel' : ''}" data-g="c">CORRECT <kbd>C</kbd></button>
      <button class="btn dec reject ${lab?.human_grade === 'INCORRECT' && lab?.human_subtype === 'STALE' ? 'sel' : ''}" data-g="s">INCORRECT · STALE <kbd>S</kbd></button>
      <button class="btn dec reject ${lab?.human_grade === 'INCORRECT' && lab?.human_subtype === 'NEAR_MISS' ? 'sel' : ''}" data-g="m">· NEAR_MISS <kbd>M</kbd></button>
      <button class="btn dec reject ${lab?.human_grade === 'INCORRECT' && lab?.human_subtype === 'OTHER' ? 'sel' : ''}" data-g="o">· OTHER <kbd>I</kbd>/<kbd>O</kbd></button>
      <button class="btn dec later ${lab?.human_grade === 'NOT_ATTEMPTED' ? 'sel' : ''}" data-g="n">NOT_ATTEMPTED <kbd>N</kbd></button>
      <label class="small"><input type="checkbox" id="unc" ${unc ? 'checked' : ''}> unsicher <kbd>?</kbd></label>
      <span class="spacer" style="flex:1"></span>
      <button class="btn" id="bPrev">←</button><button class="btn" id="bNext">→</button><button class="btn" id="bOpen">nächste offene</button>
    </div>
  </div></section>`;
  $$('[data-g]').forEach((b) => b.addEventListener('click', () => gradeBlind(b.dataset.g)));
  $('#unc').addEventListener('change', (e) => toggleUncertain(e.target.checked));
  $('#bPrev').addEventListener('click', () => blindMove(-1));
  $('#bNext').addEventListener('click', () => blindMove(1));
  $('#bOpen').addEventListener('click', blindNextOpen);
  $('#annot').addEventListener('change', (e) => { S.settings.annotator = e.target.value.trim() || 'niklas'; save(); });
}

function gradeBlind(key) {
  const r = S.sample[S.ui.blindIdx];
  if (!r || !GRADE[key]) return;
  const [g, sub] = GRADE[key];
  const prev = S.labels[labelKey(r)];
  S.labels[labelKey(r)] = {
    ...r,
    human_grade: g,
    human_subtype: sub,
    uncertain: prev ? prev.uncertain : S.ui.uncertain,
    annotator: S.settings.annotator,
    labelled_at: new Date().toISOString().replace(/\.\d{3}Z$/, '+00:00'),
  };
  S.ui.uncertain = false;
  save();
  blindMove(1);
}
function toggleUncertain(v) {
  const r = S.sample[S.ui.blindIdx];
  const lab = r && S.labels[labelKey(r)];
  if (lab) lab.uncertain = v ?? !lab.uncertain;
  else S.ui.uncertain = v ?? !S.ui.uncertain;
  save();
  render();
}
function blindMove(d) {
  S.ui.blindIdx = Math.max(0, Math.min(S.sample.length - 1, S.ui.blindIdx + d));
  save();
  render();
}
function blindNextOpen() {
  const n = S.sample.length;
  for (let k = 1; k <= n; k++) {
    const i = (S.ui.blindIdx + k) % n;
    if (!S.labels[labelKey(S.sample[i])]) {
      S.ui.blindIdx = i;
      save();
      return render();
    }
  }
  notice('Alle Antworten der Stichprobe sind bewertet.');
}

/* ---------- export ---------- */

function download(name, text, type = 'application/x-ndjson') {
  const blob = new Blob([text], { type: `${type};charset=utf-8` });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    URL.revokeObjectURL(a.href);
    a.remove();
  }, 1000);
}
const jsonl = (rows) => rows.map((r) => JSON.stringify(r)).join('\n') + (rows.length ? '\n' : '');
const reviewVersion = () => `human-review-v1 (${today()})`;

function finalDecisions() {
  const out = new Map();
  for (const e of S.log) {
    if (e.decision === 'reset') out.delete(e.core_id);
    else out.set(e.core_id, e);
  }
  return out;
}

function buildReviewed() {
  const fin = finalDecisions();
  const out = [];
  for (const id of S.order) {
    const r = clone(S.rows.get(id));
    const d = fin.get(coreIdOf(r));
    if (d?.decision === 'reject') continue;
    if (d?.decision === 'correct') {
      const mine = d.changes.filter((c) => c.item_id === id);
      if (mine.length) {
        const before = {};
        for (const c of mine) {
          before[c.field] = c.old;
          setPath(r, c.field, c.new);
        }
        r.authoring = r.authoring || {};
        let log = r.authoring.manual_correction;
        log = log == null ? [] : Array.isArray(log) ? log : [log];
        log.push({ review: reviewVersion(), by: REVIEWER, reason: d.reason, before });
        r.authoring.manual_correction = log;
      }
    }
    if (d?.decision === 'accept') (r.review_notes = r.review_notes || []).push({ review: reviewVersion(), note: d.reason || 'geprüft: korrekt laut Gesetzestext' });
    out.push(r);
  }
  return out;
}

function buildDecisions() {
  const decisions = [];
  for (const d of finalDecisions().values()) {
    if (d.decision === 'later') continue;
    const action = { accept: 'keep', correct: 'patch', reject: 'drop' }[d.decision];
    const x = { core_id: d.core_id, action, reason: d.reason || (action === 'keep' ? 'geprüft: korrekt laut Gesetzestext' : '') };
    const core = S.coreById.get(d.core_id);
    const block = (core && blockOf(core)) ?? d.block;
    if (block != null) x.block = block;
    if (action === 'patch') {
      for (const c of d.changes) {
        const row = S.rows.get(c.item_id);
        const l = row ? langOf(row) : (c.item_id.match(/-(de|fr|it)$/) || [])[1];
        (x[l] = x[l] || {})[c.field] = c.new;
      }
    }
    decisions.push(x);
  }
  return { version: reviewVersion(), reviewer: REVIEWER, decisions };
}

function buildHandwritten() {
  return S.handwritten.map((h) => {
    const { _id, ...rest } = h;
    return { _id, ...rest };
  });
}

function buildLabels() {
  return S.sample.map((r) => S.labels[labelKey(r)]).filter(Boolean).concat(Object.values(S.labels).filter((l) => !S.sample.some((r) => labelKey(r) === labelKey(l))));
}

function summaryMd() {
  const fin = [...finalDecisions().values()];
  const by = (k) => fin.filter((d) => d.decision === k);
  const total = S.cores.length;
  const final = fin.filter((d) => d.decision !== 'later');
  const secs = final.map((d) => d.duration_s || 0).filter((s) => s > 0).sort((a, b) => a - b);
  const sum = secs.reduce((a, b) => a + b, 0);
  const med = secs.length ? secs[Math.floor(secs.length / 2)] : 0;
  const perAct = {};
  for (const c of S.cores) {
    const a = rawGet(primary(c), 'act') || '–';
    const d = finalDecisions().get(c.id);
    perAct[a] = perAct[a] || { total: 0, accept: 0, correct: 0, reject: 0, later: 0 };
    perAct[a].total++;
    if (d) perAct[a][d.decision]++;
  }
  const perGen = {};
  for (const c of S.cores) {
    const g = genOf(primary(c));
    const d = finalDecisions().get(c.id);
    perGen[g] = perGen[g] || { total: 0, accept: 0, correct: 0, reject: 0, later: 0 };
    perGen[g].total++;
    if (d) perGen[g][d.decision]++;
  }
  const perBlock = {};
  for (const c of S.cores) {
    const b = blockOf(c);
    if (b == null) continue;
    const k = `${b}${hintOf(c).block_label ? ` – ${hintOf(c).block_label}` : ''}`;
    const d = finalDecisions().get(c.id);
    const s = (perBlock[k] = perBlock[k] || { total: 0, decided: 0, reject: 0, secs: [] });
    s.total++;
    if (d && d.decision !== 'later') {
      s.decided++;
      if (d.decision === 'reject') s.reject++;
      if (d.duration_s > 0) s.secs.push(d.duration_s);
    }
  }
  const blockTbl = Object.keys(perBlock).length
    ? `\n## Nach Block (Review-Paket)\n\n| Block | Kerne | Entscheidungen | verworfen | Verwerfquote | mittlere Prüfzeit |\n|---|---:|---:|---:|---:|---:|\n${Object.entries(perBlock)
        .sort((a, b) => a[0].localeCompare(b[0], 'de', { numeric: true }))
        .map(([k, s]) => `| ${k} | ${s.total} | ${s.decided} | ${s.reject} | ${s.decided ? ((100 * s.reject) / s.decided).toFixed(1) + ' %' : '–'} | ${s.secs.length ? fmtDur(s.secs.reduce((a, b) => a + b, 0) / s.secs.length) : '–'} |`)
        .join('\n')}\n\nEntscheidungen = endgültige Entscheidungen (ohne „später“); Verwerfquote = verworfen / Entscheidungen.\n`
    : '';
  const reasons = {};
  for (const d of by('reject')) reasons[d.reason_code || 'other'] = (reasons[d.reason_code || 'other'] || 0) + 1;
  const tbl = (obj) => '| | Kerne | korrekt | korrigiert | verworfen | später |\n|---|---:|---:|---:|---:|---:|\n' + Object.entries(obj).sort().map(([k, v]) => `| ${k} | ${v.total} | ${v.accept} | ${v.correct} | ${v.reject} | ${v.later} |`).join('\n');
  const ts = S.log.map((e) => e.timestamp).sort();
  const labels = buildLabels();
  return `# Prüfprotokoll Inkraft – Zusammenfassung

Prüfer: ${REVIEWER} · erstellt ${nowIso()} · Werkzeug ${TOOL}
Datensatz: ${S.files.join(', ') || '–'} (${S.rows.size} Zeilen, ${total} Kerne)
Zeitraum der Prüfung: ${ts[0] || '–'} bis ${ts.at(-1) || '–'}

## Entscheidungen

| Entscheidung | Kerne |
|---|---:|
| ✓ korrekt | ${by('accept').length} |
| ✎ korrigiert | ${by('correct').length} |
| ✗ verworfen | ${by('reject').length} |
| ? später | ${by('later').length} |
| offen | ${total - fin.length} |

Abgeschlossen: ${final.length} von ${total} Kernen (${total ? ((100 * final.length) / total).toFixed(1) : 0} %).
Geänderte Felder insgesamt: ${by('correct').reduce((a, d) => a + d.changes.length, 0)}.
${final.some((d) => d.agent_revealed_before_decision) ? `Agenten-Einschätzung vor der Entscheidung aufgedeckt: ${final.filter((d) => d.agent_revealed_before_decision).length} Kerne.
` : ''}
## Zeit

Summe ${fmtDur(sum)} · Median je Kern ${fmtDur(med)} · Mittel je Kern ${fmtDur(secs.length ? sum / secs.length : 0)} (aktive Zeit, Leerlauf > 2 min nicht gezählt).

## Nach Gesetz

${tbl(perAct)}

## Nach Generator

${tbl(perGen)}
${blockTbl}
## Verwerfungsgründe

${Object.entries(reasons).map(([k, v]) => `- ${REJECT_REASONS.find(([c]) => c === k)?.[1] || k}: ${v}`).join('\n') || '- keine'}

## Handschrift und Blind-Stichprobe

- Neue handgeschriebene Kerne: ${S.handwritten.length}
- Blind-Labels: ${labels.length} von ${S.sample.length} (unsicher: ${labels.filter((l) => l.uncertain).length})
`;
}

function doExport(kind) {
  const stamp = today();
  const tasks = {
    log: () => download('review_log.jsonl', jsonl(S.log)),
    decisions: () => download('review_decisions.json', JSON.stringify(buildDecisions(), null, 2) + '\n', 'application/json'),
    reviewed: () => download('metadata.reviewed.jsonl', jsonl(buildReviewed())),
    handwritten: () => download('handwritten.jsonl', jsonl(buildHandwritten())),
    labels: () => download(`labels_${S.settings.annotator}.jsonl`, jsonl(buildLabels())),
    summary: () => download('pruefung_zusammenfassung.md', summaryMd(), 'text/markdown'),
  };
  if (kind === 'all') {
    const list = ['log', 'decisions', 'summary'];
    if (S.rows.size) list.push('reviewed');
    if (S.handwritten.length) list.push('handwritten');
    if (Object.keys(S.labels).length) list.push('labels');
    list.forEach((k, i) => setTimeout(tasks[k], i * 400));
    notice(`${list.length} Dateien exportiert (${stamp}). Falls der Browser fragt: mehrere Downloads erlauben.`);
  } else if (tasks[kind]) tasks[kind]();
  else if (kind === 'clearData') {
    if (!confirm('Geladenen Datensatz und Stichprobe aus dem Browser entfernen? Entscheidungen bleiben erhalten.')) return;
    S.rows.clear();
    S.files = [];
    S.sample = [];
    rebuild();
    saveData();
    render();
  } else if (kind === 'reset') {
    if (!confirm('Wirklich ALLE Prüfdaten (Entscheidungen, Korrekturen, Handschrift, Labels) im Browser löschen? Vorher exportieren!')) return;
    if (!confirm('Letzte Rückfrage: unwiderruflich löschen?')) return;
    try {
      localStorage.removeItem(STORE_KEY);
      localStorage.removeItem(DATA_KEY);
    } catch (_) { /* ignore */ }
    location.reload();
  }
}

/* ---------- time tracking ---------- */

let lastActivity = Date.now();
['keydown', 'mousemove', 'mousedown', 'wheel', 'touchstart'].forEach((ev) => window.addEventListener(ev, () => (lastActivity = Date.now()), { passive: true }));
setInterval(() => {
  if (document.visibilityState !== 'visible' || Date.now() - lastActivity > IDLE_MS) return;
  let key = null;
  if (S.ui.mode === 'review' && S.ui.current && S.cores.length) key = S.ui.current;
  else if (S.ui.mode === 'handwritten' && S.ui.hwEdit) key = 'hw:' + S.ui.hwEdit._id;
  if (!key) return;
  S.time[key] = (S.time[key] || 0) + 1000;
  if (Math.round(S.time[key] / 1000) % 15 === 0) save();
}, 1000);

/* ---------- keyboard ---------- */

function onKey(e) {
  const t = e.target;
  const typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT') && t.type !== 'checkbox' && t.type !== 'radio';
  const k = e.key.toLowerCase();
  if (!$('#help').hidden) {
    if (k === 'escape' || k === 'h') $('#help').hidden = true;
    return;
  }
  if (e.altKey && ['1', '2', '3'].includes(e.key)) {
    setMode(['review', 'handwritten', 'blind'][+e.key - 1]);
    e.preventDefault();
    return;
  }
  if ((e.ctrlKey || e.metaKey) && k === 'enter') {
    e.preventDefault();
    if (S.ui.mode === 'review' && S.ui.panel === 'correct') saveCorrection();
    else if (S.ui.mode === 'review' && S.ui.panel === 'reject') confirmReject();
    else if (S.ui.mode === 'handwritten') saveHandwritten();
    return;
  }
  if (k === 'escape') {
    if (typing) t.blur();
    if (S.ui.mode === 'review' && S.ui.panel === 'correct') discardCorrection();
    else if (S.ui.mode === 'review' && S.ui.panel) { S.ui.panel = null; render(); }
    return;
  }
  if (typing || e.ctrlKey && k !== 'z' || e.metaKey || e.altKey) return;
  if (k === 'h') { $('#help').hidden = false; return; }
  if (S.ui.mode === 'review' && S.cores.length) {
    if (S.ui.panel === 'reject' && /^[1-9]$/.test(e.key)) {
      const r = REJECT_REASONS[+e.key - 1];
      if (r) { S.ui.reject.code = r[0]; render(); }
      return;
    }
    if (e.ctrlKey && k === 'z') { e.preventDefault(); undoDecision(); return; }
    const map = {
      a: () => startDecision('accept'),
      k: () => startDecision('correct'),
      v: () => startDecision('reject'),
      s: () => startDecision('later'),
      p: applyProposal,
      n: () => gotoNextOpen(true),
      arrowright: () => move(1),
      arrowleft: () => move(-1),
      t: () => { S.settings.showFullArticle = !S.settings.showFullArticle; save(); render(); },
      '/': () => $('#fSearch')?.focus(),
      g: () => $('#fJump')?.focus(),
    };
    if (S.ui.panel && ['a', 'k', 'v', 's', 'p'].includes(k)) return;
    if (map[k]) { e.preventDefault(); map[k](); }
  } else if (S.ui.mode === 'blind' && S.sample.length) {
    if (GRADE[k]) { e.preventDefault(); gradeBlind(k); }
    else if (e.key === '?') toggleUncertain();
    else if (k === 'arrowright') blindMove(1);
    else if (k === 'arrowleft') blindMove(-1);
  }
}

function setMode(m) {
  S.ui.mode = m;
  S.ui.panel = null;
  save();
  render();
}

/* ---------- init ---------- */

function init() {
  load();
  document.addEventListener('keydown', onKey);
  $$('.mode').forEach((b) => b.addEventListener('click', () => setMode(b.dataset.mode)));
  for (const id of ['#fileInput', '#fileInput2']) $(id).addEventListener('change', (e) => { loadFiles([...e.target.files]); e.target.value = ''; });
  $('#exportBtn').addEventListener('click', (e) => { e.stopPropagation(); $('#exportMenu').hidden = !$('#exportMenu').hidden; });
  document.addEventListener('click', () => ($('#exportMenu').hidden = true));
  $('#exportMenu').addEventListener('click', (e) => {
    const b = e.target.closest('[data-export]');
    if (b) doExport(b.dataset.export);
  });
  $('#helpBtn').addEventListener('click', () => ($('#help').hidden = false));
  $('#help').addEventListener('click', (e) => { if (e.target.id === 'help' || e.target.hasAttribute('data-close')) $('#help').hidden = true; });
  $('#themeBtn').addEventListener('click', () => {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('inkraft-theme', root.dataset.theme); } catch (_) { /* ignore */ }
  });
  window.addEventListener('dragover', (e) => { e.preventDefault(); document.body.classList.add('drag'); });
  window.addEventListener('dragleave', (e) => { if (!e.relatedTarget) document.body.classList.remove('drag'); });
  window.addEventListener('drop', (e) => {
    e.preventDefault();
    document.body.classList.remove('drag');
    if (e.dataTransfer?.files?.length) loadFiles([...e.dataTransfer.files]);
  });
  window.addEventListener('beforeunload', save);
  render();
}

window.InkraftApp = { S, loadFiles, doExport, buildReviewed, buildDecisions, buildLabels, buildHandwritten, summaryMd, coreChecks, decide, startDecision, saveCorrection, confirmReject, applyEdit, applyProposal, proposalChanges, select, setMode, gradeBlind };
init();
