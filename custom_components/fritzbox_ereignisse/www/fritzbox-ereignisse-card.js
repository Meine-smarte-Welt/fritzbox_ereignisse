// fritzbox-ereignisse-card.js - v1.0.0
//
// Lovelace-Karte für die fritzbox_ereignisse-Integration: zeigt das
// FRITZ!Box-Ereignisprotokoll (sensor.fritzbox_ereignisse_ereignisse,
// Attribut "events") als filterbare, durchsuchbare Liste - mit Tabs je
// Kategorie ("Gruppe", z. B. System/Internetverbindung/Telefonie/WLAN/
// USB-Geräte, siehe const.py:EVENT_GROUP_LABELS in der Integration) und
// einer Volltextsuche. Seit v0.3.0 liefert auch der Text-Rückfall
// (source: "text") dank serverseitiger Text-Heuristik oft schon
// Kategorien - der "keine Kategorien"-Hinweis unten prüft daher direkt
// die tatsächlichen Gruppen der Ereignisse, nicht mehr nur "source". Seit
// v0.4.0 ist "System" dabei server-seitig der universelle Auffang-Wert
// für alles, was keiner der anderen vier Kategorien zugeordnet werden
// kann (siehe Integration, events.py) - dieser Hinweis erscheint daher
// nur noch, wenn wirklich gar keine Meldungstexte vorliegen.
//
// Struktur/Konventionen bewusst an fritzbox-anrufe-card.js angelehnt (siehe
// dortige, ausführlichere Moduldoku): persistente Shadow-Root-Kindknoten
// statt shadowRoot.innerHTML-Ersetzung bei jedem Update, damit ein von
// außen (z. B. card_mod/Theme) in den Shadow-Root injiziertes <style>
// einen Re-Render übersteht, und damit ein Tastaturfokus im Suchfeld beim
// Tippen nicht durch einen kompletten DOM-Rebuild verloren geht.
//
// Feature in v1.0.0 - Farben (grafische Auswahl im Karten-Editor)
// -----------------------------------------------------------------
// Analog zur "Farben"-Sektion in fritzbox-anrufe-card.js (siehe dortige
// Moduldoku für die ausführliche Begründung, warum dies bewusst NICHT über
// <ha-form> gelöst ist): ein natives <details>-Akkordeon im Karten-Editor
// mit einer Zeile je konfigurierbarer Farbe (<input type="color">-Swatch
// plus Textfeld für beliebige CSS-Werte wie var()/rgb()/hsl()), plus
// "Alle Farben zurücksetzen". Übertragen auf diese Karte: eine Farbe für
// den aktiven Tab, eine für alle Zeilen-Icons (einheitlich, überschreibt
// alles andere) sowie je eine Farbe für die Tab-/Zeilen-Icons der fünf
// echten FRITZ!Box-Kategorien (Alle/Telefonie/Internetverbindung/
// USB-Geräte/WLAN/System) - siehe COLOR_EDITOR_FIELDS/CATEGORY_ICON_COLOR_KEYS
// unten. Die Tabs zeigen dafür seit v1.0.0 zusätzlich ein kleines
// Kategorie-Icon (zuvor nur Text) - sonst gäbe es für die Kategorie-
// Icon-Farben in den Tabs kein sichtbares Ziel.
//
// Der Titel der Karte war schon seit v0.1.0 über den Editor-Schalter
// "Titel anzeigen" (show_title) ausblendbar (siehe EDITOR_SCHEMA/
// _updateContent() unten) - keine Änderung in v1.0.0 nötig, hier nur zur
// Klarstellung dokumentiert, da danach ausdrücklich gefragt wurde.

const FILTER_ALL = "alle";

const CONFIG_DEFAULTS = {
  title: "FRITZ!Box Ereignisse",
  show_title: true,
  max_rows: 15,
  // Farben (seit v1.0.0) sind hier absichtlich NICHT gelistet - ein
  // leerer/nicht gesetzter Wert bedeutet "Standardfarbe verwenden" (siehe
  // COLOR_CONFIG_KEYS/sanitizeColor() unten), genau wie in
  // fritzbox-anrufe-card.js.
};

function withDefaults(config) {
  return { ...CONFIG_DEFAULTS, ...(config || {}) };
}

function escapeHtml(value) {
  return String(value === undefined || value === null ? "" : value).replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[c])
  );
}

function formatDateTime(iso) {
  if (!iso) return "";
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const GROUP_ICONS = {
  sys: "mdi:cog-outline",
  system: "mdi:cog-outline",
  internet: "mdi:web",
  dsl: "mdi:web",
  wan: "mdi:web",
  tel: "mdi:phone-outline",
  fon: "mdi:phone-outline",
  wlan: "mdi:wifi",
  usb: "mdi:usb",
  storage: "mdi:usb",
  vpn: "mdi:lock-outline",
  dect: "mdi:phone-classic",
  network: "mdi:lan",
  lan: "mdi:lan",
  smarthome: "mdi:home-automation",
  sonstiges: "mdi:information-outline",
};

function groupIcon(group) {
  return GROUP_ICONS[group] || "mdi:message-outline";
}

// Icon je Tab, inkl. des "Alle"-Sammel-Tabs (kein echtes group-Kürzel) -
// seit v1.0.0, siehe Moduldoku oben.
function tabIcon(key) {
  if (key === FILTER_ALL) return "mdi:view-list-outline";
  return groupIcon(key);
}

// --- Farben (seit v1.0.0) --------------------------------------------------
//
// Allowlist statt Blockliste: nur Zeichen, die in Hex-/rgb()-/hsl()-/
// var()-Werten oder CSS-Farbnamen vorkommen können. Ein ungültiger Wert
// wird wie "nicht gesetzt" behandelt (Rückfall auf den Standardwert) statt
// einen Fehler zu werfen - läuft bei jedem Render.
const SAFE_COLOR_RE = /^[a-zA-Z0-9#(),.%\-\s]+$/;

function sanitizeColor(value) {
  const trimmed = String(value || "").trim();
  if (!trimmed) return "";
  if (!SAFE_COLOR_RE.test(trimmed)) {
    // eslint-disable-next-line no-console
    console.warn(
      "fritzbox_ereignisse: ungültiger Farbwert ignoriert (nur Hex/rgb()/hsl()/var()/CSS-Farbnamen" +
        " erlaubt):",
      value
    );
    return "";
  }
  return trimmed;
}

// CSS-Custom-Property-Deklarationen für die beiden global wirkenden Farben
// (aktiver Tab, Zeilen-Icons einheitlich) - ein leerer/nicht gesetzter
// config-Wert fällt auf den bisherigen, festen Theme-Farbwert zurück.
const COLOR_CONFIG_KEYS = {
  tab_active: { cssVar: "--fbe-color-tab-active", fallback: "var(--primary-color, #03a9f4)" },
  row_icon: {
    cssVar: "--fbe-color-row-icon",
    fallback: "var(--secondary-text-color, #727272)",
  },
};

// Je Kategorie (Tab UND Zeilen-Icon derselben Kategorie) eine eigene, vom
// Tab-Status unabhängige Icon-Farbe - siehe CATEGORY_ICON_COLOR_NOTE.
// Deckt sowohl die von der Text-Heuristik/den Fetch-Wegen tatsächlich
// vergebenen Kürzel als auch deren in const.py vorgesehene Synonyme ab
// (siehe dortiges EVENT_GROUP_LABELS).
const CATEGORY_ICON_COLOR_KEYS = {
  [FILTER_ALL]: "color_icon_alle",
  tel: "color_icon_telefonie",
  fon: "color_icon_telefonie",
  internet: "color_icon_internet",
  dsl: "color_icon_internet",
  wan: "color_icon_internet",
  usb: "color_icon_usb",
  storage: "color_icon_usb",
  wlan: "color_icon_wlan",
  sys: "color_icon_system",
  system: "color_icon_system",
};

const CATEGORY_ICON_COLOR_NOTE =
  "Standard: folgt der Tab-Farbe (aktiv/inaktiv) bzw. der Zeilen-Icon-Farbe - hier unabhängig davon fest einstellbar.";

const COLOR_EDITOR_FIELDS = [
  { key: "color_tab_active", label: "Aktiver Tab", fallbackHex: "#03a9f4" },
  { key: "color_row_icon", label: "Symbole in der Liste (einheitlich)", fallbackHex: "#727272" },
  {
    key: "color_icon_alle",
    label: "Symbol Kategorie 'Alle'",
    fallbackHex: "#727272",
    note: CATEGORY_ICON_COLOR_NOTE,
  },
  {
    key: "color_icon_telefonie",
    label: "Symbol Kategorie 'Telefonie'",
    fallbackHex: "#727272",
    note: CATEGORY_ICON_COLOR_NOTE,
  },
  {
    key: "color_icon_internet",
    label: "Symbol Kategorie 'Internetverbindung'",
    fallbackHex: "#727272",
    note: CATEGORY_ICON_COLOR_NOTE,
  },
  {
    key: "color_icon_usb",
    label: "Symbol Kategorie 'USB-Geräte'",
    fallbackHex: "#727272",
    note: CATEGORY_ICON_COLOR_NOTE,
  },
  {
    key: "color_icon_wlan",
    label: "Symbol Kategorie 'WLAN'",
    fallbackHex: "#727272",
    note: CATEGORY_ICON_COLOR_NOTE,
  },
  {
    key: "color_icon_system",
    label: "Symbol Kategorie 'System'",
    fallbackHex: "#727272",
    note: CATEGORY_ICON_COLOR_NOTE,
  },
];

// <input type="color"> verlangt zwingend die 6-stellige #rrggbb-Form -
// weder 3-stellige Kurzschreibweise (#4c5) noch rgb()/hsl()/var()/
// Farbnamen werden akzeptiert. normalizeHex() wird zum Anzeigen eines
// evtl. 3-stelligen Hex-Fallbacks im Swatch gebraucht; für alles andere
// (rgb()/var()/...) bleibt das Swatch beim fallbackHex stehen, siehe
// _updateColorSection().
function normalizeHex(hex) {
  const h = String(hex || "").replace("#", "");
  if (h.length === 3) {
    return "#" + h.split("").map((c) => c + c).join("");
  }
  return "#" + h;
}

const HEX_COLOR_RE = /^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$/;

const COLOR_EDITOR_STYLES = `
  .fbe-color-editor {
    margin-top: 12px;
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 8px;
    padding: 0 12px;
  }
  .fbe-color-editor summary {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 0;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    color: var(--primary-text-color, #212121);
    list-style: none;
  }
  .fbe-color-editor summary::-webkit-details-marker { display: none; }
  .fbe-color-editor summary::marker { display: none; }
  .fbe-color-editor summary > ha-icon:first-child {
    --mdc-icon-size: 24px;
    color: var(--secondary-text-color, #727272);
  }
  .fbe-color-editor-chevron {
    margin-left: auto;
    --mdc-icon-size: 24px;
    color: var(--secondary-text-color, #727272);
    transition: transform 0.2s ease;
  }
  .fbe-color-editor[open] > summary .fbe-color-editor-chevron {
    transform: rotate(180deg);
  }
  .fbe-color-editor-body {
    padding: 4px 0 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .fbe-color-reset-row { display: flex; justify-content: flex-end; }
  .fbe-color-reset-button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 6px;
    padding: 6px 10px;
    background: none;
    color: var(--primary-text-color, #212121);
    font: inherit;
    font-size: 0.85em;
    cursor: pointer;
  }
  .fbe-color-reset-button:hover { background: var(--secondary-background-color, rgba(0, 0, 0, 0.04)); }
  .fbe-color-reset-button ha-icon { --mdc-icon-size: 16px; }
  .fbe-color-row { display: flex; flex-direction: column; gap: 4px; }
  .fbe-color-row-label { font-size: 0.9em; color: var(--primary-text-color, #212121); }
  .fbe-color-row-controls { display: flex; align-items: center; gap: 8px; }
  .fbe-color-row-controls input[type="color"] {
    width: 36px;
    height: 36px;
    padding: 0;
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 6px;
    cursor: pointer;
    background: none;
  }
  .fbe-color-row-controls input[type="text"] {
    flex: 1 1 auto;
    min-width: 0;
    padding: 8px;
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 6px;
    font: inherit;
    color: var(--primary-text-color, #212121);
    background: var(--card-background-color, #fff);
    box-sizing: border-box;
  }
  .fbe-color-row-helper { font-size: 0.75em; color: var(--secondary-text-color, #727272); }
`;

const CARD_CSS = `
  :host { display: block; }
  ha-card {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .fbe-header {
    font-size: 1.2em;
    font-weight: 500;
    color: var(--primary-text-color, #212121);
  }
  .fbe-controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }
  .fbe-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    flex: 1 1 auto;
  }
  .fbe-tab {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--divider-color, #e0e0e0);
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color, #212121);
    border-radius: 999px;
    padding: 4px 12px;
    font: inherit;
    font-size: 0.85em;
    cursor: pointer;
  }
  .fbe-tab ha-icon { --mdc-icon-size: 16px; }
  .fbe-tab.active {
    background: var(--fbe-color-tab-active);
    border-color: var(--fbe-color-tab-active);
    color: var(--text-primary-color, #fff);
  }
  .fbe-search {
    flex: 0 1 200px;
    min-width: 120px;
    padding: 6px 10px;
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 6px;
    font: inherit;
    color: var(--primary-text-color, #212121);
    background: var(--card-background-color, #fff);
    box-sizing: border-box;
  }
  .fbe-note {
    display: none;
    font-size: 0.85em;
    color: var(--secondary-text-color, #727272);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .fbe-note ha-icon { --mdc-icon-size: 18px; }
  .fbe-rows {
    display: flex;
    flex-direction: column;
    gap: 2px;
    max-height: 480px;
    overflow-y: auto;
  }
  .fbe-row {
    display: flex;
    gap: 10px;
    padding: 8px 4px;
    border-bottom: 1px solid var(--divider-color, #e0e0e0);
  }
  .fbe-row:last-child { border-bottom: none; }
  .fbe-row-icon {
    flex: 0 0 auto;
    color: var(--fbe-color-row-icon);
    padding-top: 2px;
  }
  .fbe-row-icon ha-icon { --mdc-icon-size: 20px; }
  .fbe-row-main {
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .fbe-row-top {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    font-size: 0.78em;
    color: var(--secondary-text-color, #727272);
  }
  .fbe-row-group { font-weight: 500; }
  .fbe-row-message {
    font-size: 0.92em;
    color: var(--primary-text-color, #212121);
    word-break: break-word;
  }
  .fbe-empty {
    padding: 16px 4px;
    color: var(--secondary-text-color, #727272);
    font-size: 0.9em;
    text-align: center;
  }
`;

// -----------------------------------------------------------------------
// fritzbox-ereignisse-card
// -----------------------------------------------------------------------

class FritzboxEreignisseCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._activeFilter = FILTER_ALL;
    // Reiner UI-Laufzeitstatus, wie bei fritzbox-anrufe-card.js - geht bei
    // jeder Config-Änderung verloren (siehe setConfig()).
    this._search = "";
    this._hass = null;
    this._config = null;
    this._lastSignature = null;
    this._cardEl = null;
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("fritzbox-ereignisse-card: 'entity' ist erforderlich.");
    }
    this._config = withDefaults(config);
    this._activeFilter = FILTER_ALL;
    this._search = "";
    this._lastSignature = null;
    this._buildShell();
    this._updateContent();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;
    const signature = this._computeSignature();
    if (signature !== this._lastSignature) {
      this._lastSignature = signature;
      this._updateContent();
    }
  }

  get hass() {
    return this._hass;
  }

  getCardSize() {
    return 5;
  }

  static getConfigElement() {
    return document.createElement("fritzbox-ereignisse-card-editor");
  }

  static getStubConfig(hass, entities) {
    const guess =
      (entities || []).find((e) => e.startsWith("sensor.") && e.includes("ereignisse")) || "";
    return { entity: guess };
  }

  _entityState() {
    if (!this._hass || !this._config) return null;
    return this._hass.states[this._config.entity] || null;
  }

  _events() {
    const state = this._entityState();
    if (!state) return [];
    return state.attributes.events || [];
  }

  _groupCounts() {
    const counts = new Map();
    this._events().forEach((event) => {
      const key = event.group || "sonstiges";
      const label = event.group_label || key;
      if (!counts.has(key)) counts.set(key, { label, count: 0 });
      counts.get(key).count += 1;
    });
    return counts;
  }

  _filteredEvents() {
    let events = this._events();
    if (this._activeFilter !== FILTER_ALL) {
      events = events.filter((event) => (event.group || "sonstiges") === this._activeFilter);
    }
    const query = this._search.trim().toLowerCase();
    if (query) {
      events = events.filter((event) =>
        `${event.message || ""} ${event.group_label || ""} ${event.date_display || ""}`
          .toLowerCase()
          .includes(query)
      );
    }
    return events;
  }

  _computeSignature() {
    const state = this._entityState();
    if (!state) return "none";
    const events = state.attributes.events || [];
    return `${state.state}|${state.attributes.source}|${events.map((e) => e.id).join(",")}`;
  }

  // CSS-Custom-Property-Deklarationen für die konfigurierbaren Farben
  // (seit v1.0.0) - ein leerer/nicht gesetzter config-Wert fällt auf den
  // bisherigen, festen Theme-Farbwert zurück (COLOR_CONFIG_KEYS), ein
  // ungültiger Wert wird von sanitizeColor() verworfen (ebenfalls
  // Fallback).
  _colorVars() {
    const cfg = this._config || {};
    return Object.entries(COLOR_CONFIG_KEYS)
      .map(([key, { cssVar, fallback }]) => {
        const value = sanitizeColor(cfg[`color_${key}`]) || fallback;
        return `${cssVar}: ${value};`;
      })
      .join("\n        ");
  }

  _styles() {
    return `
      :host {
        ${this._colorVars()}
      }

      ${CARD_CSS}
    `;
  }

  // Optionale, pro Kategorie feste Icon-Farbe für ein Zeilen-Icon (seit
  // v1.0.0) - EINZIGE AUSNAHME: ist `color_row_icon` gesetzt (die
  // Einstellung, die EINE Farbe für ALLE Zeilen-Icons zuweist), gewinnt
  // diese einheitliche Farbe. Sie wird hier bewusst NICHT zurückgegeben
  // (leerer String = kein Inline-Style), weil sie bereits als CSS-Variable
  // (--fbe-color-row-icon, siehe _colorVars()/.fbe-row-icon) für JEDES
  // Zeilen-Icon gilt - ein Inline-Style hier wäre nur eine Dopplung.
  // Identisches Prinzip wie FritzboxAnrufeCard._rowIconColor().
  _rowIconColor(group) {
    const cfg = this._config || {};
    if (sanitizeColor(cfg.color_row_icon)) return "";
    const iconColorKey = CATEGORY_ICON_COLOR_KEYS[group];
    return iconColorKey ? sanitizeColor(cfg[iconColorKey]) : "";
  }

  _buildShell() {
    if (this._cardEl) return;

    this._styleEl = document.createElement("style");
    this._styleEl.textContent = this._styles();

    const card = document.createElement("ha-card");
    this._cardEl = card;

    this._headerEl = document.createElement("div");
    this._headerEl.className = "fbe-header";

    const controls = document.createElement("div");
    controls.className = "fbe-controls";

    this._tabsEl = document.createElement("div");
    this._tabsEl.className = "fbe-tabs";

    this._searchInputEl = document.createElement("input");
    this._searchInputEl.type = "search";
    this._searchInputEl.className = "fbe-search";
    this._searchInputEl.placeholder = "Suchen …";
    // Nur die Zeilen neu rendern, NICHT die ganze Karte (siehe Moduldoku) -
    // sonst würde jeder Tastenanschlag den Fokus aus dem Suchfeld werfen.
    this._searchInputEl.addEventListener("input", () => {
      this._search = this._searchInputEl.value;
      this._renderRows();
    });

    controls.appendChild(this._tabsEl);
    controls.appendChild(this._searchInputEl);

    this._noteEl = document.createElement("div");
    this._noteEl.className = "fbe-note";

    this._rowsEl = document.createElement("div");
    this._rowsEl.className = "fbe-rows";

    card.appendChild(this._headerEl);
    card.appendChild(controls);
    card.appendChild(this._noteEl);
    card.appendChild(this._rowsEl);

    // Persistente Kindknoten des Shadow-Root (Style + Karte) statt
    // shadowRoot.innerHTML - siehe Moduldoku oben.
    this.shadowRoot.replaceChildren(this._styleEl, card);
  }

  _updateContent() {
    this._buildShell();

    // Farben können sich geändert haben (Karten-Editor), ohne dass die
    // Karte neu geladen wird - daher bei jedem Update neu berechnen.
    this._styleEl.textContent = this._styles();

    this._headerEl.style.display = this._config.show_title === false ? "none" : "";
    this._headerEl.textContent = this._config.title || "";

    const state = this._entityState();
    if (!state) {
      this._tabsEl.replaceChildren();
      this._noteEl.style.display = "flex";
      this._noteEl.innerHTML = `<ha-icon icon="mdi:alert-circle-outline"></ha-icon><span>Entität ${escapeHtml(
        this._config.entity
      )} nicht gefunden.</span>`;
      this._rowsEl.innerHTML = "";
      return;
    }

    this._renderTabs();

    // v0.3.0: die Text-Heuristik (siehe Integration, events.py) liefert
    // inzwischen auch ohne native Kategorie oft brauchbare Kategorien -
    // "source: text" allein bedeutet also nicht mehr zwangsläufig "keine
    // Kategorien". Der Hinweis erscheint daher jetzt nur noch, wenn es
    // tatsächlich Ereignisse gibt, aber ausnahmslos ALLE unter
    // "Sonstiges" landen.
    const events = this._events();
    const allUncategorized =
      events.length > 0 && events.every((event) => (event.group || "sonstiges") === "sonstiges");
    if (allUncategorized) {
      this._noteEl.style.display = "flex";
      this._noteEl.innerHTML =
        '<ha-icon icon="mdi:information-outline"></ha-icon><span>Für diese Ereignisse konnte keine Kategorie ermittelt werden – alle erscheinen als "Sonstiges".</span>';
    } else {
      this._noteEl.style.display = "none";
      this._noteEl.textContent = "";
    }

    this._renderRows();
  }

  _renderTabs() {
    const cfg = this._config || {};
    const counts = this._groupCounts();
    const total = this._events().length;
    const tabs = [{ key: FILTER_ALL, label: "Alle", count: total }];
    Array.from(counts.entries())
      .sort((a, b) => a[1].label.localeCompare(b[1].label, "de"))
      .forEach(([key, { label, count }]) => tabs.push({ key, label, count }));

    // Falls die zuvor aktive Kategorie zwischenzeitlich keine Einträge
    // mehr hat (z. B. nach einem Neustart mit frisch geleertem Log),
    // stillschweigend auf "Alle" zurückfallen statt eine leere Liste ohne
    // erkennbaren aktiven Tab zu zeigen.
    if (this._activeFilter !== FILTER_ALL && !counts.has(this._activeFilter)) {
      this._activeFilter = FILTER_ALL;
    }

    this._tabsEl.replaceChildren(
      ...tabs.map((tab) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `fbe-tab${tab.key === this._activeFilter ? " active" : ""}`;
        // Optionale, pro Kategorie feste Icon-Farbe (seit v1.0.0) - per
        // Inline-Style, damit sie (falls gesetzt) die geerbte Tab-Farbe
        // (aktiv/inaktiv) überschreibt; ungesetzt/ungültig bleibt das
        // Icon wie bisher beim geerbten Wert.
        const iconColorKey = CATEGORY_ICON_COLOR_KEYS[tab.key];
        const iconColor = iconColorKey ? sanitizeColor(cfg[iconColorKey]) : "";
        const iconStyle = iconColor ? ` style="color: ${iconColor};"` : "";
        btn.innerHTML = `<ha-icon icon="${tabIcon(tab.key)}"${iconStyle}></ha-icon><span>${escapeHtml(
          tab.label
        )} (${tab.count})</span>`;
        btn.addEventListener("click", () => {
          this._activeFilter = tab.key;
          this._renderTabs();
          this._renderRows();
        });
        return btn;
      })
    );
  }

  _renderRows() {
    const maxRows = Number(this._config.max_rows) || CONFIG_DEFAULTS.max_rows;
    const events = this._filteredEvents().slice(0, maxRows);

    if (!events.length) {
      this._rowsEl.innerHTML = `<div class="fbe-empty">Keine Ereignisse vorhanden.</div>`;
      return;
    }

    this._rowsEl.innerHTML = events
      .map((event) => {
        const when = formatDateTime(event.date) || escapeHtml(event.date_display || "");
        const iconColor = this._rowIconColor(event.group);
        const iconStyle = iconColor ? ` style="color: ${iconColor};"` : "";
        return `
      <div class="fbe-row">
        <div class="fbe-row-icon"><ha-icon icon="${groupIcon(event.group)}"${iconStyle}></ha-icon></div>
        <div class="fbe-row-main">
          <div class="fbe-row-top">
            <span class="fbe-row-group">${escapeHtml(event.group_label || "")}</span>
            <span class="fbe-row-date">${when}</span>
          </div>
          <div class="fbe-row-message">${escapeHtml(event.message || "")}</div>
        </div>
      </div>`;
      })
      .join("");
  }
}

// -----------------------------------------------------------------------
// fritzbox-ereignisse-card-editor
// -----------------------------------------------------------------------

const EDITOR_SCHEMA = [
  { name: "entity", selector: { entity: { domain: "sensor" } } },
  { name: "title", selector: { text: {} } },
  { name: "show_title", selector: { boolean: {} } },
  {
    name: "max_rows",
    selector: { number: { min: 1, max: 100, mode: "box" } },
  },
];

const EDITOR_LABELS = {
  entity: "Ereignisse-Sensor",
  title: "Titel",
  show_title: "Titel anzeigen",
  max_rows: "Maximale Anzahl angezeigter Ereignisse",
  // Farben (seit v1.0.0) sind hier absichtlich NICHT gelistet - siehe
  // COLOR_EDITOR_FIELDS und FritzboxEreignisseCardEditor._buildColorSection()
  // weiter unten.
};

function computeEditorLabel(schema) {
  return EDITOR_LABELS[schema.name] || schema.name;
}

class FritzboxEreignisseCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = withDefaults(config);
    this._renderConfig();
  }

  set hass(hass) {
    this._hass = hass;
    // Nur die hass-Referenz des Formulars aktualisieren (Entity-Picker
    // brauchen den aktuellen Zustand) - NICHT `.data` bei jedem hass-Tick
    // neu setzen, siehe fritzbox-anrufe-card.js für die ausführliche
    // Begründung (sonst würde jede Eingabe durch den nächsten,
    // unabhängigen hass-Tick überschrieben).
    if (this._form) {
      this._form.hass = hass;
    } else {
      this._renderConfig();
    }
  }

  _valueChanged(ev) {
    ev.stopPropagation();
    this._config = ev.detail.value;
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      })
    );
  }

  _renderConfig() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => this._valueChanged(ev));
      this._form.schema = EDITOR_SCHEMA;
      this._form.computeLabel = computeEditorLabel;
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.data = this._config;

    // Farben-Sektion (seit v1.0.0) - siehe Moduldoku und
    // _buildColorSection() unten. Wie beim <ha-form> oben nur bei einer
    // ECHTEN externen Config-Änderung neu befüllen (setConfig()/erster
    // hass-Aufruf), NICHT bei jedem hass-Tick - sonst würden Eingaben bei
    // jedem unabhängigen hass-Update überschrieben (identisches Problem
    // wie beim hass-Setter oben).
    if (!this._colorSection) {
      this._colorSection = this._buildColorSection();
      this.appendChild(this._colorSection);
    }
    this._updateColorSection();
  }

  // Baut die "Farben"-Sektion einmalig als natives <details>-Akkordeon mit
  // einer Zeile je COLOR_EDITOR_FIELDS-Eintrag: ein grafisches
  // <input type="color">-Swatch (Klick öffnet den Farbwähler des
  // Betriebssystems/Browsers) plus ein Textfeld für den vollen CSS-Wert
  // (var()/rgb()/hsl()/Farbnamen - alles, was das Swatch selbst nicht
  // abbilden kann). Bewusst NICHT über <ha-form> gelöst (siehe
  // fritzbox-anrufe-card.js-Moduldoku): <ha-form> hat keinen eingebauten
  // Selector-Typ, der gleichzeitig beliebige CSS-Werte UND eine grafische
  // Farbauswahl UND den aktuell wirksamen Wert anzeigen kann - natives
  // HTML ist hier zugleich funktional passender und unabhängig von der
  // HA-Frontend-Version.
  _buildColorSection() {
    const details = document.createElement("details");
    details.className = "fbe-color-editor";

    const style = document.createElement("style");
    style.textContent = COLOR_EDITOR_STYLES;
    details.appendChild(style);

    const summary = document.createElement("summary");
    summary.innerHTML =
      `<ha-icon icon="mdi:palette-outline"></ha-icon><span>Farben</span>` +
      `<ha-icon class="fbe-color-editor-chevron" icon="mdi:chevron-down"></ha-icon>`;
    details.appendChild(summary);

    const body = document.createElement("div");
    body.className = "fbe-color-editor-body";
    details.appendChild(body);

    const resetRow = document.createElement("div");
    resetRow.className = "fbe-color-reset-row";
    resetRow.innerHTML =
      `<button type="button" class="fbe-color-reset-button">` +
      `<ha-icon icon="mdi:restore"></ha-icon><span>Alle Farben zurücksetzen</span>` +
      `</button>`;
    resetRow.querySelector(".fbe-color-reset-button").addEventListener("click", () =>
      this._resetAllColors()
    );
    body.appendChild(resetRow);

    this._colorInputs = {};
    this._focusedColorKey = null;

    COLOR_EDITOR_FIELDS.forEach((field) => {
      const row = document.createElement("div");
      row.className = "fbe-color-row";
      row.innerHTML = `
        <div class="fbe-color-row-label">${escapeHtml(field.label)}</div>
        <div class="fbe-color-row-controls">
          <input type="color" class="fbe-color-swatch" aria-label="${escapeHtml(field.label)} (grafische Auswahl)" />
          <input type="text" class="fbe-color-text" placeholder="${escapeHtml(field.fallbackHex)}" />
        </div>
        <div class="fbe-color-row-helper"></div>
      `;
      const swatch = row.querySelector(".fbe-color-swatch");
      const text = row.querySelector(".fbe-color-text");

      // Swatch -> Textfeld: <input type="color"> liefert immer ein
      // gültiges #rrggbb, das direkt als CSS-Wert übernommen werden kann.
      swatch.addEventListener("input", () => {
        text.value = swatch.value;
        this._onColorFieldChange(field.key, swatch.value);
      });

      // Textfeld -> config: erst bei "change" (Verlassen des Felds/Enter),
      // nicht bei jedem Tastenanschlag - vermeidet unnötig viele
      // config-changed-Events während des Tippens.
      text.addEventListener("change", () => {
        this._onColorFieldChange(field.key, text.value);
      });
      // _updateColorSection() darf ein Feld, das der Nutzer gerade
      // bearbeitet, nicht überschreiben (gleiches Prinzip wie beim
      // hass-Setter oben) - eigene Fokus-Verfolgung statt
      // document.activeElement, da Letzteres über Shadow-DOM-Grenzen
      // hinweg (z. B. innerhalb eines HA-Dialogs) nicht zuverlässig auf
      // dieses konkrete <input> zeigt.
      text.addEventListener("focus", () => {
        this._focusedColorKey = field.key;
      });
      text.addEventListener("blur", () => {
        if (this._focusedColorKey === field.key) this._focusedColorKey = null;
      });

      body.appendChild(row);
      this._colorInputs[field.key] = { row, swatch, text };
    });

    return details;
  }

  _onColorFieldChange(key, rawValue) {
    this._config = { ...this._config, [key]: rawValue };
    this._updateColorSection();
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      })
    );
  }

  // "Alle Farben zurücksetzen" - leert alle color_*-Schlüssel in einem
  // Zug (= zurück zum bisherigen, festen Theme-Farbverhalten), statt jedes
  // Feld einzeln leeren zu müssen. Löscht bewusst den Fokus-Schutz für
  // diese eine Aktion (siehe _updateColorSection()) - ein expliziter
  // Zurücksetzen-Klick soll IMMER greifen, auch falls der Nutzer gerade in
  // einem der Textfelder tippt. Ein einziges config-changed-Event mit
  // allen geänderten Werten, nicht mehrere einzelne.
  _resetAllColors() {
    const cleared = {};
    COLOR_EDITOR_FIELDS.forEach((field) => {
      cleared[field.key] = "";
    });
    this._config = { ...this._config, ...cleared };
    this._focusedColorKey = null;
    this._updateColorSection();
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      })
    );
  }

  // Aktualisiert Swatch/Textfeld/Hilfetext je Farbfeld anhand von
  // this._config - insbesondere den "aktuell verwendet"-Hinweis
  // (expliziter Wert, sonst der Standardwert).
  _updateColorSection() {
    if (!this._colorInputs) return;
    const cfg = this._config || {};
    COLOR_EDITOR_FIELDS.forEach((field) => {
      const inputs = this._colorInputs[field.key];
      if (!inputs) return;
      const raw = String(cfg[field.key] || "").trim();

      inputs.swatch.value = HEX_COLOR_RE.test(raw) ? normalizeHex(raw) : field.fallbackHex;

      if (this._focusedColorKey !== field.key) {
        inputs.text.value = raw;
      }

      const helperParts = [
        raw ? `Aktuell verwendet: ${raw}` : `Aktuell verwendet (Standard): ${field.fallbackHex}`,
      ];
      if (field.note) helperParts.push(field.note);
      inputs.row.querySelector(".fbe-color-row-helper").textContent = helperParts.join(" – ");
    });
  }
}

customElements.define("fritzbox-ereignisse-card", FritzboxEreignisseCard);
customElements.define("fritzbox-ereignisse-card-editor", FritzboxEreignisseCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "fritzbox-ereignisse-card",
  name: "FRITZ!Box Ereignisse",
  description:
    "Zeigt das FRITZ!Box-Ereignisprotokoll als durchsuchbare, nach Kategorie filterbare Liste - inkl. konfigurierbarer Farben.",
});
