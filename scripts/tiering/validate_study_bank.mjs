// End-to-end validation of the tiered question bank and the exam builders.
// usage: node scripts/tiering/validate_study_bank.mjs   (writes data/study-validation-report.json)
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { contentHash } from "./content-fingerprint.mjs";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const load = (relative) => import(pathToFileURL(path.join(root, relative)).href);
const readJson = (relative) => JSON.parse(fs.readFileSync(path.join(root, relative), "utf8"));

const { questionBank } = await load("questions.js");
const builder = await load("exam-builder.js");
const baseline = readJson("data/question-bank-baseline.json");
const { questionCorrections } = await load("data/question-corrections.js");
const { questionRemovals } = await load("data/question-removals.js");
// The textbook transcription (data/book-pages.json) is copyrighted text and stays out of the public repository.
// Without it, page references are checked against the printed page range only and the excerpt check is skipped.
const hasBookText = fs.existsSync(path.join(root, "data/book-pages.json"));
const bookPages = hasBookText ? new Map(readJson("data/book-pages.json").pages.map((page) => [page.bookPage, page])) : null;
const pageExists = (page) => Number.isInteger(page) && page >= 1 && page <= 220 && (!bookPages || bookPages.has(page));
const structure = readJson("data/book-structure.json");
const chapterOf = (page) => structure.chapters.find((chapter) => page >= chapter.startBookPage && page <= chapter.endBookPage)?.id ?? null;

const checks = [];
const skip = (id, description, reason) => checks.push({ id, description, status: "skipped", reason });
const check = (id, description, failures, details = {}) => {
  checks.push({ id, description, status: failures.length ? "fail" : "pass", failures: failures.length, examples: failures.slice(0, 10), ...details });
};

const loose = (text) => String(text ?? "").normalize("NFKC").replace(/[يى]/g, "ی").replace(/ك/g, "ک")
  .replace(/‌/g, " ").replace(/‍/g, "").replace(/\[کادر\]\s*/g, "").replace(/(^|\s)[-–ـ]+(?=\s)/g, "$1").replace(/\s+/g, " ").trim();
const pageCorpus = new Map([...(bookPages ?? [])].map(([number, page]) => [number, loose([page.text, ...page.headings, ...page.signs.map((s) => s.caption), ...page.figures.map((f) => f.caption ?? "")].join("\n"))]));
const pdfCount = (question) => new Set(question.sources.map((source) => source.pdf)).size;
const byIdForHints = new Set(questionBank.map((question) => question.id));

// ---- Bank integrity ---------------------------------------------------------------------------
const ids = questionBank.map((question) => question.id);
const baselineIds = new Set(Object.keys(baseline.questions));
// The only questions allowed to be missing are the ones removed at the owner's request, each documented
// with its reason in data/question-removals.js.
const removedIds = Object.keys(questionRemovals);
const expectedCount = baselineIds.size - removedIds.length;
check("bank.count", `exactly ${expectedCount} questions (the ${baselineIds.size} of the baseline minus ${removedIds.length} documented removals)`,
  questionBank.length === expectedCount ? [] : [`count=${questionBank.length}`]);
check("bank.uniqueIds", "question ids are unique", ids.length === new Set(ids).size ? [] : ["duplicate ids"]);
check("bank.noNewQuestions", "no question outside the pre-change baseline", ids.filter((id) => !baselineIds.has(id)));
check("bank.noRemovedQuestions", "every baseline question is still present unless its removal is documented",
  [...baselineIds].filter((id) => !ids.includes(id) && !questionRemovals[id]));
check("bank.removalsDocumented", "each documented removal is a baseline question, absent from the bank, with a date and a reason",
  removedIds.filter((id) => !baselineIds.has(id) || ids.includes(id) || !questionRemovals[id].removedAt || !questionRemovals[id].reason),
  { removedQuestions: removedIds });
// A documented correction may only swap the image file; hashing with the documented previous
// image must reproduce the baseline exactly (so text, options, key and sources are untouched).
const asBaseline = (question) => {
  const correction = questionCorrections[question.id];
  if (!correction) return question;
  const restored = "previousImage" in correction ? { ...question, image: correction.previousImage } : { ...question };
  if (correction.previousOptionText) {
    restored.options = question.options.map((option) => (option.id in correction.previousOptionText ? { ...option, text: correction.previousOptionText[option.id] } : option));
  }
  return restored;
};
check("bank.contentUnchanged", "text, options, correct answer, image and provenance unchanged (SHA-256 vs baseline)",
  questionBank.filter((question) => baseline.questions[question.id] && baseline.questions[question.id] !== contentHash(asBaseline(question))).map((question) => question.id),
  { documentedCorrections: Object.keys(questionCorrections) });
check("bank.correctionsDocumented", "documented corrections change only the image or mistyped option text, with evidence and the previous value",
  Object.entries(questionCorrections).filter(([id, correction]) => {
    const question = questionBank.find((item) => item.id === id);
    if (!question || !correction.evidence?.length || !("image" in correction || correction.optionText)) return true;
    const imageOk = !("image" in correction) || ("previousImage" in correction && (correction.image === null
      ? question.image === null
      : question.image?.src === correction.image.src && fs.existsSync(path.join(root, correction.image.src))));
    const textOk = !correction.optionText || Object.entries(correction.optionText).every(([optionId, text]) =>
      optionId in (correction.previousOptionText ?? {}) && question.options.find((option) => option.id === optionId)?.text === text);
    return !imageOk || !textOk;
  }).map(([id]) => id));
check("bank.answersValid", "correctOptionId is one of the four options",
  questionBank.filter((question) => question.options.length !== 4 || !question.options.some((option) => option.id === question.correctOptionId)).map((q) => q.id));

// ---- Tiers ---------------------------------------------------------------------------------------
check("tier.exactlyOne", "every question has exactly one tier in 1..5", questionBank.filter((question) => !builder.TIERS.includes(question.tier)).map((q) => `${q.id}:${q.tier}`));
check("tier.scoreRange", "priorityScore is an integer 0..100", questionBank.filter((q) => !Number.isInteger(q.priorityScore) || q.priorityScore < 0 || q.priorityScore > 100).map((q) => q.id));
check("tier.reasons", "every question records at least one tier reason", questionBank.filter((q) => !q.tierReasons?.length).map((q) => q.id));
const crossSource = questionBank.filter((question) => pdfCount(question) > 1);
check("tier.crossSourceDuplicatesTier1", "all questions merged from >=2 PDFs are Tier 1", crossSource.filter((q) => q.tier !== 1).map((q) => q.id), { crossSourceDuplicates: crossSource.length });
check("tier.importantMatchesTier1", "isImportant (red star) is set exactly for Tier 1", questionBank.filter((q) => q.isImportant !== (q.tier === 1)).map((q) => q.id));
check("tier.provenanceKept", "sources / duplicateCount / sourceCount present", questionBank.filter((q) => !Array.isArray(q.sources) || !q.sources.length || !Number.isInteger(q.duplicateCount) || q.sourceCount !== pdfCount(q)).map((q) => q.id));

// ---- Book references ---------------------------------------------------------------------------
const referenced = questionBank.filter((q) => q.bookPage !== null);
check("ref.validPage", `every book page is a printed page 1..220${hasBookText ? " present in the transcription" : ""}`, referenced.filter((q) => !pageExists(q.bookPage)).map((q) => `${q.id}:${q.bookPage}`));
check("ref.pdfPageMapping", "bookPdfPage = bookPage + 2", referenced.filter((q) => q.bookPdfPage !== q.bookPage + 2).map((q) => q.id));
check("ref.confidenceConsistent", "pages only with high/medium/low; not_found has no page",
  questionBank.filter((q) => (q.bookPage === null) !== (q.referenceConfidence === "not_found") || !["high", "medium", "low", "not_found"].includes(q.referenceConfidence)).map((q) => q.id));
if (hasBookText) check("ref.excerptVerbatim", "supportingText is verbatim from the referenced page",
  referenced.filter((q) => q.supportingText && !pageCorpus.get(q.bookPage)?.includes(loose(q.supportingText).replace(/[.…]+$/, "").trim())).map((q) => q.id));
else skip("ref.excerptVerbatim", "supportingText is verbatim from the referenced page", "data/book-pages.json is not in this checkout");
check("ref.chapterMatchesPage", "chapterId matches the chapter range of bookPage", referenced.filter((q) => q.chapterId !== chapterOf(q.bookPage)).map((q) => q.id));
check("ref.secondaryValid", "secondary references point to existing pages", questionBank.filter((q) => (q.secondaryReferences ?? []).some((r) => !pageExists(r.bookPage) || r.bookPdfPage !== r.bookPage + 2)).map((q) => q.id));

// ---- Study hints -------------------------------------------------------------------------------
const { questionHints } = await load("data/question-hints.js");
check("hints.everyQuestion", "every question has a short study hint", questionBank.filter((q) => !(questionHints[q.id] ?? "").trim()).map((q) => q.id));
check("hints.length", "hints are at most 190 characters", Object.entries(questionHints).filter(([, hint]) => hint.length > 190).map(([id]) => id));
check("hints.noOptionNumbers", "hints never point at an option number/letter",
  Object.entries(questionHints).filter(([, hint]) => /گزینه(ٔ|ی)?\s*(\d|[۰-۹]|الف|ب(?![\u0600-\u06FF])|ج(?![\u0600-\u06FF])|د(?![\u0600-\u06FF]))/.test(hint)).map(([id]) => id));
check("hints.knownIds", "hints exist only for questions of the bank", Object.keys(questionHints).filter((id) => !byIdForHints.has(id)));

// ---- Assets ------------------------------------------------------------------------------------
const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const brokenAssets = questionBank.filter((q) => q.image).filter((q) => {
  const file = path.join(root, q.image.src);
  if (!fs.existsSync(file)) return true;
  const head = Buffer.alloc(8);
  const fd = fs.openSync(file, "r");
  fs.readSync(fd, head, 0, 8, 0);
  fs.closeSync(fd);
  return !head.equals(PNG) || fs.statSync(file).size < 200;
}).map((q) => `${q.id}:${q.image.src}`);
check("assets.imagesExist", "every question image exists and is a valid PNG", brokenAssets, { imageQuestions: questionBank.filter((q) => q.image).length });
check("assets.altText", "every question image has alt text", questionBank.filter((q) => q.image && !q.image.alt).map((q) => q.id));

// ---- Session simulations -----------------------------------------------------------------------
const byId = new Map(questionBank.map((q) => [q.id, q]));
const sessionProblems = (session, { tiers, expected }) => {
  const problems = [];
  const sessionIds = session.questions.map((q) => q.id);
  if (new Set(sessionIds).size !== sessionIds.length) problems.push("duplicate question in session");
  if (expected !== undefined && session.questions.length !== expected) problems.push(`count ${session.questions.length} != ${expected}`);
  for (const question of session.questions) {
    if (!byId.has(question.id)) problems.push(`unknown id ${question.id}`);
    if (tiers && !tiers.includes(question.tier)) problems.push(`tier ${question.tier} outside ${tiers}`);
    if (!question.options.some((option) => option.id === question.correctOptionId)) problems.push(`invalid answer ${question.id}`);
    if (question.image && !fs.existsSync(path.join(root, question.image.src))) problems.push(`missing image ${question.id}`);
  }
  return problems;
};

const simulations = [];
const tierCounts = builder.countByTier(questionBank);
const modes = [
  { name: "Tier 1 only", tiers: [1] },
  { name: "Tier 1 + Tier 2", tiers: [1, 2] },
  { name: "Tier 3 only", tiers: [3] },
  { name: "Tier 2 + Tier 3 + Tier 4", tiers: [2, 3, 4] },
  { name: "All tiers", tiers: [1, 2, 3, 4, 5] },
];
let seed = 1;
for (const mode of modes) {
  const available = mode.tiers.reduce((sum, tier) => sum + tierCounts[tier], 0);
  for (const count of builder.COUNT_OPTIONS) {
    const failures = [];
    const runs = 60;
    for (let run = 0; run < runs; run += 1) {
      const session = builder.buildTierSession(questionBank, { tiers: mode.tiers, count, rng: builder.mulberry32(seed++) });
      const expected = count === "all" ? available : Math.min(count, available);
      failures.push(...sessionProblems(session, { tiers: mode.tiers, expected }));
      if (session.available !== available) failures.push(`available ${session.available} != ${available}`);
    }
    simulations.push({ mode: mode.name, count, runs, available, status: failures.length ? "fail" : "pass", failures: failures.slice(0, 5) });
  }
}

// Standard (simulated) exam: exactly 30 questions, 20 from chapter 1 and 10 from other chapters.
const standard = { runs: 500, failures: [], tierTotals: Object.fromEntries(builder.TIERS.map((t) => [t, 0])), distinctQuestions: new Set(), identicalExams: 0 };
const examKeys = new Set();
for (let run = 0; run < standard.runs; run += 1) {
  const session = builder.buildSimulationSession(questionBank, { rng: builder.mulberry32(10_000 + run) });
  standard.failures.push(...sessionProblems(session, { expected: 30 }));
  const chapterOne = session.questions.filter((q) => q.chapterId === 1).length;
  const others = session.questions.filter((q) => Number.isInteger(q.chapterId) && q.chapterId !== 1).length;
  if (chapterOne !== 20 || others !== 10) standard.failures.push(`chapter split ${chapterOne}+${others}`);
  for (const question of session.questions) {
    standard.tierTotals[question.tier] += 1;
    standard.distinctQuestions.add(question.id);
  }
  const key = session.questions.map((q) => q.id).sort().join(",");
  if (examKeys.has(key)) standard.identicalExams += 1;
  examKeys.add(key);
}
const totalPicked = standard.runs * 30;
const tierSharePercent = Object.fromEntries(Object.entries(standard.tierTotals).map(([tier, n]) => [tier, Math.round((1000 * n) / totalPicked) / 10]));
const bankSharePercent = Object.fromEntries(builder.TIERS.map((tier) => [tier, Math.round((1000 * tierCounts[tier]) / questionBank.length) / 10]));
const weightingOk = tierSharePercent[1] > bankSharePercent[1] && tierSharePercent[5] < bankSharePercent[5] && tierSharePercent[1] > tierSharePercent[4];
simulations.push({
  mode: "Standard exam (simulation)", count: 30, runs: standard.runs,
  status: standard.failures.length || !weightingOk || standard.identicalExams ? "fail" : "pass",
  failures: standard.failures.slice(0, 5), tierSharePercent, bankSharePercent, higherTiersFavoured: weightingOk,
  distinctQuestionsAcrossRuns: standard.distinctQuestions.size, identicalExams: standard.identicalExams,
});

// Rotation: while unseen questions remain, a session never repeats an already-shown one.
const rotation = [];
for (const tiers of [[1], [3], [1, 2]]) {
  const pool = builder.poolForTiers(questionBank, tiers);
  const seen = {};
  const shown = new Set();
  const sessions = Math.ceil(pool.length / 30) + 2;
  let prematureRepeats = 0;
  let coveredAfter = null;
  for (let run = 0; run < sessions; run += 1) {
    const unseenBefore = pool.length - shown.size;
    const session = builder.buildTierSession(questionBank, { tiers, count: 30, rng: builder.mulberry32(500 + run), seen });
    const fresh = session.questions.filter((question) => !shown.has(question.id)).length;
    if (fresh < Math.min(session.questions.length, unseenBefore)) prematureRepeats += 1;
    for (const question of session.questions) {
      shown.add(question.id);
      seen[question.id] = (seen[question.id] ?? 0) + 1;
    }
    if (coveredAfter === null && shown.size === pool.length) coveredAfter = run + 1;
  }
  rotation.push({ tiers, pool: pool.length, sessionsRun: sessions, fullCoverageAfterSessions: coveredAfter, minimumPossible: Math.ceil(pool.length / 30), prematureRepeats,
    status: prematureRepeats === 0 && coveredAfter === Math.ceil(pool.length / 30) ? "pass" : "fail" });
}

check("sessions.tierModes", "tier / multi-tier / all-tier sessions with every count option", simulations.filter((s) => s.status === "fail" && s.mode !== "Standard exam (simulation)").map((s) => `${s.mode} x ${s.count}`));
check("sessions.standardExam", "standard exam: 30 questions, 20 chapter-1 + 10 other, higher tiers favoured, varied", simulations.filter((s) => s.mode === "Standard exam (simulation)" && s.status === "fail").map((s) => JSON.stringify(s.failures)));
check("sessions.rotation", "repeated sessions rotate through the whole pool before repeating", rotation.filter((r) => r.status === "fail").map((r) => JSON.stringify(r)));
const shortfall = builder.buildTierSession(questionBank, { tiers: [1], count: 100000 });
check("sessions.gracefulShortfall", "a count larger than the pool yields the whole pool and reports the shortfall",
  shortfall.questions.length === tierCounts[1] && shortfall.shortfall === 100000 - tierCounts[1] ? [] : ["shortfall not reported"]);

const summary = {
  totalQuestions: questionBank.length,
  tierCounts,
  referenced: referenced.length,
  referenceConfidence: questionBank.reduce((acc, q) => ({ ...acc, [q.referenceConfidence]: (acc[q.referenceConfidence] ?? 0) + 1 }), {}),
  chapterCounts: questionBank.reduce((acc, q) => ({ ...acc, [q.chapterId ?? "unknown"]: (acc[q.chapterId ?? "unknown"] ?? 0) + 1 }), {}),
  checksPassed: checks.filter((c) => c.status === "pass").length,
  checksFailed: checks.filter((c) => c.status === "fail").length,
  checksSkipped: checks.filter((c) => c.status === "skipped").length,
  sessionsSimulated: simulations.reduce((sum, s) => sum + s.runs, 0) + rotation.reduce((sum, r) => sum + r.sessionsRun, 0),
};
const report = { generatedAt: new Date().toISOString(), status: summary.checksFailed ? "fail" : "pass", summary, checks, simulations, rotation };
fs.writeFileSync(path.join(root, "data/study-validation-report.json"), JSON.stringify(report, null, 1) + "\n");
console.log(JSON.stringify(summary, null, 1));
for (const failed of checks.filter((c) => c.status === "fail")) console.log("FAIL", failed.id, failed.failures, JSON.stringify(failed.examples.slice(0, 3)));
process.exitCode = summary.checksFailed ? 1 : 0;
