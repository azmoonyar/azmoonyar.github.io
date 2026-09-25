/* Installable web app: registers the service worker (sw.js) and drives the "add to home screen" button.
 *
 * Chrome, Edge and Samsung Internet offer their own install dialog (beforeinstallprompt); the button opens it.
 * iOS / iPadOS and other browsers have no such dialog, so the button shows short steps for the browser menu.
 */

const INSTALLED_KEY = "ayeen.installed.v1";
const userAgent = navigator.userAgent;
const isAndroid = /android/i.test(userAgent);
// iPadOS reports itself as a Mac; a touch screen tells them apart.
const isIos = !isAndroid && (/iphone|ipad|ipod/i.test(userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1));
const isMacSafari = !isIos && /macintosh/i.test(userAgent) && Number(userAgent.match(/version\/(\d+)[\d.]* safari/i)?.[1]) >= 17
  && !/chrome|chromium|crios|edg|firefox|fxios|opr/i.test(userAgent);

let deferredPrompt = null;
const listeners = new Set();

function remembered() {
  try {
    return window.localStorage.getItem(INSTALLED_KEY) === "1";
  } catch {
    return false;
  }
}

function remember(installed) {
  try {
    if (installed) window.localStorage.setItem(INSTALLED_KEY, "1");
    else window.localStorage.removeItem(INSTALLED_KEY);
  } catch {
    // Storage may be unavailable; the button then simply stays visible.
  }
}

const notify = () => listeners.forEach((listener) => listener());

export const isStandalone = () => window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;

/**
 * How the app can be installed here: "prompt" (the browser's own dialog), "ios" / "android" / "mac" (steps in the
 * browser menu), or null when it is already installed or the browser cannot install web apps.
 */
export function installMode() {
  if (isStandalone()) return null;
  if (deferredPrompt) return "prompt";
  if (remembered()) return null;
  if (isIos) return "ios";
  if (isAndroid) return "android";
  if (isMacSafari) return "mac";
  return null;
}

/** Phones and tablets add to the home screen; computers install an app. */
export const installLabel = () => (isIos || isAndroid ? "افزودن به صفحهٔ اصلی" : "نصب برنامه");

/** Opens the browser's install dialog when there is one; returns false when steps should be shown instead. */
export async function promptInstall() {
  if (!deferredPrompt) return false;
  const prompt = deferredPrompt;
  deferredPrompt = null;
  prompt.prompt();
  try {
    const { outcome } = await prompt.userChoice;
    if (outcome === "accepted") remember(true);
  } finally {
    notify();
  }
  return true;
}

export function onInstallChange(listener) {
  listeners.add(listener);
}

const ICON_INSTALL = `<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path d="M12 4v10m-4.5-4.5L12 14l4.5-4.5M5 19.5h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const ICON_SHARE = `<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path d="M12 3.5v11M8 7.5l4-4 4 4M8.5 10.5H7a1.5 1.5 0 0 0-1.5 1.5v7A1.5 1.5 0 0 0 7 20.5h10a1.5 1.5 0 0 0 1.5-1.5v-7a1.5 1.5 0 0 0-1.5-1.5h-1.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

const STEPS = {
  ios: {
    title: "افزودن آزمون‌یار به صفحهٔ اصلی",
    steps: [
      `در نوار مرورگر، دکمهٔ اشتراک‌گذاری <span class="install-key">${ICON_SHARE}</span> را بزنید.`,
      `در فهرستی که باز می‌شود «Add to Home Screen» (افزودن به صفحهٔ اصلی) را انتخاب کنید. اگر دیده نمی‌شود، فهرست را کمی بالا بکشید.`,
      `روی «Add» (افزودن) بزنید.`,
    ],
  },
  android: {
    title: "افزودن آزمون‌یار به صفحهٔ اصلی",
    steps: [
      `منوی مرورگر <span class="install-key">⋮</span> را باز کنید.`,
      `«Install app» (نصب برنامه) یا «Add to Home screen» (افزودن به صفحهٔ اصلی) را بزنید.`,
      `نصب را تأیید کنید.`,
    ],
  },
  mac: {
    title: "نصب آزمون‌یار روی مک",
    steps: [`در نوار منوی Safari، منوی «File» را باز کنید.`, `«Add to Dock» را بزنید و تأیید کنید.`],
  },
};

/** The button for the start page, or an empty string when there is nothing to install. */
export function renderInstallButton() {
  if (!installMode()) return "";
  return `<button type="button" class="install-button" data-action="install">${ICON_INSTALL}<span>${installLabel()}</span></button>`;
}

export async function handleInstall() {
  if (await promptInstall()) return;
  const mode = installMode();
  if (STEPS[mode]) showInstallSteps(mode);
}

function showInstallSteps(mode) {
  let dialog = document.querySelector("#install-help");
  if (!dialog) {
    dialog = document.createElement("dialog");
    dialog.id = "install-help";
    dialog.className = "install-sheet";
    dialog.setAttribute("aria-labelledby", "install-help-title");
    // A click on the backdrop lands on the dialog itself (its content fills the box).
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog || event.target.closest("[data-install-close]")) closeDialog(dialog);
    });
    document.body.append(dialog);
  }
  const { title, steps } = STEPS[mode];
  dialog.innerHTML = `<div class="install-sheet-body">
    <h2 id="install-help-title">${title}</h2>
    <p>آزمون‌یار مثل یک برنامه، تمام‌صفحه و بدون نوار مرورگر از صفحهٔ اصلی باز می‌شود و بدون اینترنت هم اجرا می‌شود.</p>
    <ol class="install-steps">${steps.map((step, index) => `<li><span class="install-step-number">${(index + 1).toLocaleString("fa-IR")}</span><span>${step}</span></li>`).join("")}</ol>
    <button type="button" class="button button-primary" data-install-close>متوجه شدم</button>
  </div>`;
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
}

function closeDialog(dialog) {
  if (typeof dialog.close === "function") dialog.close();
  else dialog.removeAttribute("open");
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault(); // keep the dialog for the button instead of the browser's mini banner
  deferredPrompt = event;
  remember(false); // the browser offers installation, so the app is not installed (any more)
  notify();
});

window.addEventListener("appinstalled", () => {
  deferredPrompt = null;
  remember(true);
  notify();
});

window.matchMedia("(display-mode: standalone)").addEventListener?.("change", notify);

// Service workers need a secure context (https, or localhost while developing).
if ("serviceWorker" in navigator && window.isSecureContext) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js", { updateViaCache: "none" }).catch(() => {
      // Without the service worker the app still works online; it just cannot open offline.
    });
  });
}
