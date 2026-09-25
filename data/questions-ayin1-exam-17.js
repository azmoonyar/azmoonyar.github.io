import { questions600Pages76To80 } from "./questions-600-pages-76-80.js";
import { questions600Page81 } from "./questions-600-page-81.js";

const all = [...questions600Pages76To80, ...questions600Page81];
const find = (sourceNumber) => {
  const item = all.find((question) => question.sources[0].examNumber === 19 && question.sources[0].questionNumber === sourceNumber);
  if (!item) throw new Error(`Missing verified source question 19/${sourceNumber}`);
  return item;
};
const pageOf = (number) => number <= 6 || number >= 23 ? 50 : 51;
const clone = (number, sourceNumber) => {
  const item = find(sourceNumber);
  return {
    ...item,
    id: `q-ayin1-e17-n${String(number).padStart(2, "0")}`,
    options: item.options.map((option) => ({ ...option })),
    sources: [{ pdf: "ایین نامه-1.pdf", page: pageOf(number), questionNumber: number, examNumber: 17 }],
    duplicateCount: 0,
  };
};

export const questionsAyin1Exam17 = [
  clone(1, 14), clone(2, 29), clone(3, 28), clone(4, 27), clone(5, 26), clone(6, 25),
  clone(7, 24), clone(8, 23), clone(9, 22), clone(10, 21), clone(11, 20), clone(12, 19),
  clone(13, 30), clone(14, 13), clone(15, 18), clone(16, 17), clone(17, 16), clone(18, 15),
  clone(19, 8), clone(20, 7), clone(21, 12), clone(22, 11), clone(23, 10), clone(24, 9),
  clone(25, 6), clone(26, 5), clone(27, 4), clone(28, 3), clone(29, 2), clone(30, 1),
];
