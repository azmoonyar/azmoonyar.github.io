import { questions600Pages82To85 } from "./questions-600-pages-82-85.js";
const find=n=>{const item=questions600Pages82To85.find(q=>q.sources[0].questionNumber===n);if(!item)throw new Error(`Missing verified source question 20/${n}`);return item;};
const pageOf=n=>n<=6||n>=23?47:48;
const clone=(n,sourceNumber)=>{const item=find(sourceNumber),page=pageOf(n);return{...item,id:`q-ayin1-e16-n${String(n).padStart(2,"0")}`,options:item.options.map(o=>({...o})),sources:[{pdf:"ایین نامه-1.pdf",page,questionNumber:n,examNumber:16}],duplicateCount:0};};
export const questionsAyin1Exam16=[
clone(1,30),clone(2,29),clone(3,28),clone(4,27),clone(5,26),clone(6,25),clone(7,24),clone(8,23),clone(9,22),clone(10,21),clone(11,20),clone(12,19),clone(13,18),clone(14,17),clone(15,1),clone(16,2),clone(17,3),clone(18,4),clone(19,5),clone(20,6),clone(21,7),clone(22,8),clone(23,9),clone(24,10),clone(25,11),clone(26,12),clone(27,13),clone(28,14),clone(29,15),clone(30,16),
];
