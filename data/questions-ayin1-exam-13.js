import { questions600Pages46To50 } from "./questions-600-pages-46-50.js";
import { questions600Pages51To55 } from "./questions-600-pages-51-55.js";
import { questions600Pages56To60 } from "./questions-600-pages-56-60.js";

const all=[...questions600Pages46To50,...questions600Pages51To55,...questions600Pages56To60];
const find=(exam,number)=>{const item=all.find(q=>q.sources[0].examNumber===exam&&q.sources[0].questionNumber===number);if(!item)throw new Error(`Missing verified source question ${exam}/${number}`);return item;};
const pageOf=n=>n<=6||n>=23?38:39;
const clone=(n,exam,number,answer=null)=>{const item=find(exam,number),page=pageOf(n);return{...item,id:`q-ayin1-e13-n${String(n).padStart(2,"0")}`,options:item.options.map(o=>({...o})),correctOptionId:answer??item.correctOptionId,sources:[{pdf:"ایین نامه-1.pdf",page,questionNumber:n,examNumber:13}],duplicateCount:0};};
export const questionsAyin1Exam13=[
clone(1,12,30,"b"),clone(2,12,29),clone(3,12,28),clone(4,12,27),clone(5,12,26),clone(6,12,25),
clone(7,12,24),clone(8,12,23),clone(9,13,23),clone(10,12,21),clone(11,13,21),clone(12,13,20),clone(13,13,19),clone(14,13,18),
clone(15,12,1),clone(16,12,2),clone(17,12,3),clone(18,12,4),clone(19,12,5),clone(20,12,6),clone(21,12,7),clone(22,12,8),
clone(23,12,9),clone(24,12,10,"c"),clone(25,12,11),clone(26,12,12),clone(27,12,13),clone(28,12,14),clone(29,12,15),clone(30,12,16),
];
