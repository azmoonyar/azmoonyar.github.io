// Builds the آزمون‌یار logo and every file made from it, from one geometry:
//   - the mark: the letter «آ» drawn as a road running into the distance (alef) under an amber madda,
//     on the indigo brand tile;
//   - SVGs: branding/logo.svg (master), icons/icon.svg (favicon and in-app brand mark);
//   - PNGs: icons/icon-192/512 (rounded), icons/icon-maskable-192/512 (full bleed, safe zone),
//     icons/apple-touch-icon.png, icons/favicon-32.png;
//   - branding/logo-lockup-light.png / -dark.png (mark + name, for the README) and
//     branding/social-preview.png (1280×640, GitHub repository card).
// PNGs are rendered with headless Chrome (set CHROME to override the macOS path); the name uses the
// Vazirmatn web font, so the lockups need an internet connection. No OCR, no font files are shipped.
// usage: node scripts/build_brand_assets.mjs
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const chrome = process.env.CHROME ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const work = fs.mkdtempSync(path.join(os.tmpdir(), "ayeen-brand-"));

// ---- Geometry (512 × 512) -------------------------------------------------------------------------
const TOP = 190; // road top edge
const SLOPE = 0.2293; // road edge slope (x per y); the edges meet just under the madda
const roadWidth = (y) => 48 + 2 * SLOPE * (y - TOP);
const DASHES = [[238, 262], [290, 322], [360, 404], [452, 512], [566, 640]];
const n = (value) => Number(value.toFixed(1));
const road = `M232 ${TOP + 8}Q232 ${TOP} 240 ${TOP}L272 ${TOP}Q280 ${TOP} 280 ${TOP + 8}L${n(280 + SLOPE * (640 - TOP - 8))} 640L${n(232 - SLOPE * (640 - TOP - 8))} 640Z`;
const dashes = DASHES.map(([y1, y2]) => {
  const [a, b] = [roadWidth(y1) * 0.0625, roadWidth(y2) * 0.0625];
  return `M${n(256 - a)} ${y1}L${n(256 + a)} ${y1}L${n(256 + b)} ${y2}L${n(256 - b)} ${y2}Z`;
}).join("");
const MADDA = "M186 132C208 98 236 98 256 122C276 146 304 146 326 112";
const AMBER = "#ffc53d";

const defs = (id) => `<defs>
    <linearGradient id="${id}-bg" x1="0.05" y1="-0.04" x2="0.95" y2="1.04"><stop offset="0" stop-color="#5d6ef0"/><stop offset="1" stop-color="#3546bd"/></linearGradient>
    <radialGradient id="${id}-shine" cx="0.22" cy="0.12" r="0.9"><stop offset="0" stop-color="#fff" stop-opacity=".22"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <mask id="${id}-lanes" maskUnits="userSpaceOnUse" x="-512" y="-512" width="1536" height="1536"><rect x="-512" y="-512" width="1536" height="1536" fill="#fff"/><path d="${dashes}" fill="#000"/></mask>
    <clipPath id="${id}-tile"><rect width="512" height="512" rx="${id === "full" ? 0 : 116}"/></clipPath>
  </defs>`;

/** The mark as SVG. rounded: tile with rounded corners; scale: content size inside the tile (safe zones). */
function markSvg({ rounded = true, scale = 1, size = null } = {}) {
  const id = rounded ? "mark" : "full";
  const radius = rounded ? 116 : 0;
  const content = scale === 1 ? "" : ` transform="translate(256 256) scale(${scale}) translate(-256 -256)"`;
  const dimensions = size ? ` width="${size}" height="${size}"` : "";
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"${dimensions} role="img" aria-label="آزمون‌یار">
  ${defs(id)}
  <g clip-path="url(#${id}-tile)">
    <rect width="512" height="512" rx="${radius}" fill="url(#${id}-bg)"/>
    <rect width="512" height="512" rx="${radius}" fill="url(#${id}-shine)"/>
    <g${content}>
      <path d="${road}" fill="#fff" mask="url(#${id}-lanes)"/>
      <path d="${MADDA}" fill="none" stroke="${AMBER}" stroke-width="32" stroke-linecap="round"/>
    </g>
  </g>
</svg>
`;
}

// ---- Rendering ------------------------------------------------------------------------------------
/** Renders an HTML page with headless Chrome. Chrome writes the screenshot but does not always exit on its
 * own, so the process group is stopped as soon as it reports the file as written. */
function screenshot(html, width, height, output, { scale = 1, transparent = true } = {}) {
  const page = path.join(work, `${path.basename(output)}.html`);
  const rendered = path.join(work, path.basename(output));
  fs.writeFileSync(page, html);
  fs.rmSync(rendered, { force: true });
  const args = [
    "--headless=new", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
    `--user-data-dir=${path.join(work, "profile")}`, `--force-device-scale-factor=${scale}`,
    ...(transparent ? ["--default-background-color=00000000"] : []),
    "--virtual-time-budget=8000", `--window-size=${width},${height}`, `--screenshot=${rendered}`, `file://${page}`,
  ];
  return new Promise((resolve, reject) => {
    const child = spawn(chrome, args, { detached: true, stdio: ["ignore", "pipe", "pipe"] });
    const stop = () => { try { process.kill(-child.pid, "SIGKILL"); } catch { /* already gone */ } };
    const finish = (error) => {
      clearTimeout(timer);
      stop();
      if (error) return reject(error);
      if (!fs.existsSync(rendered)) return reject(new Error(`not rendered: ${output}`));
      // Chrome writes into the temporary folder; the file is copied into the project from here.
      fs.copyFileSync(rendered, path.join(root, output));
      resolve();
    };
    const timer = setTimeout(() => finish(new Error(`timed out: ${output}`)), 90000);
    const watch = (chunk) => { if (String(chunk).includes("bytes written to file")) finish(); };
    child.stdout.on("data", watch);
    child.stderr.on("data", watch);
    child.on("error", finish);
  });
}

const pageFor = (svg, size) => `<!doctype html><html><head><style>html,body{margin:0;background:transparent}svg{display:block;width:${size}px;height:${size}px}</style></head><body>${svg}</body></html>`;
const png = (output, size, options) => screenshot(pageFor(markSvg(options), size), size, size, output);

fs.mkdirSync(path.join(root, "branding"), { recursive: true });
fs.mkdirSync(path.join(root, "icons"), { recursive: true });
fs.writeFileSync(path.join(root, "branding/logo.svg"), markSvg());
fs.writeFileSync(path.join(root, "icons/icon.svg"), markSvg());

await png("icons/icon-192.png", 192);
await png("icons/icon-512.png", 512);
await png("icons/icon-maskable-192.png", 192, { rounded: false, scale: 0.8 });
await png("icons/icon-maskable-512.png", 512, { rounded: false, scale: 0.8 });
await png("icons/apple-touch-icon.png", 180, { rounded: false, scale: 0.9 });
await png("icons/favicon-32.png", 32);

const FONT = `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@500;800&display=block" rel="stylesheet">`;
const lockup = (ink, muted) => `<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">${FONT}<style>
  html,body{margin:0;background:transparent}
  .lockup{display:flex;align-items:center;justify-content:center;gap:26px;box-sizing:border-box;width:600px;height:180px;padding:0 24px;font-family:Vazirmatn,sans-serif}
  .lockup svg{flex:none;width:128px;height:128px;filter:drop-shadow(0 10px 18px rgba(53,70,189,.28))}
  strong{display:block;color:${ink};font-size:66px;font-weight:800;line-height:1.15}
  span{display:block;color:${muted};font-size:25px;font-weight:500;line-height:1.5}
</style></head><body><div class="lockup">${markSvg()}<div><strong>آزمون‌یار</strong><span>تمرین آزمون آیین‌نامهٔ رانندگی</span></div></div></body></html>`;
await screenshot(lockup("#172033", "#6c768b"), 600, 180, "branding/logo-lockup-light.png", { scale: 2 });
await screenshot(lockup("#ffffff", "#c9cfe6"), 600, 180, "branding/logo-lockup-dark.png", { scale: 2 });

const social = `<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">${FONT}<style>
  html,body{margin:0}
  body{width:1280px;height:640px;overflow:hidden;font-family:Vazirmatn,sans-serif;color:#fff;
    background:radial-gradient(circle at 82% 18%,rgba(255,255,255,.16) 0,transparent 42%),linear-gradient(140deg,#5163ec,#2f3dac)}
  .wrap{display:flex;align-items:center;gap:64px;height:100%;padding:0 104px}
  .wrap > svg{flex:none;width:300px;height:300px;filter:drop-shadow(0 26px 40px rgba(15,22,70,.35))}
  h1{margin:0;font-size:112px;font-weight:800;line-height:1.15}
  p{margin:10px 0 34px;color:#dfe3ff;font-size:38px;font-weight:500}
  ul{display:flex;flex-wrap:wrap;gap:14px;margin:0;padding:0;list-style:none}
  li{padding:10px 22px;border:1px solid rgba(255,255,255,.28);border-radius:999px;background:rgba(255,255,255,.12);font-size:25px;font-weight:500}
</style></head><body><div class="wrap">${markSvg()}<div>
  <h1>آزمون‌یار</h1><p>تمرین آزمون آیین‌نامهٔ رانندگی</p>
  <ul><li>سؤال‌های واقعی نمونه‌آزمون‌ها</li><li>سطح‌بندی اهمیت</li><li>نکتهٔ آموزشی و منبع کتاب</li><li>قابل نصب و آفلاین</li></ul>
</div></div></body></html>`;
await screenshot(social, 1280, 640, "branding/social-preview.png", { transparent: false });

fs.rmSync(work, { recursive: true, force: true });
console.log("brand assets written: branding/logo.svg, icons/*, branding/logo-lockup-*.png, branding/social-preview.png");
