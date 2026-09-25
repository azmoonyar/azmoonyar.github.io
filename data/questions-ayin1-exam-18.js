import { questions600Pages71To75 } from "./questions-600-pages-71-75.js";
import { questions600Pages76To80 } from "./questions-600-pages-76-80.js";

const all = [...questions600Pages71To75, ...questions600Pages76To80];
const find = (sourceNumber) => {
  const item = all.find((question) => question.sources[0].examNumber === 18 && question.sources[0].questionNumber === sourceNumber);
  if (!item) throw new Error(`Missing verified source question 18/${sourceNumber}`);
  return item;
};
const pageOf = (number) => number <= 6 || number >= 23 ? 53 : 54;
const clone = (number, sourceNumber) => {
  const item = find(sourceNumber);
  return {
    ...item,
    id: `q-ayin1-e18-n${String(number).padStart(2, "0")}`,
    options: item.options.map((option) => ({ ...option })),
    sources: [{ pdf: "ایین نامه-1.pdf", page: pageOf(number), questionNumber: number, examNumber: 18 }],
    duplicateCount: 0,
  };
};

export const questionsAyin1Exam18 = [
  clone(1, 1), clone(2, 2), clone(3, 4), clone(4, 30), clone(5, 29), clone(6, 28),
  clone(7, 27), clone(8, 26), clone(9, 25), clone(10, 24), clone(11, 23), clone(12, 22),
  clone(13, 21), clone(14, 20), clone(15, 19), clone(16, 18), clone(17, 17), clone(18, 16),
  clone(19, 15), clone(20, 14), clone(21, 13), clone(22, 12), clone(23, 11), clone(24, 10),
  clone(25, 9), clone(26, 8), clone(27, 7), clone(28, 6), clone(29, 5), clone(30, 3),
];
