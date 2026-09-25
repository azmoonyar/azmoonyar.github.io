/**
 * Pure exam-session builders (no DOM access) shared by the UI and by the
 * programmatic session simulations in scripts/tiering/simulate-sessions.mjs.
 *
 * Tiers are study-priority ranks derived from the extracted question bank and
 * the reference book; they are not official exam probabilities.
 */

export const TIERS = [1, 2, 3, 4, 5];

export const SIMULATION = Object.freeze({
  size: 30,
  chapterOneCount: 20,
  // Relative selection weight of each tier in the simulated exam.
  tierWeights: Object.freeze({ 1: 6, 2: 4, 3: 2.4, 4: 1.2, 5: 0.6 }),
});

export const PRESETS = Object.freeze({
  simulation: Object.freeze({ tiers: [...TIERS], count: SIMULATION.size }),
  essentials: Object.freeze({ tiers: [1] }),
  serious: Object.freeze({ tiers: [1, 2] }),
  complete: Object.freeze({ tiers: [...TIERS] }),
});

export const COUNT_OPTIONS = [10, 20, 30, 50, 100, "all"];
export const DEFAULT_COUNT = 30;

/** Deterministic PRNG for reproducible simulations; the UI uses Math.random. */
export function mulberry32(seed) {
  let value = seed >>> 0;
  return () => {
    value = (value + 0x6d2b79f5) >>> 0;
    let t = value;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function shuffle(items, rng = Math.random) {
  const result = [...items];
  for (let index = result.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(rng() * (index + 1));
    [result[index], result[swap]] = [result[swap], result[index]];
  }
  return result;
}

export const normalizeTiers = (tiers) =>
  [...new Set((tiers ?? []).map(Number))].filter((tier) => TIERS.includes(tier)).sort();

export function poolForTiers(bank, tiers) {
  const selected = new Set(normalizeTiers(tiers));
  return bank.filter((question) => selected.has(question.tier));
}

export function countByTier(bank) {
  const counts = Object.fromEntries(TIERS.map((tier) => [tier, 0]));
  for (const question of bank) if (counts[question.tier] !== undefined) counts[question.tier] += 1;
  return counts;
}

export function resolveCount(count, available) {
  const requested = count === "all" ? available : Math.max(0, Number(count) || 0);
  return { requested, delivered: Math.min(requested, available), shortfall: Math.max(0, requested - available) };
}

const seenCount = (seen, id) => Number(seen?.[id] ?? 0);

/**
 * Picks `size` questions preferring the least-seen ones, so repeated sessions
 * rotate through the whole pool before any question comes back.
 */
function pickFreshest(pool, size, rng, seen) {
  const decorated = pool.map((question) => ({ question, seen: seenCount(seen, question.id), tieBreak: rng() }));
  decorated.sort((left, right) => left.seen - right.seen || left.tieBreak - right.tieBreak);
  return decorated.slice(0, size).map((item) => item.question);
}

/** Weighted sampling without replacement (Efraimidis–Spirakis keys). */
function pickWeighted(pool, size, rng, weightOf) {
  return pool
    .map((question) => {
      const weight = Math.max(weightOf(question), 1e-9);
      return { question, key: Math.log(Math.max(rng(), 1e-12)) / weight };
    })
    .sort((left, right) => right.key - left.key)
    .slice(0, size)
    .map((item) => item.question);
}

export function buildTierSession(bank, { tiers, count = DEFAULT_COUNT, rng = Math.random, seen = {} } = {}) {
  const pool = poolForTiers(bank, tiers);
  const { requested, delivered, shortfall } = resolveCount(count, pool.length);
  const questions = shuffle(pickFreshest(pool, delivered, rng, seen), rng);
  return { mode: "tiers", tiers: normalizeTiers(tiers), available: pool.length, requested, delivered, shortfall, questions };
}

export function buildSimulationSession(bank, { rng = Math.random, seen = {}, config = SIMULATION } = {}) {
  const weightOf = (question) => (config.tierWeights[question.tier] ?? 0) / (1 + seenCount(seen, question.id));
  const chapterOne = bank.filter((question) => question.chapterId === 1);
  const otherChapters = bank.filter((question) => Number.isInteger(question.chapterId) && question.chapterId !== 1);
  const chapterOneTarget = Math.min(config.chapterOneCount, chapterOne.length);
  const otherTarget = Math.min(config.size - chapterOneTarget, otherChapters.length);
  const pickedChapterOne = pickWeighted(chapterOne, chapterOneTarget, rng, weightOf);
  const pickedOthers = pickWeighted(otherChapters, otherTarget, rng, weightOf);
  let questions = [...pickedChapterOne, ...pickedOthers];

  // If one side lacks data, top up from the remaining chapter-tagged questions.
  if (questions.length < config.size) {
    const used = new Set(questions.map((question) => question.id));
    const remaining = [...chapterOne, ...otherChapters].filter((question) => !used.has(question.id));
    questions = [...questions, ...pickWeighted(remaining, config.size - questions.length, rng, weightOf)];
  }

  return {
    mode: "simulation",
    tiers: [...TIERS],
    available: chapterOne.length + otherChapters.length,
    requested: config.size,
    delivered: questions.length,
    shortfall: Math.max(0, config.size - questions.length),
    chapterOneCount: questions.filter((question) => question.chapterId === 1).length,
    questions: shuffle(questions, rng),
  };
}
