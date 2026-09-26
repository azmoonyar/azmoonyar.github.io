import { questionBank } from "./questions.js";
import {
  COUNT_OPTIONS, DEFAULT_COUNT, PRESETS, SIMULATION, TIERS,
  buildSimulationSession, buildTierSession, countByTier, normalizeTiers, poolForTiers, resolveCount,
} from "./exam-builder.js";
import { handleInstall, onInstallChange, renderInstallButton } from "./pwa.js";
import { renderThemeToggle, toggleTheme } from "./theme.js";

const app = document.querySelector("#app");

const TIER_META = {
  1: { title: "خیلی مهم", hint: "بیشترین تکرار در نمونه‌آزمون‌های مستقل؛ حتماً بلد باش." },
  2: { title: "مهم", hint: "پرتکرار و کلیدی؛ برای آمادگی آزمون بسیار مهم است." },
  3: { title: "متوسط", hint: "ارزش مطالعه و تمرین دارد." },
  4: { title: "کم‌تکرار", hint: "جزئی‌تر و کمتر دیده‌شده." },
  5: { title: "تکمیلی", hint: "کمتر دیده می‌شود، ولی دانستنش مفید است." },
};

const MODES = [
  { id: "simulation", title: "آزمون شبیه‌سازی‌شده", copy: "۳۰ سؤال مثل آزمون اصلی: ۲۰ سؤال از فصل ۱ و ۱۰ سؤال از سایر فصل‌ها.", badge: "پیشنهادی" },
  { id: "essentials", title: "مرور مهم‌ترین‌ها", copy: "فقط سطح ۱ (خیلی مهم)" },
  { id: "serious", title: "آمادگی جدی آزمون", copy: "سطح‌های ۱ و ۲" },
  { id: "complete", title: "مطالعهٔ کامل", copy: "هر پنج سطح؛ همهٔ سؤال‌های بانک" },
  { id: "custom", title: "انتخاب دستی", copy: "سطح‌ها را خودت انتخاب کن" },
];

const STORAGE_KEYS = { setup: "ayeen.setup.v1", seen: "ayeen.seen.v1", session: "ayeen.session.v1" };

const NAV_PAGE_SIZE = 40;
const NAV_FILTERS = [
  { id: "all", label: "همه" },
  { id: "unanswered", label: "بی‌پاسخ" },
  { id: "wrong", label: "غلط" },
  { id: "important", label: "★ سطح ۱" },
];
// The app logo («آ» drawn as a road; branding/logo.svg); the name next to it stays live text.
const BRAND_LOGO = `<img class="brand-logo" src="./icons/icon.svg" alt="" width="32" height="32">`;
const STATUS_LABEL = { unanswered: "بدون پاسخ", correct: "پاسخ صحیح", wrong: "پاسخ غلط" };

const faNumber = (value) => Number(value).toLocaleString("fa-IR");
const faDigits = (value) => String(value).replace(/\d/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[digit]);
const tierName = (tier) => `سطح ${faNumber(tier)}`;
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);

function readStorage(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeStorage(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage can be unavailable (private mode, blocked site data); the app works without it.
  }
}

function removeStorage(key) {
  try {
    window.localStorage.removeItem(key);
  } catch {
    // See writeStorage.
  }
}

let questionHints = {};
const hintsLoaded = import("./data/question-hints.js?v=20260925-2") // bump when the hints are regenerated
  .then((module) => { questionHints = module.questionHints ?? {}; })
  .catch(() => { questionHints = {}; }); // hints are optional; the book source still shows

const tierCounts = countByTier(questionBank);
const savedSetup = readStorage(STORAGE_KEYS.setup, null);
const initialMode = MODES.some((mode) => mode.id === savedSetup?.mode) ? savedSetup.mode : "simulation";

const state = {
  phase: "intro", // intro | active | results | review
  setup: {
    mode: initialMode,
    tiers: normalizeTiers(savedSetup?.tiers).length ? normalizeTiers(savedSetup.tiers) : [1, 2],
    count: COUNT_OPTIONS.includes(savedSetup?.count) ? savedSetup.count : DEFAULT_COUNT,
  },
  session: [],
  sessionInfo: null,
  currentIndex: 0,
  startedAt: null,
  elapsedSeconds: 0,
  answers: new Map(),
  nav: { filter: "all", page: null, open: false }, // question navigator: filter, manual page, mobile sheet
};

const formatTime = (totalSeconds) => {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return faDigits(`${minutes}:${seconds}`);
};

function getStats() {
  let correct = 0;
  let wrong = 0;
  for (const question of state.session) {
    const answerId = state.answers.get(question.id);
    if (!answerId) continue;
    if (question.correctOptionId === answerId) correct += 1;
    else wrong += 1;
  }
  return { correct, wrong, answered: correct + wrong, unanswered: state.session.length - correct - wrong };
}

function questionState(question) {
  const selected = state.answers.get(question.id);
  if (!selected) return "unanswered";
  return selected === question.correctOptionId ? "correct" : "wrong";
}

function tierLabel(tiers) {
  const list = normalizeTiers(tiers);
  if (list.length === TIERS.length) return "همهٔ سطح‌ها";
  if (list.length === 1) return tierName(list[0]);
  const numbers = list.map(faNumber);
  return `سطح‌های ${numbers.slice(0, -1).join("، ")} و ${numbers.at(-1)}`;
}

function sessionTitle() {
  if (state.sessionInfo?.mode === "simulation") return "آزمون شبیه‌سازی‌شده";
  return `تمرین ${tierLabel(state.sessionInfo?.tiers ?? [])}`;
}

/* ---------- Setup (start) page ---------- */

function presetMatching(tiers) {
  const key = normalizeTiers(tiers).join(",");
  return ["essentials", "serious", "complete"].find((id) => PRESETS[id].tiers.join(",") === key) ?? "custom";
}

function setupSummary() {
  const { mode, tiers, count } = state.setup;
  if (mode === "simulation") {
    const tagged = questionBank.filter((question) => Number.isInteger(question.chapterId));
    return { available: tagged.length, delivered: Math.min(SIMULATION.size, tagged.length), shortfall: 0 };
  }
  const available = poolForTiers(questionBank, tiers).length;
  return { available, ...resolveCount(count, available) };
}

function renderModeCards() {
  const current = state.setup.mode;
  return `<div class="mode-grid" role="radiogroup" aria-label="نوع آزمون">
    ${MODES.map((mode) => `<button type="button" class="mode-card ${mode.id === "simulation" ? "mode-featured" : ""} ${mode.id === current ? "is-selected" : ""}" role="radio" aria-checked="${mode.id === current}" data-mode="${mode.id}">
      <span class="mode-radio" aria-hidden="true"></span>
      <span class="mode-text"><strong>${mode.title}${mode.badge ? ` <em>${mode.badge}</em>` : ""}</strong><span>${mode.copy}</span></span>
    </button>`).join("")}
  </div>`;
}

function renderTierCards() {
  const selected = new Set(state.setup.tiers);
  return `<div class="tier-grid" role="group" aria-label="سطح اهمیت سؤال‌ها">
    ${TIERS.map((tier) => `<button type="button" class="tier-card tier-${tier} ${selected.has(tier) ? "is-selected" : ""}" role="checkbox" aria-checked="${selected.has(tier)}" data-tier="${tier}">
      <span class="tier-check" aria-hidden="true"></span>
      <span class="tier-chip tier-${tier}">${tier === 1 ? "★ " : ""}${tierName(tier)}</span>
      <strong>${TIER_META[tier].title}</strong>
      <span class="tier-hint">${TIER_META[tier].hint}</span>
      <span class="tier-count">${faNumber(tierCounts[tier])} سؤال</span>
    </button>`).join("")}
  </div>`;
}

function renderCountSelector() {
  return `<div class="count-options" role="radiogroup" aria-label="تعداد سؤال">
    ${COUNT_OPTIONS.map((option) => `<button type="button" class="count-option ${state.setup.count === option ? "is-selected" : ""}" role="radio" aria-checked="${state.setup.count === option}" data-count="${option}">${option === "all" ? "همه" : faNumber(option)}</button>`).join("")}
  </div>`;
}

function renderSummaryLine() {
  const summary = setupSummary();
  const isSimulation = state.setup.mode === "simulation";
  if (!isSimulation && !state.setup.tiers.length) {
    return { html: `<p class="summary-line is-warning">حداقل یک سطح را انتخاب کنید.</p>`, disabled: true };
  }
  const main = isSimulation
    ? `<strong>${faNumber(summary.delivered)} سؤال</strong> از ${faNumber(summary.available)} سؤال بانک، با ترکیب ۲۰ + ۱۰ انتخاب خواهد شد.`
    : `<strong>${faNumber(summary.delivered)} سؤال</strong> از ${faNumber(summary.available)} سؤال ${tierLabel(state.setup.tiers)} انتخاب خواهد شد.`;
  const note = summary.shortfall
    ? `<span class="summary-note">در سطح‌های انتخاب‌شده فقط ${faNumber(summary.available)} سؤال وجود دارد؛ آزمون با همهٔ همین سؤال‌ها ساخته می‌شود.</span>`
    : "";
  return { html: `<p class="summary-line"><span>${main}</span>${note}</p>`, disabled: summary.delivered === 0 };
}

function renderIntro() {
  const isSimulation = state.setup.mode === "simulation";
  const summary = renderSummaryLine();
  const referencedCount = questionBank.filter((question) => question.bookPage).length;
  app.innerHTML = `
    <section class="intro-page setup-page" aria-labelledby="exam-title">
      <div class="setup-topbar"><div class="brand">${BRAND_LOGO}<span>آزمون‌یار</span></div><div class="topbar-actions"><div class="install-slot">${renderInstallButton()}</div>${renderThemeToggle()}</div></div>
      <div class="setup-card">
        <header class="setup-hero">
          <p class="eyebrow">آماده‌سازی آزمون</p>
          <h1 id="exam-title">آزمون آیین‌نامه رانندگی</h1>
          <p class="intro-copy">سؤال‌های واقعی نمونه‌آزمون‌ها، سطح‌بندی‌شده برای اینکه وقتت را اول روی مهم‌ترین‌ها بگذاری. بعد از هر پاسخ، نتیجه و منبع کتاب را همان‌جا می‌بینی.</p>
          <div class="exam-facts" aria-label="اطلاعات بانک سؤال">
            <div><strong>${faNumber(questionBank.length)}</strong><span>سؤال واقعی</span></div>
            <div><strong>${faNumber(tierCounts[1])}</strong><span>سؤال سطح ۱</span></div>
            <div><strong>${faNumber(referencedCount)}</strong><span>سؤال با منبع کتاب</span></div>
          </div>
        </header>

        <section class="setup-section" aria-labelledby="mode-title">
          <div class="section-head"><h2 id="mode-title">نوع آزمون</h2></div>
          ${renderModeCards()}
        </section>

        ${isSimulation ? `
        <p class="setup-info">در آزمون شبیه‌سازی‌شده سؤال‌ها از همهٔ سطح‌ها انتخاب می‌شوند، ولی سؤال‌های سطح ۱ و ۲ شانس بیشتری دارند؛ هر بار ترکیب تازه‌ای می‌سازی.</p>` : `
        <section class="setup-section" aria-labelledby="tier-title">
          <div class="section-head"><h2 id="tier-title">سطح اهمیت سؤال‌ها</h2><span>می‌توانی چند سطح را با هم انتخاب کنی</span></div>
          ${renderTierCards()}
        </section>
        <section class="setup-section" aria-labelledby="count-title">
          <div class="section-head"><h2 id="count-title">تعداد سؤال</h2><span>آزمون اصلی ۳۰ سؤال دارد</span></div>
          ${renderCountSelector()}
        </section>`}

        <footer class="setup-footer">
          ${summary.html}
          <button class="button button-primary button-large" data-action="start" ${summary.disabled ? "disabled" : ""}>شروع آزمون <span>←</span></button>
        </footer>
        <p class="tier-disclaimer">سطح‌ها احتمال رسمی نیستند؛ اولویت مطالعه‌اند که از تکرار هر سؤال در نمونه‌آزمون‌های مستقل و جایگاه موضوعش در کتاب آموزشی به دست آمده‌اند. تایمر فقط پس از شروع آزمون فعال می‌شود.</p>
      </div>
    </section>`;
}

/* ---------- Exam ---------- */

function renderHeader(stats) {
  const total = state.session.length;
  const progress = Math.round((stats.answered / total) * 100);
  return `
    <header class="exam-header">
      <div class="topbar"><a href="#" class="brand" data-action="exit">${BRAND_LOGO}<span>آزمون‌یار</span></a><span class="exam-name">${sessionTitle()}</span>${renderThemeToggle()}<button class="text-button" data-action="finish">${state.phase === "review" ? "بازگشت به نتیجه" : "پایان آزمون"}</button></div>
      <div class="metrics" aria-label="وضعیت آزمون">
        <div class="metric metric-question"><span>سؤال</span><strong>${faNumber(state.currentIndex + 1)} <em>از</em> ${faNumber(total)}</strong></div>
        <div class="metric metric-correct"><span>✓ صحیح</span><strong>${faNumber(stats.correct)}</strong></div>
        <div class="metric metric-wrong"><span>× غلط</span><strong>${faNumber(stats.wrong)}</strong></div>
        <div class="metric metric-unanswered"><span>بدون پاسخ</span><strong>${faNumber(stats.unanswered)}</strong></div>
        <div class="metric metric-time"><span>زمان</span><strong id="timer">${formatTime(state.elapsedSeconds)}</strong></div>
      </div>
      <div class="progress-track" aria-label="${progress} درصد پاسخ داده شده"><div class="progress-value" style="width:${progress}%"></div></div>
    </header>`;
}

/* ---------- Question navigator ---------- */

function matchesNavFilter(question, filter) {
  const status = questionState(question);
  if (filter === "unanswered") return status === "unanswered";
  if (filter === "wrong") return status === "wrong";
  if (filter === "important") return question.tier === 1;
  return true;
}

function navigatorModel() {
  const entries = state.session.map((question, index) => ({ question, index, status: questionState(question) }));
  const counts = Object.fromEntries(NAV_FILTERS.map(({ id }) => [id, entries.filter((entry) => matchesNavFilter(entry.question, id)).length]));
  const visible = entries.filter((entry) => matchesNavFilter(entry.question, state.nav.filter));
  const pageCount = Math.max(1, Math.ceil(visible.length / NAV_PAGE_SIZE));
  const currentPosition = visible.findIndex((entry) => entry.index === state.currentIndex);
  const followPage = currentPosition >= 0 ? Math.floor(currentPosition / NAV_PAGE_SIZE) : 0;
  const page = Math.min(pageCount - 1, Math.max(0, state.nav.page ?? followPage));
  return { counts, page, pageCount, cells: visible.slice(page * NAV_PAGE_SIZE, (page + 1) * NAV_PAGE_SIZE) };
}

/** Next unanswered question (next wrong one while reviewing), wrapping around; null when none is left. */
function jumpTarget() {
  const wanted = state.phase === "review" ? "wrong" : "unanswered";
  for (let step = 1; step < state.session.length; step += 1) {
    const index = (state.currentIndex + step) % state.session.length;
    if (questionState(state.session[index]) === wanted) return index;
  }
  return null;
}

const jumpLabel = () => (state.phase === "review" ? "غلط بعدی" : "بی‌پاسخ بعدی");

function renderProgressSegments(stats) {
  const share = (value) => ((100 * value) / state.session.length).toFixed(2);
  return `<div class="nav-progress" role="img" aria-label="${faNumber(stats.correct)} صحیح، ${faNumber(stats.wrong)} غلط، ${faNumber(stats.unanswered)} بدون پاسخ"><i class="is-correct" style="width:${share(stats.correct)}%"></i><i class="is-wrong" style="width:${share(stats.wrong)}%"></i></div>`;
}

const levelMark = (tier) => (tier === 1 ? "★" : faNumber(tier));

function renderNavCell({ question, index, status }) {
  const isCurrent = index === state.currentIndex;
  const isMissed = state.phase === "review" && status === "unanswered";
  const hasLevel = TIERS.includes(question.tier);
  const label = [`سؤال ${faNumber(index + 1)}`, isMissed ? "بی‌پاسخ مانده" : STATUS_LABEL[status], hasLevel ? `${tierName(question.tier)}، ${TIER_META[question.tier].title}` : ""].filter(Boolean).join("، ");
  return `<button type="button" class="nav-cell is-${status}${isCurrent ? " is-current" : ""}${isMissed ? " is-missed" : ""}" data-question-index="${index}" aria-label="${label}"${isCurrent ? ' aria-current="step"' : ""}>${faNumber(index + 1)}${hasLevel ? `<i class="level-mark tier-${question.tier}" aria-hidden="true">${levelMark(question.tier)}</i>` : ""}</button>`;
}

/** Compact sticky bar shown on small screens; opens the full navigator as a bottom sheet. */
function renderNavBar(stats) {
  const target = jumpTarget();
  return `<div class="nav-bar">
    ${renderProgressSegments(stats)}
    <div class="nav-bar-row">
      <div class="nav-bar-text"><strong>سؤال ${faNumber(state.currentIndex + 1)} <em>از ${faNumber(state.session.length)}</em></strong><span>${faNumber(stats.answered)} پاسخ داده شده</span></div>
      <div class="nav-bar-actions">
        <button type="button" class="nav-bar-jump" data-action="nav-jump" ${target === null ? "disabled" : ""}>${jumpLabel()}</button>
        <button type="button" class="nav-bar-open" data-action="nav-open" aria-controls="question-navigator" aria-expanded="${state.nav.open}" aria-label="فهرست همهٔ سؤال‌ها"><span class="grid-icon" aria-hidden="true"></span>فهرست</button>
      </div>
    </div>
  </div>`;
}

function renderNavigator(stats) {
  const model = navigatorModel();
  const target = jumpTarget();
  const isOpen = state.nav.open;
  const isReview = state.phase === "review";
  return `<div class="nav-backdrop${isOpen ? " is-open" : ""}" data-action="nav-close" aria-hidden="true"></div>
  <aside class="exam-nav${isOpen ? " is-open" : ""}" id="question-navigator" aria-label="ناوبری سؤال‌ها"${isOpen ? ' role="dialog" aria-modal="true"' : ""}>
    <header class="nav-head">
      <div><h2>ناوبری سؤال‌ها</h2><p>${faNumber(stats.answered)} از ${faNumber(state.session.length)} پاسخ داده شده</p></div>
      <button type="button" class="nav-close" data-action="nav-close" aria-label="بستن فهرست سؤال‌ها">×</button>
    </header>
    ${renderProgressSegments(stats)}
    <div class="nav-filters" role="radiogroup" aria-label="نمایش سؤال‌ها">
      ${NAV_FILTERS.map(({ id, label }) => {
        const active = state.nav.filter === id;
        const empty = !active && id !== "all" && model.counts[id] === 0;
        return `<button type="button" class="nav-filter${active ? " is-active" : ""}${id === "important" ? " is-important" : ""}" role="radio" aria-checked="${active}" data-nav-filter="${id}" ${empty ? "disabled" : ""}>${label}<b>${faNumber(model.counts[id])}</b></button>`;
      }).join("")}
    </div>
    ${model.cells.length ? `<div class="nav-grid">${model.cells.map(renderNavCell).join("")}</div>` : `<p class="nav-empty">سؤالی در این دسته نیست.</p>`}
    ${model.pageCount > 1 ? `<div class="nav-pager">
      <button type="button" data-nav-page="${model.page - 1}" aria-label="صفحهٔ قبل" ${model.page === 0 ? "disabled" : ""}>→</button>
      <span>صفحهٔ ${faNumber(model.page + 1)} از ${faNumber(model.pageCount)}</span>
      <button type="button" data-nav-page="${model.page + 1}" aria-label="صفحهٔ بعد" ${model.page === model.pageCount - 1 ? "disabled" : ""}>←</button>
    </div>` : ""}
    <button type="button" class="nav-jump" data-action="nav-jump" ${target === null ? "disabled" : ""}>${target === null ? (isReview ? "پاسخ غلطی نمانده" : "همهٔ سؤال‌ها پاسخ داده شده") : `${jumpLabel()} <span aria-hidden="true">←</span>`}</button>
    <div class="nav-legend" aria-hidden="true">
      ${isReview ? '<span><i class="swatch is-missed"></i>بی‌پاسخ مانده</span>' : '<span><i class="swatch is-unanswered"></i>بدون پاسخ</span>'}<span><i class="swatch is-correct"></i>صحیح</span><span><i class="swatch is-wrong"></i>غلط</span>
      <span class="legend-levels">سطح اهمیت:${TIERS.map((tier) => `<i class="level-mark tier-${tier}" title="${tierName(tier)}: ${TIER_META[tier].title}">${levelMark(tier)}</i>`).join("")}<small>از خیلی مهم تا تکمیلی</small></span>
    </div>
  </aside>`;
}

function renderTierBadge(question) {
  if (!TIERS.includes(question.tier)) return "";
  return `<span class="tier-badge tier-${question.tier}" title="سطح اهمیت: ${TIER_META[question.tier].title}"><b>${question.tier === 1 ? "★ " : ""}${tierName(question.tier)}</b><span>${TIER_META[question.tier].title}</span></span>`;
}

/**
 * Study panel shown after answering: a short study hint and the book source, each collapsible.
 * Both start open after a wrong answer (or an unanswered question in review) and closed after a correct one.
 */
function renderStudyPanel(question, expanded) {
  const hint = questionHints[question.id] ?? question.explanation ?? null;
  const hasPage = Number.isInteger(question.bookPage) && question.referenceConfidence !== "not_found";
  if (!hint && !hasPage) return "";
  const open = expanded ? " open" : "";
  const tentative = question.referenceConfidence === "low";
  // Separator is a Persian comma: a middle dot would read like the Persian digit zero (۰).
  const location = `${question.chapterId ? `فصل ${faNumber(question.chapterId)}، ` : ""}صفحهٔ ${faNumber(question.bookPage)}`;
  const secondary = (question.secondaryReferences ?? []).filter((reference) => Number.isInteger(reference.bookPage));
  return `<section class="study-panel" aria-label="نکتهٔ آموزشی و منبع کتاب">
    ${hint ? `<details class="study-item study-hint"${open}>
      <summary><span class="study-icon" aria-hidden="true">💡</span><span class="study-title">نکتهٔ آموزشی</span><span class="study-chevron" aria-hidden="true"></span></summary>
      <p class="study-content">${escapeHtml(hint)}</p>
    </details>` : ""}
    ${hasPage ? `<details class="study-item study-source${tentative ? " is-tentative" : ""}"${open}>
      <summary><span class="study-icon" aria-hidden="true">📖</span><span class="study-title">${tentative ? "منبع احتمالی در کتاب" : "منبع در کتاب"}</span><span class="study-location">${location}</span><span class="study-chevron" aria-hidden="true"></span></summary>
      <div class="study-content">
        ${question.bookReference ? `<p class="study-section">${escapeHtml(question.bookReference)}</p>` : ""}
        ${question.supportingText ? `<blockquote>${escapeHtml(question.supportingText)}</blockquote>` : ""}
        ${secondary.length ? `<p class="study-secondary">همچنین: ${secondary.map((reference) => `صفحهٔ ${faNumber(reference.bookPage)}`).join("، ")}</p>` : ""}
        ${tentative ? `<p class="study-caution">ارتباط این صفحه با سؤال قطعی نیست؛ صفحه‌های مجاور را هم مرور کنید.</p>` : ""}
      </div>
    </details>` : ""}
  </section>`;
}

function renderQuestion(question) {
  const selected = state.answers.get(question.id);
  const isReview = state.phase === "review";
  const isLocked = Boolean(selected) || isReview;
  const isLast = state.currentIndex === state.session.length - 1;
  return `<article class="question-card">
    <div class="question-heading"><div><p class="eyebrow">سؤال ${faNumber(state.currentIndex + 1)}</p><h1>${question.text}</h1></div>${renderTierBadge(question)}</div>
    ${question.image ? `<figure class="question-image"><img src="${question.image.src}" alt="${escapeHtml(question.image.alt)}" decoding="async" /></figure>` : ""}
    <div class="options" role="radiogroup" aria-label="گزینه‌های پاسخ">
      ${question.options.map((option, index) => {
        const status = !isLocked ? "" : option.id === question.correctOptionId ? "is-correct" : option.id === selected ? "is-wrong" : "is-muted";
        const marker = ["الف", "ب", "ج", "د"][index];
        return `<button class="option ${status}" data-option-id="${option.id}" ${isLocked ? "disabled" : ""} aria-pressed="${selected === option.id}"><span class="option-letter">${marker}</span><span>${option.text}</span>${status === "is-correct" ? '<b>✓</b>' : status === "is-wrong" ? '<b>×</b>' : ""}</button>`;
      }).join("")}
    </div>
    ${isLocked ? renderStudyPanel(question, selected !== question.correctOptionId) : ""}
    <footer class="question-actions"><button class="button button-secondary" data-action="previous" ${state.currentIndex === 0 ? "disabled" : ""}>→ سؤال قبلی</button><span>${selected ? '<span class="locked-state">پاسخ ثبت و قفل شد</span>' : isReview ? '<span class="review-state">بدون پاسخ — گزینهٔ صحیح مشخص شده است</span>' : "یک گزینه را انتخاب کنید"}</span><button class="button button-primary" data-action="next" ${isLast ? "disabled" : ""}>سؤال بعدی ←</button></footer>
  </article>`;
}

function prefetchNextImage() {
  const next = state.session[state.currentIndex + 1];
  if (next?.image?.src) {
    const image = new Image();
    image.decoding = "async";
    image.src = next.image.src;
  }
}

function renderExam() {
  const stats = getStats();
  app.innerHTML = `${renderHeader(stats)}<div class="exam-layout">${renderNavBar(stats)}<main class="exam-main">${renderQuestion(state.session[state.currentIndex])}</main>${renderNavigator(stats)}</div>`;
  prefetchNextImage();
}

/* ---------- Results ---------- */

function tierBreakdown() {
  return TIERS.map((tier) => {
    const questions = state.session.filter((question) => question.tier === tier);
    const correct = questions.filter((question) => state.answers.get(question.id) === question.correctOptionId).length;
    return { tier, total: questions.length, correct };
  }).filter((row) => row.total > 0);
}

function renderResults() {
  const stats = getStats();
  const total = state.session.length;
  const percentage = Math.round((stats.correct / total) * 100);
  const breakdown = tierBreakdown();
  app.innerHTML = `<section class="results-page"><div class="setup-topbar"><div class="brand">${BRAND_LOGO}<span>آزمون‌یار</span></div>${renderThemeToggle()}</div><div class="results-card"><div class="result-icon">${percentage >= 50 ? "✓" : "!"}</div><p class="eyebrow">نتیجهٔ ${sessionTitle()}</p><h1>آزمون شما به پایان رسید</h1><p class="result-copy">${stats.answered === total ? "همهٔ سؤال‌ها پاسخ داده شده‌اند." : "می‌توانید پاسخ‌های ثبت‌شده و سؤال‌های بدون پاسخ را مرور کنید."}</p><div class="score-ring" style="--score:${percentage}"><strong>${faNumber(percentage)}٪</strong><span>پاسخ صحیح</span></div><div class="result-stats"><div><strong>${faNumber(total)}</strong><span>کل سؤال‌ها</span></div><div class="correct"><strong>${faNumber(stats.correct)}</strong><span>صحیح</span></div><div class="wrong"><strong>${faNumber(stats.wrong)}</strong><span>غلط</span></div><div><strong>${faNumber(stats.unanswered)}</strong><span>بدون پاسخ</span></div><div><strong>${formatTime(state.elapsedSeconds)}</strong><span>زمان صرف‌شده</span></div></div>
    ${breakdown.length > 1 || state.sessionInfo?.mode === "simulation" ? `<div class="tier-breakdown" aria-label="عملکرد بر اساس سطح"><p class="eyebrow">عملکرد بر اساس سطح</p>${breakdown.map((row) => `<div class="breakdown-row"><span class="tier-chip tier-${row.tier}">${row.tier === 1 ? "★ " : ""}${tierName(row.tier)}</span><div class="breakdown-bar"><i class="tier-${row.tier}" style="width:${Math.round((row.correct / row.total) * 100)}%"></i></div><strong>${faNumber(row.correct)} از ${faNumber(row.total)}</strong></div>`).join("")}</div>` : ""}
    <div class="results-actions"><button class="button button-primary button-large" data-action="review">مشاهدهٔ پاسخ‌ها <span>←</span></button><button class="button button-secondary button-large" data-action="new-exam">آزمون جدید</button></div></div></section>`;
}

/* ---------- Flow ---------- */

/** After jumping to another question, bring its card into view below the sticky bars. */
function revealQuestionCard() {
  const card = document.querySelector(".question-card");
  if (!card) return;
  const stickyHeight = [...document.querySelectorAll(".exam-header, .nav-bar")]
    .filter((element) => getComputedStyle(element).position === "sticky")
    .reduce((sum, element) => sum + element.offsetHeight, 0);
  const top = card.getBoundingClientRect().top;
  if (top < stickyHeight) window.scrollTo({ top: window.scrollY + top - stickyHeight - 12, behavior: "smooth" });
}

function render(preserveScroll = false, { revealQuestion = false } = {}) {
  const scrollPosition = preserveScroll ? window.scrollY : 0;
  if (state.phase === "intro") renderIntro();
  else if (state.phase === "results") renderResults();
  else renderExam();
  saveSession();
  document.documentElement.classList.toggle("nav-sheet-open", state.nav.open && (state.phase === "active" || state.phase === "review"));
  window.requestAnimationFrame(() => {
    if (preserveScroll) window.scrollTo({ top: scrollPosition });
    if (revealQuestion) revealQuestionCard();
  });
}

/** Opens / closes the navigator bottom sheet on small screens without re-rendering, so it animates. */
function setNavigatorOpen(open) {
  state.nav.open = open;
  const panel = document.querySelector(".exam-nav");
  const opener = document.querySelector(".nav-bar-open");
  panel?.classList.toggle("is-open", open);
  document.querySelector(".nav-backdrop")?.classList.toggle("is-open", open);
  if (open) {
    panel?.setAttribute("role", "dialog");
    panel?.setAttribute("aria-modal", "true");
  } else {
    panel?.removeAttribute("role");
    panel?.removeAttribute("aria-modal");
  }
  opener?.setAttribute("aria-expanded", String(open));
  document.documentElement.classList.toggle("nav-sheet-open", open);
  const focusTarget = open ? panel?.querySelector(".nav-cell.is-current") ?? panel?.querySelector(".nav-close") : opener;
  focusTarget?.focus({ preventScroll: true });
}

function goToQuestion(index) {
  state.currentIndex = index;
  state.nav.page = null;
  state.nav.open = false;
  render(true, { revealQuestion: true });
}

function resetNavigator() {
  state.nav = { filter: "all", page: null, open: false };
}

function saveSetup() {
  writeStorage(STORAGE_KEYS.setup, state.setup);
}

function recordSeen(questions) {
  const seen = readStorage(STORAGE_KEYS.seen, {});
  for (const question of questions) seen[question.id] = (Number(seen[question.id]) || 0) + 1;
  writeStorage(STORAGE_KEYS.seen, seen);
}

/** Keeps the running exam across reloads: an installed app is often closed by the system while in the background. */
function saveSession() {
  if (state.phase === "intro" || !state.session.length) {
    removeStorage(STORAGE_KEYS.session);
    return;
  }
  const { questions, ...info } = state.sessionInfo ?? {};
  writeStorage(STORAGE_KEYS.session, {
    phase: state.phase,
    ids: state.session.map((question) => question.id),
    answers: [...state.answers],
    currentIndex: state.currentIndex,
    elapsedSeconds: state.phase === "active" ? Math.floor((Date.now() - state.startedAt) / 1000) : state.elapsedSeconds,
    info,
  });
}

function restoreSession() {
  const saved = readStorage(STORAGE_KEYS.session, null);
  if (!saved || !["active", "results", "review"].includes(saved.phase) || !Array.isArray(saved.ids)) return;
  const byId = new Map(questionBank.map((question) => [question.id, question]));
  const questions = saved.ids.map((id) => byId.get(id));
  if (!questions.length || questions.some((question) => !question)) return; // the bank changed: start fresh
  const inSession = new Set(saved.ids);
  const answers = (Array.isArray(saved.answers) ? saved.answers : [])
    .filter(([id, optionId]) => inSession.has(id) && byId.get(id).options.some((option) => option.id === optionId));
  const elapsed = Math.max(0, Math.floor(Number(saved.elapsedSeconds) || 0));
  state.session = questions;
  state.sessionInfo = { ...saved.info, questions };
  state.answers = new Map(answers);
  state.currentIndex = Math.min(Math.max(0, Math.floor(Number(saved.currentIndex) || 0)), questions.length - 1);
  state.elapsedSeconds = elapsed;
  state.startedAt = Date.now() - elapsed * 1000; // the time the app was closed does not count
  state.phase = saved.phase;
}

function startExam() {
  const seen = readStorage(STORAGE_KEYS.seen, {});
  const session = state.setup.mode === "simulation"
    ? buildSimulationSession(questionBank, { seen })
    : buildTierSession(questionBank, { tiers: state.setup.tiers, count: state.setup.count, seen });
  if (!session.questions.length) return;
  recordSeen(session.questions);
  saveSetup();
  state.session = session.questions;
  state.sessionInfo = session;
  state.answers = new Map();
  resetNavigator();
  state.currentIndex = 0;
  state.elapsedSeconds = 0;
  state.phase = "active";
  state.startedAt = Date.now();
  render();
}

function finishExam() {
  if (state.phase === "active") state.elapsedSeconds = Math.floor((Date.now() - state.startedAt) / 1000);
  state.phase = "results";
  render();
}

function selectMode(mode) {
  state.setup.mode = mode;
  if (PRESETS[mode]?.tiers && mode !== "simulation") state.setup.tiers = [...PRESETS[mode].tiers];
  saveSetup();
  render(true);
}

function toggleTier(tier) {
  const tiers = new Set(state.setup.tiers);
  if (tiers.has(tier)) tiers.delete(tier);
  else tiers.add(tier);
  state.setup.tiers = normalizeTiers([...tiers]);
  state.setup.mode = presetMatching(state.setup.tiers);
  saveSetup();
  render(true);
}

app.addEventListener("click", (event) => {
  const target = event.target;
  const action = target.closest("[data-action]")?.dataset.action;
  const questionIndex = target.closest("[data-question-index]")?.dataset.questionIndex;
  const optionId = target.closest("[data-option-id]")?.dataset.optionId;
  const mode = target.closest("[data-mode]")?.dataset.mode;
  const tier = target.closest("[data-tier]")?.dataset.tier;
  const count = target.closest("[data-count]")?.dataset.count;
  const navFilter = target.closest("[data-nav-filter]")?.dataset.navFilter;
  const navPage = target.closest("[data-nav-page]")?.dataset.navPage;

  if (state.phase === "intro") {
    if (mode) { selectMode(mode); return; }
    if (tier) { toggleTier(Number(tier)); return; }
    if (count) { state.setup.count = count === "all" ? "all" : Number(count); saveSetup(); render(true); return; }
  }
  if (questionIndex !== undefined) { goToQuestion(Number(questionIndex)); return; }
  if (navFilter) { state.nav.filter = navFilter; state.nav.page = null; render(true); return; }
  if (navPage !== undefined) { state.nav.page = Number(navPage); render(true); return; }
  if (optionId && state.phase === "active") {
    const question = state.session[state.currentIndex];
    if (!state.answers.has(question.id)) {
      state.answers.set(question.id, optionId);
      if (state.answers.size === state.session.length) finishExam();
      else render(true);
    }
    return;
  }
  if (action === "install") handleInstall();
  if (action === "theme") toggleTheme();
  if (action === "start") startExam();
  if (action === "finish") finishExam();
  if (action === "review") { state.phase = "review"; state.currentIndex = 0; resetNavigator(); render(); }
  if (action === "new-exam") { state.phase = "intro"; render(); }
  if (action === "next" && state.currentIndex < state.session.length - 1) goToQuestion(state.currentIndex + 1);
  if (action === "previous" && state.currentIndex > 0) goToQuestion(state.currentIndex - 1);
  if (action === "nav-jump") { const index = jumpTarget(); if (index !== null) goToQuestion(index); }
  if (action === "nav-open") setNavigatorOpen(true);
  if (action === "nav-close") setNavigatorOpen(false);
  if (action === "exit") { event.preventDefault(); resetNavigator(); state.phase = "intro"; render(); }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.nav.open) setNavigatorOpen(false);
});

// Store the elapsed time when the app goes to the background; it may not come back to the foreground.
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") saveSession();
});
window.addEventListener("pagehide", saveSession);

// The install button appears or changes once the browser reports whether the app can be installed.
onInstallChange(() => {
  const slot = document.querySelector(".install-slot");
  if (slot) slot.innerHTML = renderInstallButton();
});

window.setInterval(() => {
  if (state.phase === "active" && state.startedAt) {
    state.elapsedSeconds = Math.floor((Date.now() - state.startedAt) / 1000);
    const timer = document.querySelector("#timer");
    if (timer) timer.textContent = formatTime(state.elapsedSeconds);
  }
}, 1000);

restoreSession();
render();
// Hints load in the background so they never delay the first screen; refresh an open study panel once they arrive.
hintsLoaded.then(() => {
  const question = state.session[state.currentIndex];
  const showsStudyPanel = question && (state.phase === "review" || (state.phase === "active" && state.answers.has(question.id)));
  if (showsStudyPanel) render(true);
});
