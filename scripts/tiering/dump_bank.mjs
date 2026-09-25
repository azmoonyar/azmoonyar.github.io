// Dumps the merged question bank (as the UI sees it) to JSON for the Python tiering pipeline.
// usage: node scripts/tiering/dump_bank.mjs OUTPUT.json
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const { questionBank } = await import(pathToFileURL(path.join(root, "questions.js")).href);
fs.writeFileSync(process.argv[2], JSON.stringify(questionBank, null, 1));
console.log(`dumped ${questionBank.length} questions`);
