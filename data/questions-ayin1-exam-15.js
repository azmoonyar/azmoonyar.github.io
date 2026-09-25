import { questions600Pages16To20 } from "./questions-600-pages-16-20.js";
import { questions600Pages21To25 } from "./questions-600-pages-21-25.js";
import { questions600Pages51To55 } from "./questions-600-pages-51-55.js";
const all=[...questions600Pages16To20,...questions600Pages21To25,...questions600Pages51To55];
const find=(exam,n)=>{const item=all.find(q=>q.sources[0].examNumber===exam&&q.sources[0].questionNumber===n);if(!item)throw new Error(`Missing verified source question ${exam}/${n}`);return item;};
const pageOf=n=>n<=6||n>=23?44:45;
const clone=(n,exam,sourceNumber)=>{const item=find(exam,sourceNumber),page=pageOf(n);return{...item,id:`q-ayin1-e15-n${String(n).padStart(2,"0")}`,options:item.options.map(o=>({...o})),sources:[{pdf:"ایین نامه-1.pdf",page,questionNumber:n,examNumber:15}],duplicateCount:0};};
export const questionsAyin1Exam15=[
clone(1,4,30),clone(2,4,12),clone(3,4,11),clone(4,4,10),clone(5,4,9),clone(6,4,8),clone(7,4,7),clone(8,4,6),clone(9,4,5),clone(10,4,4),clone(11,4,3),clone(12,4,2),clone(13,4,1),clone(14,4,13),clone(15,4,14),clone(16,4,15),clone(17,4,16),clone(18,4,17),clone(19,4,18),clone(20,4,19),clone(21,4,20),clone(22,4,21),clone(23,4,22),clone(24,4,23),clone(25,4,24),clone(26,13,12),clone(27,4,25),clone(28,4,27),clone(29,4,28),clone(30,4,29),
];
