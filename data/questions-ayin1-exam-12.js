import { questions600Pages51To55 } from "./questions-600-pages-51-55.js";
import { questions600Pages56To60 } from "./questions-600-pages-56-60.js";

const sourceQuestions = [...questions600Pages51To55, ...questions600Pages56To60];
const find = (examNumber, questionNumber) => {
  const item = sourceQuestions.find((question) => {
    const source = question.sources[0];
    return source.examNumber === examNumber && source.questionNumber === questionNumber;
  });
  if (!item) throw new Error(`Missing verified source question ${examNumber}/${questionNumber}`);
  return item;
};

const pageOf = (number) => (number <= 6 || number >= 23 ? 35 : 36);
const clone = (number, examNumber, questionNumber, answerOverride = null) => {
  const item = find(examNumber, questionNumber);
  const page = pageOf(number);
  return {
    ...item,
    id: `q-ayin1-e12-n${String(number).padStart(2, "0")}`,
    options: item.options.map((option) => ({ ...option })),
    correctOptionId: answerOverride ?? item.correctOptionId,
    sources: [{ pdf: "ایین نامه-1.pdf", page, questionNumber: number, examNumber: 12 }],
    duplicateCount: 0,
  };
};

export const questionsAyin1Exam12 = [
  clone(1, 13, 15, "c"),
  clone(2, 13, 30),
  clone(3, 13, 29),
  clone(4, 13, 28),
  clone(5, 13, 27),
  clone(6, 13, 26),
  clone(7, 13, 25),
  clone(8, 13, 24),
  clone(9, 13, 23),
  clone(10, 13, 22),
  clone(11, 13, 21),
  clone(12, 13, 20),
  clone(13, 13, 19),
  clone(14, 13, 18),
  clone(15, 13, 1),
  clone(16, 13, 2),
  clone(17, 13, 3),
  clone(18, 13, 4),
  clone(19, 13, 5),
  clone(20, 13, 6),
  clone(21, 13, 7),
  clone(22, 13, 8),
  clone(23, 13, 9),
  clone(24, 13, 10),
  clone(25, 13, 11),
  clone(26, 13, 12),
  clone(27, 13, 13),
  clone(28, 13, 14),
  clone(29, 13, 16),
  clone(30, 13, 17),
];
