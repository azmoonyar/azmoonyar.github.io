const optionIds = ["a", "b", "c", "d"];

export const questionsVisualPage15 = [{
  id: "q-visual-e07-p015-n15",
  text: "این شکل چه موردی را هشدار می دهد؟",
  options: [
    "در شرایطی مانند مه یا ریزش باران که شعاع دید کم است باید با سرعتی کمتر از محدوده سرعت قانونی حرکت نمود.",
    "در صورت عبور پیاده یا دوچرخه سوار در جاده سرعت مناسب را انتخاب نمود.",
    "زمانیکه شرایط جاده استاندارد نیست و چاله و دست انداز وجود دارد باید احتیاط نمود.",
    "در نزدیکی مراکز خرید از سرعت خود بکاهید.",
  ].map((text, index) => ({ id: optionIds[index], text })),
  correctOptionId: "c",
  image: {
    src: "./assets/questions/q-src-4-5888983329180487891-1-p015-n15.png",
    alt: "دید راننده از مسیر دارای مانع و دست انداز",
  },
  isImportant: false,
  bookPage: null,
  bookReference: null,
  explanation: null,
  sources: [{ pdf: "4_5888983329180487891-1.pdf", page: 15, questionNumber: 15, examNumber: 7 }],
  duplicateCount: 0,
}];
