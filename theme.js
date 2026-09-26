/* Light / dark theme. It follows the device setting until the toggle is used; the choice is then remembered.
 * The inline script in index.html sets <html data-theme> before the first paint (same storage key and rule);
 * this module keeps the toggles, the browser's theme colour and later device changes in sync. */

const STORAGE_KEY = "ayeen.theme";
const THEME_COLOR = { light: "#f6f7fb", dark: "#0f1320" };
const deviceDark = window.matchMedia("(prefers-color-scheme: dark)");

const ICON_MOON = `<svg class="icon-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7Z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/></svg>`;
const ICON_SUN = `<svg class="icon-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>`;

function savedTheme() {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value === "dark" || value === "light" ? value : null;
  } catch {
    return null;
  }
}

export const currentTheme = () => (document.documentElement.dataset.theme === "dark" ? "dark" : "light");

const labelFor = (theme) => (theme === "dark" ? "تغییر به حالت روشن" : "تغییر به حالت تاریک");

function apply(theme) {
  document.documentElement.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", THEME_COLOR[theme]);
  for (const button of document.querySelectorAll(".theme-toggle")) {
    button.setAttribute("aria-pressed", String(theme === "dark"));
    button.setAttribute("aria-label", labelFor(theme));
    button.title = labelFor(theme);
  }
}

export function toggleTheme() {
  const next = currentTheme() === "dark" ? "light" : "dark";
  try {
    window.localStorage.setItem(STORAGE_KEY, next);
  } catch {
    // Without storage the choice lasts until the page is reloaded.
  }
  apply(next);
}

/** The toggle button for the page headers (moon in the light theme, sun in the dark theme). */
export function renderThemeToggle() {
  const theme = currentTheme();
  return `<button type="button" class="theme-toggle" data-action="theme" aria-pressed="${theme === "dark"}" aria-label="${labelFor(theme)}" title="${labelFor(theme)}">${ICON_MOON}${ICON_SUN}</button>`;
}

deviceDark.addEventListener?.("change", (event) => {
  if (!savedTheme()) apply(event.matches ? "dark" : "light");
});

apply(savedTheme() ?? (deviceDark.matches ? "dark" : "light"));
