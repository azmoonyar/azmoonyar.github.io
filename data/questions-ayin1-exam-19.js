import { questions600Pages66To70 } from "./questions-600-pages-66-70.js";
import { questions600Pages71To75 } from "./questions-600-pages-71-75.js";

const all = [...questions600Pages66To70, ...questions600Pages71To75];
const find = (sourceNumber) => {
  const item = all.find((question) => question.sources[0].examNumber === 17 && question.sources[0].questionNumber === sourceNumber);
  if (!item) throw new Error(`Missing verified source question 17/${sourceNumber}`);
  return item;
};
const pageOf = (number) => number <= 6 || number >= 23 ? 56 : 57;
const clone = (number, sourceNumber) => {
  const item = find(sourceNumber);
  return {
    ...item,
    id: `q-ayin1-e19-n${String(number).padStart(2, "0")}`,
    options: item.options.map((option) => ({ ...option })),
    sources: [{ pdf: "ایین نامه-1.pdf", page: pageOf(number), questionNumber: number, examNumber: 19 }],
    duplicateCount: 0,
  };
};

export const questionsAyin1Exam19 = [
  clone(1, 15), clone(2, 14), clone(3, 13), clone(4, 12), clone(5, 11), clone(6, 10),
  clone(7, 9), clone(8, 8), clone(9, 7), clone(10, 6), clone(11, 5), clone(12, 4),
  clone(13, 3), clone(14, 2), clone(15, 1), clone(16, 16), clone(17, 17), clone(18, 18),
  clone(19, 19), clone(20, 20), clone(21, 21), clone(22, 22), clone(23, 23), clone(24, 24),
  clone(25, 25), clone(26, 26), clone(27, 27), clone(28, 28), clone(29, 29), clone(30, 30),
];
