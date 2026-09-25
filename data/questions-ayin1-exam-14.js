import { questions600Pages46To50 } from "./questions-600-pages-46-50.js";

const find=(number)=>{const item=questions600Pages46To50.find(q=>q.sources[0].examNumber===11&&q.sources[0].questionNumber===number);if(!item)throw new Error(`Missing verified source question 11/${number}`);return item;};
const pageOf=n=>n<=6||n>=23?41:42;
const clone=(n,number)=>{const item=find(number),page=pageOf(n);return{...item,id:`q-ayin1-e14-n${String(n).padStart(2,"0")}`,options:item.options.map(o=>({...o})),sources:[{pdf:"ایین نامه-1.pdf",page,questionNumber:n,examNumber:14}],duplicateCount:0};};
export const questionsAyin1Exam14=[
clone(1,15),clone(2,14),clone(3,13),clone(4,12),clone(5,11),clone(6,10),clone(7,9),clone(8,8),clone(9,6),clone(10,7),
clone(11,5),clone(12,4),clone(13,3),clone(14,2),clone(15,1),clone(16,16),clone(17,17),clone(18,18),clone(19,19),clone(20,20),
clone(21,21),clone(22,22),clone(23,23),clone(24,24),clone(25,25),clone(26,26),clone(27,27),clone(28,28),clone(29,29),clone(30,30),
];
