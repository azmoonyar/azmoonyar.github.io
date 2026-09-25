const digitMap = new Map([
  ["۰", "0"], ["۱", "1"], ["۲", "2"], ["۳", "3"], ["۴", "4"],
  ["۵", "5"], ["۶", "6"], ["۷", "7"], ["۸", "8"], ["۹", "9"],
  ["٠", "0"], ["١", "1"], ["٢", "2"], ["٣", "3"], ["٤", "4"],
  ["٥", "5"], ["٦", "6"], ["٧", "7"], ["٨", "8"], ["٩", "9"],
]);

const normalizeExactText = (value) => String(value ?? "")
  .normalize("NFKC")
  .replace(/[۰-۹٠-٩]/g, (digit) => digitMap.get(digit))
  .replace(/[يى]/g, "ی")
  .replace(/ك/g, "ک")
  .replace(/[\u200c\u200d\s\p{P}\p{S}]+/gu, "")
  .toLocaleLowerCase("fa");

const duplicateKey = (question) => [
  normalizeExactText(question.text),
  ...question.options.map((option) => normalizeExactText(option.text)),
  question.correctOptionId ?? "unresolved",
].join("|");

export const mergeExactDuplicates = (questions) => {
  const byKey = new Map();
  const merged = [];

  for (const item of questions) {
    const key = duplicateKey(item);
    const existing = byKey.get(key);
    if (!existing) {
      const clone = { ...item, sources: [...item.sources], duplicateCount: item.duplicateCount ?? 0 };
      byKey.set(key, clone);
      merged.push(clone);
      continue;
    }

    for (const source of item.sources) {
      const sourceKey = `${source.pdf}|${source.page}|${source.questionNumber ?? ""}`;
      const alreadyPresent = existing.sources.some((candidate) =>
        `${candidate.pdf}|${candidate.page}|${candidate.questionNumber ?? ""}` === sourceKey
      );
      if (!alreadyPresent) existing.sources.push(source);
    }
    existing.duplicateCount = Math.max(0, existing.sources.length - 1);
  }

  return merged;
};
