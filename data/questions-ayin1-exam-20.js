import { questions600Pages66To70 } from "./questions-600-pages-66-70.js";

const find = (sourceNumber) => {
  const item = questions600Pages66To70.find((question) => question.sources[0].examNumber === 16 && question.sources[0].questionNumber === sourceNumber);
  if (!item) throw new Error(`Missing verified source question 16/${sourceNumber}`);
  return item;
};
const pageOf = (number) => number <= 6 || number >= 23 ? 59 : 60;
const clone = (number, sourceNumber) => {
  const item = find(sourceNumber);
  return {
    ...item,
    id: `q-ayin1-e20-n${String(number).padStart(2, "0")}`,
    options: item.options.map((option) => ({ ...option })),
    sources: [{ pdf: "ایین نامه-1.pdf", page: pageOf(number), questionNumber: number, examNumber: 20 }],
    duplicateCount: 0,
  };
};

export const questionsAyin1Exam20 = [
  clone(1, 30), clone(2, 29), clone(3, 28), clone(4, 27), clone(5, 26), clone(6, 25),
  clone(7, 24), clone(8, 23), clone(9, 22), clone(10, 21), clone(11, 20), clone(12, 19),
  clone(13, 18), clone(14, 17), clone(15, 1), clone(16, 2), clone(17, 3), clone(18, 4),
  clone(19, 5), clone(20, 6), clone(21, 7), clone(22, 8), clone(23, 9), clone(24, 10),
  clone(25, 11), clone(26, 12), clone(27, 13), clone(28, 14), clone(29, 15), clone(30, 16),
];
