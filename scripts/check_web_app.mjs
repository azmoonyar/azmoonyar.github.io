// Checks the installable web app: the manifest and its icons, the page's install tags, and that every file the
// page loads exists. The service worker (sw.js) caches exactly these files for offline use, found by following
// the same references, so a broken reference here would also break opening the app offline.
// usage: node scripts/check_web_app.mjs
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const failures = [];

// Use the service worker's own reference patterns so this check and the offline cache cannot drift apart.
const sw = read("sw.js");
const referencePatterns = Function(`return ${sw.match(/const REFERENCE_PATTERNS = (\[[\s\S]*?\]);/)[1]}`)();
const imagePath = sw.match(/const IMAGE_PATH = "([^"]+)"/)[1];

const queue = ["index.html"];
const seen = new Set();
while (queue.length) {
  const file = queue.shift();
  if (seen.has(file)) continue;
  seen.add(file);
  if (!fs.existsSync(path.join(root, file))) {
    failures.push(`missing file referenced by the app: ${file}`);
    continue;
  }
  if (!/\.(html|js|json)$/.test(file)) continue;
  const text = read(file);
  for (const pattern of referencePatterns) {
    for (const match of text.matchAll(pattern)) {
      const url = new URL(match[1], `https://app.invalid/${file}`);
      if (url.host === "app.invalid" && !url.pathname.includes(imagePath)) queue.push(decodeURIComponent(url.pathname.slice(1)));
    }
  }
}

const pngSize = (file) => {
  const data = fs.readFileSync(path.join(root, file));
  return data.toString("ascii", 1, 4) === "PNG" ? `${data.readUInt32BE(16)}x${data.readUInt32BE(20)}` : null;
};

const manifest = JSON.parse(read("manifest.json"));
for (const field of ["name", "short_name", "start_url", "scope", "display", "icons", "theme_color", "background_color"]) {
  if (!manifest[field]) failures.push(`manifest.json: missing ${field}`);
}
if (!["standalone", "fullscreen", "minimal-ui"].includes(manifest.display)) failures.push(`manifest.json: display "${manifest.display}" is not installable`);
for (const icon of manifest.icons ?? []) {
  const file = icon.src.replace(/^\.\//, "");
  if (!fs.existsSync(path.join(root, file))) failures.push(`manifest icon missing: ${icon.src}`);
  else if (icon.type === "image/png" && pngSize(file) !== icon.sizes) failures.push(`manifest icon ${icon.src}: declared ${icon.sizes}, file is ${pngSize(file)}`);
}
for (const [purpose, size] of [["any", "192x192"], ["any", "512x512"], ["maskable", "512x512"]]) {
  if (!manifest.icons?.some((icon) => (icon.purpose ?? "any").split(" ").includes(purpose) && icon.sizes === size)) failures.push(`manifest.json: no ${size} icon for purpose "${purpose}"`);
}

const page = read("index.html");
for (const [label, pattern] of [
  ["manifest link", /<link rel="manifest" href="\.\/manifest\.json"/],
  ["apple-touch-icon", /<link rel="apple-touch-icon" href="\.\/icons\/apple-touch-icon\.png"/],
  ["theme-color", /<meta name="theme-color"/],
  ["viewport", /<meta name="viewport" content="[^"]*width=device-width/],
]) {
  if (!pattern.test(page)) failures.push(`index.html: no ${label}`);
}
if (pngSize("icons/apple-touch-icon.png") !== "180x180") failures.push("icons/apple-touch-icon.png is not 180x180");
if (!/serviceWorker\.register\("\.\/sw\.js"/.test(read("pwa.js"))) failures.push("pwa.js does not register ./sw.js");

console.log(JSON.stringify({ filesCachedForOffline: seen.size - failures.filter((f) => f.startsWith("missing file")).length, failures }, null, 1));
process.exitCode = failures.length ? 1 : 0;
