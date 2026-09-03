// fritzbox-ereignisse-card.js - v0.3.0
//
// Lovelace-Karte für die fritzbox_ereignisse-Integration: zeigt das
// FRITZ!Box-Ereignisprotokoll (sensor.fritzbox_ereignisse_ereignisse,
// Attribut "events") als filterbare, durchsuchbare Liste - mit Tabs je
// Kategorie ("Gruppe", z. B. System/Internetverbindung/Telefonie/WLAN/
// USB-Geräte, siehe const.py:EVENT_GROUP_LABELS in der Integration) und
// einer Volltextsuche. Seit v0.3.0 liefert auch der Text-Rückfall
// (source: "text") dank serverseitiger Text-Heuristik oft schon
// Kategorien - der "keine Kategorien"-Hinweis unten prüft daher direkt
// die tatsächlichen Gruppen der Ereignisse, nicht mehr nur "source".
//
// Struktur/Konventionen bewusst an fritzbox-anrufe-card.js angelehnt (siehe
// dortige, ausführlichere Moduldoku): persistente Shadow-Root-Kindknoten
// statt shadowRoot.innerHTML-Ersetzung bei jedem Update, damit ein von
// außen (z. B. card_mod/Theme) in den Shadow-Root injiziertes <style>
// einen Re-Render übersteht, und damit ein Tastaturfokus im Suchfeld beim
// Tippen nicht durch einen kompletten DOM-Rebuild verloren geht.

const FILTER_ALL = "alle";

const CONFIG_DEFAULTS = {
  title: "FRITZ!Box Ereignisse",
  show_title: true,
  max_rows: 15,
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
    border: 1px solid var(--divider-color, #e0e0e0);
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color, #212121);
    border-radius: 999px;
    padding: 4px 12px;
    font: inherit;
    font-size: 0.85em;
    cursor: pointer;
  }
  .fbe-tab.active {
    background: var(--primary-color, #03a9f4);
    border-color: var(--primary-color, #03a9f4);
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
    color: var(--secondary-text-color, #727272);
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

  _buildShell() {
    if (this._cardEl) return;

    const style = document.createElement("style");
    style.textContent = CARD_CSS;

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
    this.shadowRoot.replaceChildren(style, card);
  }

  _updateContent() {
    this._buildShell();

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
        btn.textContent = `${tab.label} (${tab.count})`;
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
        return `
      <div class="fbe-row">
        <div class="fbe-row-icon"><ha-icon icon="${groupIcon(event.group)}"></ha-icon></div>
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
  }
}

customElements.define("fritzbox-ereignisse-card", FritzboxEreignisseCard);
customElements.define("fritzbox-ereignisse-card-editor", FritzboxEreignisseCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "fritzbox-ereignisse-card",
  name: "FRITZ!Box Ereignisse",
  description:
    "Zeigt das FRITZ!Box-Ereignisprotokoll als durchsuchbare, nach Kategorie filterbare Liste.",
});
