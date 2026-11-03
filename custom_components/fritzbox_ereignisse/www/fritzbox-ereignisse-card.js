// SHA256 (Inhalt ab Zeile 2, d.h. dieser Datei ohne diese erste Zeile): a75050d1e8e59c7b67e80f654293630869b2204476d74dba3348a28b8f38552a
// fritzbox-ereignisse-card.js - v1.1.0
//
// Lovelace-Karte für die fritzbox_ereignisse-Integration: zeigt das
// FRITZ!Box-Ereignisprotokoll (sensor.fritzbox_ereignisse_ereignisse,
// Attribut "events") als filterbare, durchsuchbare Liste - mit Tabs je
// Kategorie ("Gruppe", z. B. System/Internetverbindung/Telefonie/WLAN/
// USB-Geräte) und einer Volltextsuche.
//
// Struktur/Konventionen bewusst an fritzbox-anrufe-card.js angelehnt:
// persistente Shadow-Root-Kindknoten statt shadowRoot.innerHTML-Ersetzung
// bei jedem Update, damit ein von außen (z. B. card_mod/Theme) in den
// Shadow-Root injiziertes <style> einen Re-Render übersteht, und damit der
// Tastaturfokus im Suchfeld beim Tippen nicht verloren geht.
//
// Neu in v1.1.0
// -------------
// * Fünf Sprachen (de, en, nl, fr, es) für die Karte selbst (I18N unten);
//   Sprache aus hass.language, Rückfall Englisch.
// * Letzter Tab = Zahnrad ("Einstellungen") mit Akkordeons:
//     1. App-Version (Integration, Karte, neueste Version, Update-Hinweis,
//        "Jetzt prüfen", Link zum Release),
//     2. Notification Center (Hauptschalter + eine Zeile je Meldungsart,
//        nach Dringlichkeit sortiert). Schreiben nur für Administratoren
//        (WebSocket-Aktion fritzbox_ereignisse/action, serverseitig geprüft).
// * Jede Kategorie einzeln ein-/ausschaltbar (show_*), default_tab,
//   show_search, read_only, zoom - alles im grafischen Editor.
// * Versionsblock oben im Editor ("Karte 1.1.0 · Integration 1.1.0").
// * Zusätzliche Statusfarben (success/warning/error/info) einstellbar.
// * Die Karte registriert ihre Elemente nur, wenn sie noch nicht definiert
//   sind. Damit ist ein mehrfaches Laden (Lovelace-Ressource UND
//   Frontend-Rückfall, oder ein manuell eingetragener /hacsfiles-Pfad)
//   unkritisch (Issue #2, "Custom element not found").
//
// Farben (seit v1.0.0): grafische Auswahl im Karten-Editor (natives
// <details>-Akkordeon mit <input type="color"> plus Textfeld für beliebige
// CSS-Werte), siehe COLOR_EDITOR_FIELDS/CATEGORY_ICON_COLOR_KEYS unten.

const CARD_VERSION = "1.1.0";
const WS_ACTION = "fritzbox_ereignisse/action";
const RELEASES_URL = "https://github.com/Meine-smarte-Welt/fritzbox_ereignisse/releases";

const FILTER_ALL = "alle";
const TAB_SETTINGS = "settings";

// --- Sprachen (de, en, nl, fr, es) ------------------------------------------
const I18N = {
  de: {
    search: "Suchen …",
    all: "Alle",
    settings: "Einstellungen",
    none: "Keine Ereignisse vorhanden.",
    entity_missing: "Entität {entity} nicht gefunden.",
    all_uncategorized:
      'Für diese Ereignisse konnte keine Kategorie ermittelt werden – alle erscheinen als "Sonstiges".',
    grp_telefonie: "Telefonie",
    grp_internet: "Internetverbindung",
    grp_usb: "USB-Geräte",
    grp_wlan: "WLAN",
    grp_system: "System",
    grp_sonstiges: "Sonstiges",
    acc_version: "App-Version",
    acc_nc: "Notification Center",
    ver_integration: "Integration",
    ver_card: "Karte",
    ver_latest: "Neueste Version",
    ver_checked: "Zuletzt geprüft",
    ver_check_now: "Jetzt prüfen",
    ver_release: "Release ansehen",
    ver_status_ok: "Aktuell",
    ver_status_update: "Neue Version verfügbar",
    ver_status_failed: "Prüfung nicht möglich",
    ver_status_unchecked: "Noch nicht geprüft",
    ver_update_hint:
      "Aktualisiere über HACS und starte Home Assistant neu. Danach Browser neu laden (Strg+F5).",
    ver_mismatch:
      "Karte ({card}) und Integration ({integration}) haben unterschiedliche Versionen. Browser-Cache leeren (Strg+F5).",
    ver_old_integration: "Die Integration liefert noch keine Versionsdaten. Bitte Home Assistant neu starten.",
    nc_detected: "Notification Center: erkannt",
    nc_missing: "Notification Center: nicht installiert",
    nc_missing_hint:
      "Meldungen werden gesendet, sobald das Notification Center installiert ist.",
    nc_master: "Meldungen an das Notification Center senden",
    nc_types: "Meldungsarten",
    experimental: "Experimentell",
    exp_hint:
      "Experimentelle Funktion: ungeprüft und standardmäßig aus. Sie ist nur sichtbar, weil die experimentellen Funktionen eingeschaltet sind.",
    nc_admin_only: "Nur Administratoren können diese Einstellungen ändern.",
    nc_unavailable: "Die Integration liefert noch keine Notification-Center-Daten. Bitte Home Assistant neu starten.",
    sev_critical: "Kritisch",
    sev_warning: "Warnung",
    sev_info: "Info",
    sev_ok: "OK",
    toast_saved: "Gespeichert",
    toast_checked: "Prüfung abgeschlossen",
    toast_error: "Fehler: {error}",
  },
  en: {
    search: "Search …",
    all: "All",
    settings: "Settings",
    none: "No events available.",
    entity_missing: "Entity {entity} not found.",
    all_uncategorized:
      'No category could be determined for these events – all appear as "Other".',
    grp_telefonie: "Telephony",
    grp_internet: "Internet connection",
    grp_usb: "USB devices",
    grp_wlan: "Wi-Fi",
    grp_system: "System",
    grp_sonstiges: "Other",
    acc_version: "App version",
    acc_nc: "Notification Center",
    ver_integration: "Integration",
    ver_card: "Card",
    ver_latest: "Latest version",
    ver_checked: "Last checked",
    ver_check_now: "Check now",
    ver_release: "View release",
    ver_status_ok: "Up to date",
    ver_status_update: "New version available",
    ver_status_failed: "Check not possible",
    ver_status_unchecked: "Not checked yet",
    ver_update_hint:
      "Update via HACS and restart Home Assistant. Then reload the browser (Ctrl+F5).",
    ver_mismatch:
      "Card ({card}) and integration ({integration}) have different versions. Clear the browser cache (Ctrl+F5).",
    ver_old_integration: "The integration does not provide version data yet. Please restart Home Assistant.",
    nc_detected: "Notification Center: detected",
    nc_missing: "Notification Center: not installed",
    nc_missing_hint:
      "Messages will be sent as soon as the Notification Center is installed.",
    nc_master: "Send messages to the Notification Center",
    nc_types: "Message types",
    experimental: "Experimental",
    exp_hint:
      "Experimental feature: untested and off by default. It is only visible because experimental features are switched on.",
    nc_admin_only: "Only administrators can change these settings.",
    nc_unavailable: "The integration does not provide Notification Center data yet. Please restart Home Assistant.",
    sev_critical: "Critical",
    sev_warning: "Warning",
    sev_info: "Info",
    sev_ok: "OK",
    toast_saved: "Saved",
    toast_checked: "Check finished",
    toast_error: "Error: {error}",
  },
  nl: {
    search: "Zoeken …",
    all: "Alle",
    settings: "Instellingen",
    none: "Geen gebeurtenissen beschikbaar.",
    entity_missing: "Entiteit {entity} niet gevonden.",
    all_uncategorized:
      'Voor deze gebeurtenissen kon geen categorie worden bepaald – alle verschijnen als "Overig".',
    grp_telefonie: "Telefonie",
    grp_internet: "Internetverbinding",
    grp_usb: "USB-apparaten",
    grp_wlan: "WLAN",
    grp_system: "Systeem",
    grp_sonstiges: "Overig",
    acc_version: "App-versie",
    acc_nc: "Notification Center",
    ver_integration: "Integratie",
    ver_card: "Kaart",
    ver_latest: "Nieuwste versie",
    ver_checked: "Laatst gecontroleerd",
    ver_check_now: "Nu controleren",
    ver_release: "Release bekijken",
    ver_status_ok: "Actueel",
    ver_status_update: "Nieuwe versie beschikbaar",
    ver_status_failed: "Controle niet mogelijk",
    ver_status_unchecked: "Nog niet gecontroleerd",
    ver_update_hint:
      "Werk bij via HACS en herstart Home Assistant. Laad daarna de browser opnieuw (Ctrl+F5).",
    ver_mismatch:
      "Kaart ({card}) en integratie ({integration}) hebben verschillende versies. Wis de browsercache (Ctrl+F5).",
    ver_old_integration: "De integratie levert nog geen versiegegevens. Herstart Home Assistant.",
    nc_detected: "Notification Center: gevonden",
    nc_missing: "Notification Center: niet geïnstalleerd",
    nc_missing_hint:
      "Meldingen worden verzonden zodra het Notification Center is geïnstalleerd.",
    nc_master: "Meldingen naar het Notification Center sturen",
    nc_types: "Meldingstypen",
    experimental: "Experimenteel",
    exp_hint:
      "Experimentele functie: ongetest en standaard uit. Ze is alleen zichtbaar omdat experimentele functies zijn ingeschakeld.",
    nc_admin_only: "Alleen beheerders kunnen deze instellingen wijzigen.",
    nc_unavailable: "De integratie levert nog geen Notification Center-gegevens. Herstart Home Assistant.",
    sev_critical: "Kritiek",
    sev_warning: "Waarschuwing",
    sev_info: "Info",
    sev_ok: "OK",
    toast_saved: "Opgeslagen",
    toast_checked: "Controle voltooid",
    toast_error: "Fout: {error}",
  },
  fr: {
    search: "Rechercher …",
    all: "Tous",
    settings: "Paramètres",
    none: "Aucun événement disponible.",
    entity_missing: "Entité {entity} introuvable.",
    all_uncategorized:
      "Aucune catégorie n'a pu être déterminée pour ces événements – tous apparaissent comme « Autre ».",
    grp_telefonie: "Téléphonie",
    grp_internet: "Connexion Internet",
    grp_usb: "Appareils USB",
    grp_wlan: "Wi-Fi",
    grp_system: "Système",
    grp_sonstiges: "Autre",
    acc_version: "Version de l'app",
    acc_nc: "Notification Center",
    ver_integration: "Intégration",
    ver_card: "Carte",
    ver_latest: "Dernière version",
    ver_checked: "Dernière vérification",
    ver_check_now: "Vérifier maintenant",
    ver_release: "Voir la version",
    ver_status_ok: "À jour",
    ver_status_update: "Nouvelle version disponible",
    ver_status_failed: "Vérification impossible",
    ver_status_unchecked: "Pas encore vérifié",
    ver_update_hint:
      "Mets à jour via HACS et redémarre Home Assistant. Recharge ensuite le navigateur (Ctrl+F5).",
    ver_mismatch:
      "La carte ({card}) et l'intégration ({integration}) ont des versions différentes. Vide le cache du navigateur (Ctrl+F5).",
    ver_old_integration: "L'intégration ne fournit pas encore de données de version. Redémarre Home Assistant.",
    nc_detected: "Notification Center : détecté",
    nc_missing: "Notification Center : non installé",
    nc_missing_hint:
      "Les notifications seront envoyées dès que le Notification Center sera installé.",
    nc_master: "Envoyer les notifications au Notification Center",
    nc_types: "Types de notifications",
    experimental: "Expérimental",
    exp_hint:
      "Fonction expérimentale : non testée et désactivée par défaut. Elle n'est visible que parce que les fonctions expérimentales sont activées.",
    nc_admin_only: "Seuls les administrateurs peuvent modifier ces paramètres.",
    nc_unavailable: "L'intégration ne fournit pas encore de données Notification Center. Redémarre Home Assistant.",
    sev_critical: "Critique",
    sev_warning: "Avertissement",
    sev_info: "Info",
    sev_ok: "OK",
    toast_saved: "Enregistré",
    toast_checked: "Vérification terminée",
    toast_error: "Erreur : {error}",
  },
  es: {
    search: "Buscar …",
    all: "Todos",
    settings: "Ajustes",
    none: "No hay eventos disponibles.",
    entity_missing: "Entidad {entity} no encontrada.",
    all_uncategorized:
      'No se pudo determinar una categoría para estos eventos – todos aparecen como "Otros".',
    grp_telefonie: "Telefonía",
    grp_internet: "Conexión a Internet",
    grp_usb: "Dispositivos USB",
    grp_wlan: "Wi-Fi",
    grp_system: "Sistema",
    grp_sonstiges: "Otros",
    acc_version: "Versión de la app",
    acc_nc: "Notification Center",
    ver_integration: "Integración",
    ver_card: "Tarjeta",
    ver_latest: "Última versión",
    ver_checked: "Última comprobación",
    ver_check_now: "Comprobar ahora",
    ver_release: "Ver versión",
    ver_status_ok: "Actualizado",
    ver_status_update: "Nueva versión disponible",
    ver_status_failed: "Comprobación no posible",
    ver_status_unchecked: "Aún no comprobado",
    ver_update_hint:
      "Actualiza a través de HACS y reinicia Home Assistant. Después recarga el navegador (Ctrl+F5).",
    ver_mismatch:
      "La tarjeta ({card}) y la integración ({integration}) tienen versiones distintas. Vacía la caché del navegador (Ctrl+F5).",
    ver_old_integration: "La integración aún no proporciona datos de versión. Reinicia Home Assistant.",
    nc_detected: "Notification Center: detectado",
    nc_missing: "Notification Center: no instalado",
    nc_missing_hint:
      "Los avisos se enviarán en cuanto se instale el Notification Center.",
    nc_master: "Enviar avisos al Notification Center",
    nc_types: "Tipos de aviso",
    experimental: "Experimental",
    exp_hint:
      "Función experimental: sin probar y desactivada por defecto. Solo es visible porque las funciones experimentales están activadas.",
    nc_admin_only: "Solo los administradores pueden cambiar estos ajustes.",
    nc_unavailable: "La integración aún no proporciona datos del Notification Center. Reinicia Home Assistant.",
    sev_critical: "Crítico",
    sev_warning: "Advertencia",
    sev_info: "Info",
    sev_ok: "OK",
    toast_saved: "Guardado",
    toast_checked: "Comprobación finalizada",
    toast_error: "Error: {error}",
  },
};

function translate(hass, key, vars) {
  const lang = String((hass && hass.language) || "en").slice(0, 2).toLowerCase();
  const table = I18N[lang] || I18N.en;
  let text = table[key];
  if (text === undefined) text = I18N.en[key];
  if (text === undefined) text = key;
  if (vars) {
    Object.entries(vars).forEach(([name, value]) => {
      text = text.split(`{${name}}`).join(String(value));
    });
  }
  return text;
}

function uiLocale(hass) {
  const lang = String((hass && hass.language) || "en").toLowerCase();
  return lang || "en";
}

const CONFIG_DEFAULTS = {
  title: "FRITZ!Box Ereignisse",
  show_title: true,
  max_rows: 15,
  show_search: true,
  read_only: false,
  zoom: 100,
  default_tab: "alle",
  show_alle: true,
  show_telefonie: true,
  show_internet: true,
  show_usb: true,
  show_wlan: true,
  show_system: true,
  show_settings: true,
  // Experimentell (Regeln 07): Standard aus.
  show_experimental: false,
  // Farben (seit v1.0.0) sind hier absichtlich NICHT gelistet - ein
  // leerer/nicht gesetzter Wert bedeutet "Standardfarbe verwenden" (siehe
  // COLOR_CONFIG_KEYS/sanitizeColor() unten).
};

// Experimentelle Funktionen (Regeln 07) - schlüsselgleich zu
// EXPERIMENTAL_FEATURES in const.py. Ungeprüft und standardmäßig ausgeblendet:
// sichtbar nur, wenn in der Integration "experimental_enabled" UND in der
// Karte "show_experimental" eingeschaltet sind. "label" ist ein I18N-Schlüssel.
const EXPERIMENTAL = [
  { key: "notification_center", since: "1.1.0", icon: "mdi:bell-outline", label: "acc_nc" },
];

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

function formatDateTime(iso, hass) {
  if (!iso) return "";
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleString(uiLocale(hass), {
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

// Icon je Tab, inkl. des "Alle"-Sammel-Tabs und des Zahnrads.
function tabIcon(key) {
  if (key === FILTER_ALL) return "mdi:view-list-outline";
  if (key === TAB_SETTINGS) return "mdi:cog";
  return groupIcon(key);
}

// Gruppen-Kürzel -> eine der fünf Kategorien der echten FRITZ!Box-Oberfläche
// (steuert Beschriftung und die show_*-Schalter). Alles Unbekannte zählt zu
// "System" - wie im Backend (events.py) der Auffang-Wert.
const CANON = {
  tel: "telefonie",
  fon: "telefonie",
  internet: "internet",
  dsl: "internet",
  wan: "internet",
  usb: "usb",
  storage: "usb",
  wlan: "wlan",
  sys: "system",
  system: "system",
};

function canonCategory(group) {
  return CANON[group] || "system";
}

const CONTENT_SHOW_KEYS = [
  "show_alle",
  "show_telefonie",
  "show_internet",
  "show_usb",
  "show_wlan",
  "show_system",
];

// --- Farben ------------------------------------------------------------------
//
// Allowlist statt Blockliste: nur Zeichen, die in Hex-/rgb()-/hsl()-/
// var()-Werten oder CSS-Farbnamen vorkommen können. Ein ungültiger Wert
// wird wie "nicht gesetzt" behandelt (Rückfall auf den Standardwert).
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

// CSS-Custom-Property-Deklarationen für die global wirkenden Farben - ein
// leerer/nicht gesetzter config-Wert fällt auf den festen Theme-Farbwert
// zurück. Bedeutung der Statusfarben: success = aktuell/erkannt, warning =
// Update verfügbar/Warnung, error = Fehler/kritisch, info = Hinweis.
const COLOR_CONFIG_KEYS = {
  tab_active: { cssVar: "--fbe-color-tab-active", fallback: "var(--primary-color, #03a9f4)" },
  row_icon: {
    cssVar: "--fbe-color-row-icon",
    fallback: "var(--secondary-text-color, #727272)",
  },
  success: { cssVar: "--fbe-color-success", fallback: "var(--success-color, #43a047)" },
  warning: { cssVar: "--fbe-color-warning", fallback: "var(--warning-color, #ff9800)" },
  error: { cssVar: "--fbe-color-error", fallback: "var(--error-color, #db4437)" },
  info: { cssVar: "--fbe-color-info", fallback: "var(--info-color, #039be5)" },
};

// Je Kategorie (Tab UND Zeilen-Icon derselben Kategorie) eine eigene, vom
// Tab-Status unabhängige Icon-Farbe. Deckt die tatsächlich vergebenen Kürzel
// und deren Synonyme ab (siehe const.py:EVENT_GROUP_LABELS).
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
  [TAB_SETTINGS]: "color_icon_settings",
};

const CATEGORY_ICON_COLOR_NOTE =
  "Standard: folgt der Tab-Farbe (aktiv/inaktiv) bzw. der Zeilen-Icon-Farbe - hier unabhängig davon fest einstellbar.";

// Editor-Beschriftungen dürfen Deutsch bleiben (Home Assistant übersetzt
// Editoren nicht), die Karte selbst ist mehrsprachig.
const COLOR_EDITOR_FIELDS = [
  { key: "color_tab_active", label: "Aktiver Tab", fallbackHex: "#03a9f4" },
  { key: "color_row_icon", label: "Symbole in der Liste (einheitlich)", fallbackHex: "#727272" },
  { key: "color_success", label: "Status: aktuell / erkannt (grün)", fallbackHex: "#43a047" },
  { key: "color_warning", label: "Status: Warnung / Update verfügbar (orange)", fallbackHex: "#ff9800" },
  { key: "color_error", label: "Status: Fehler / kritisch (rot)", fallbackHex: "#db4437" },
  { key: "color_info", label: "Status: Hinweis (blau)", fallbackHex: "#039be5" },
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
  {
    key: "color_icon_settings",
    label: "Symbol Zahnrad (Einstellungen)",
    fallbackHex: "#727272",
    note: CATEGORY_ICON_COLOR_NOTE,
  },
];

// <input type="color"> verlangt zwingend die 6-stellige #rrggbb-Form.
function normalizeHex(hex) {
  const h = String(hex || "").replace("#", "");
  if (h.length === 3) {
    return "#" + h.split("").map((c) => c + c).join("");
  }
  return "#" + h;
}

const HEX_COLOR_RE = /^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$/;

const SEVERITY_COLOR_VAR = {
  critical: "var(--fbe-color-error)",
  warning: "var(--fbe-color-warning)",
  info: "var(--fbe-color-info)",
  ok: "var(--fbe-color-success)",
};

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
  .fbe-editor-version {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 10px 12px;
    margin-bottom: 12px;
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 8px;
    font-size: 0.9em;
    color: var(--primary-text-color, #212121);
  }
  .fbe-editor-version.warn { border-color: var(--warning-color, #ff9800); }
  .fbe-editor-version .status-ok { color: var(--success-color, #43a047); }
  .fbe-editor-version .status-warn { color: var(--warning-color, #ff9800); }
  .fbe-editor-version .status-err { color: var(--error-color, #db4437); }
  .fbe-editor-version .status-info { color: var(--info-color, #039be5); }
`;

const CARD_CSS = `
  :host { display: block; container-type: inline-size; container-name: fbe; }
  ha-card {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    position: relative;
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
  .fbe-badge-up {
    color: var(--fbe-color-warning);
    font-weight: 700;
  }
  .fbe-tab.active .fbe-badge-up { color: inherit; }
  @container fbe (max-width: 480px) {
    .fbe-tab .fbe-tab-label { display: none; }
    .fbe-tab { padding: 6px 10px; }
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

  /* Einstellungen: Akkordeons (Design-Master, Abschnitt 5) */
  .fbe-settings { display: flex; flex-direction: column; gap: 10px; }
  .settings-accordion {
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 8px;
  }
  .settings-accordion.update { border-color: var(--fbe-color-warning); }
  .settings-accordion-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    cursor: pointer;
    list-style: none;
    font-weight: 500;
    color: var(--primary-text-color, #212121);
  }
  .settings-accordion-summary::-webkit-details-marker { display: none; }
  .settings-accordion-summary::marker { display: none; }
  .settings-accordion-summary ha-icon {
    --mdc-icon-size: 20px;
    color: var(--secondary-text-color, #727272);
  }
  .settings-accordion-summary .grow { flex: 1 1 auto; }
  .settings-accordion-summary .meta { font-size: 0.8em; font-weight: 400; color: var(--secondary-text-color, #727272); }
  .settings-accordion-summary::after {
    content: "";
    width: 7px;
    height: 7px;
    border-right: 2px solid var(--secondary-text-color, #727272);
    border-bottom: 2px solid var(--secondary-text-color, #727272);
    transform: rotate(45deg);
    transition: transform 0.2s ease;
    margin: 0 4px 3px 4px;
  }
  .settings-accordion[open] > .settings-accordion-summary::after { transform: rotate(225deg); margin-bottom: 0; margin-top: 4px; }
  .settings-accordion-body { padding: 4px 12px 12px; display: flex; flex-direction: column; gap: 8px; }
  .settings-line { display: flex; justify-content: space-between; gap: 12px; font-size: 0.9em; }
  .settings-line .label { color: var(--secondary-text-color, #727272); }
  .settings-line .value { font-weight: 600; color: var(--primary-text-color, #212121); text-align: right; word-break: break-word; }
  .status-ok { color: var(--fbe-color-success); }
  .status-warn { color: var(--fbe-color-warning); }
  .status-err { color: var(--fbe-color-error); }
  .status-info { color: var(--fbe-color-info); }
  .fbe-hint { font-size: 0.82em; color: var(--secondary-text-color, #727272); }
  .fbe-hint.warn { color: var(--fbe-color-warning); }
  .fbe-actions { display: flex; flex-wrap: wrap; gap: 8px; }
  .btn {
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
    text-decoration: none;
  }
  .btn:hover { background: var(--secondary-background-color, rgba(0, 0, 0, 0.04)); }
  .btn ha-icon { --mdc-icon-size: 16px; }
  .nc-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
  .nc-row .dot { width: 8px; height: 8px; border-radius: 50%; flex: 0 0 auto; }
  .nc-row ha-icon { --mdc-icon-size: 18px; color: var(--secondary-text-color, #727272); }
  .nc-row .grow { flex: 1 1 auto; font-size: 0.9em; color: var(--primary-text-color, #212121); }
  .nc-row.off .grow { color: var(--secondary-text-color, #727272); }
  .badge-exp {
    display: inline-block; padding: 1px 8px; border: 1px solid var(--fbe-color-warning);
    border-radius: 999px; color: var(--fbe-color-warning); font-size: 0.78em; font-weight: 600;
  }
  .nc-title { font-size: 0.85em; font-weight: 600; color: var(--secondary-text-color, #727272); margin-top: 4px; }
  .fbe-toast {
    position: absolute;
    left: 50%;
    bottom: 12px;
    transform: translateX(-50%);
    max-width: 90%;
    padding: 8px 14px;
    border-radius: 6px;
    background: var(--primary-text-color, #212121);
    color: var(--card-background-color, #fff);
    font-size: 0.85em;
    display: none;
    z-index: 2;
  }
  .fbe-toast.error { background: var(--fbe-color-error); color: #fff; }
`;

// -----------------------------------------------------------------------
// fritzbox-ereignisse-card
// -----------------------------------------------------------------------

class FritzboxEreignisseCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    // null = noch nichts gewählt -> default_tab gilt (siehe _resolveTabs()).
    this._activeFilter = null;
    // Reiner UI-Laufzeitstatus - geht bei jeder Config-Änderung verloren.
    this._search = "";
    // Auf-/Zuklapp-Zustand der Akkordeons (data-k). Übersteht jedes
    // Neuzeichnen; der toggle-Handler zeichnet NICHT neu (sonst Endlosschleife).
    this._acc = { version: true, nc: false };
    this._hass = null;
    this._config = null;
    this._lastSignature = null;
    this._cardEl = null;
    this._toastTimer = null;
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("fritzbox-ereignisse-card: 'entity' ist erforderlich.");
    }
    this._config = withDefaults(config);
    this._activeFilter = null;
    this._search = "";
    this._lastSignature = null;
    this._buildShell();
    if (this._searchInputEl) this._searchInputEl.value = "";
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

  _t(key, vars) {
    return translate(this._hass, key, vars);
  }

  _entityState() {
    if (!this._hass || !this._config) return null;
    return this._hass.states[this._config.entity] || null;
  }

  _attrs() {
    const state = this._entityState();
    return state ? state.attributes || {} : {};
  }

  _isAdmin() {
    return !!(this._hass && this._hass.user && this._hass.user.is_admin);
  }

  _canEdit() {
    return !this._config.read_only && this._isAdmin();
  }

  // Zeigt die Gruppen-Beschriftung in der Sprache der Oberfläche; unbekannte
  // Kürzel behalten die vom Backend gelieferte Bezeichnung.
  _groupLabel(event) {
    const group = event.group || "sonstiges";
    if (group === "sonstiges") return this._t("grp_sonstiges");
    if (CANON[group]) return this._t(`grp_${CANON[group]}`);
    return event.group_label || group;
  }

  // Ereignisse ohne die per show_* ausgeschalteten Kategorien.
  _events() {
    const state = this._entityState();
    if (!state) return [];
    const all = state.attributes.events || [];
    const show = this._effectiveShow();
    return all.filter((event) => show[canonCategory(event.group)] !== false);
  }

  // Wirksame Kategorie-Schalter: mindestens eine Kategorie bleibt immer
  // sichtbar - sind alle ausgeschaltet, gilt "Alle".
  _effectiveShow() {
    const cfg = this._config || CONFIG_DEFAULTS;
    const show = {
      alle: cfg.show_alle !== false,
      telefonie: cfg.show_telefonie !== false,
      internet: cfg.show_internet !== false,
      usb: cfg.show_usb !== false,
      wlan: cfg.show_wlan !== false,
      system: cfg.show_system !== false,
      settings: cfg.show_settings !== false,
    };
    if (!CONTENT_SHOW_KEYS.some((key) => cfg[key] !== false)) show.alle = true;
    return show;
  }

  _groupCounts() {
    const counts = new Map();
    this._events().forEach((event) => {
      const key = event.group || "sonstiges";
      if (!counts.has(key)) counts.set(key, { label: this._groupLabel(event), count: 0 });
      counts.get(key).count += 1;
    });
    return counts;
  }

  // Tab-Liste und der tatsächlich aktive Tab (berücksichtigt show_*,
  // default_tab und Kategorien, die gerade keine Einträge haben).
  _resolveTabs() {
    const show = this._effectiveShow();
    const counts = this._groupCounts();
    const tabs = [];
    if (show.alle) tabs.push({ key: FILTER_ALL, label: this._t("all"), count: this._events().length });
    Array.from(counts.entries())
      .sort((a, b) => a[1].label.localeCompare(b[1].label, uiLocale(this._hass)))
      .forEach(([key, { label, count }]) => tabs.push({ key, label, count }));
    if (show.settings) tabs.push({ key: TAB_SETTINGS, label: this._t("settings"), count: null });

    const has = (key) => tabs.some((tab) => tab.key === key);
    let active = this._activeFilter;
    if (active === null) {
      const wanted = String((this._config && this._config.default_tab) || FILTER_ALL);
      if (wanted === TAB_SETTINGS && has(TAB_SETTINGS)) active = TAB_SETTINGS;
      else if (wanted === FILTER_ALL && has(FILTER_ALL)) active = FILTER_ALL;
      else {
        const match = tabs.find((tab) => tab.key !== FILTER_ALL && tab.key !== TAB_SETTINGS && canonCategory(tab.key) === wanted);
        active = match ? match.key : null;
      }
    }
    if (active === null || !has(active)) active = tabs.length ? tabs[0].key : FILTER_ALL;
    return { tabs, active };
  }

  _filteredEvents(active) {
    let events = this._events();
    if (active !== FILTER_ALL) {
      events = events.filter((event) => (event.group || "sonstiges") === active);
    }
    const query = this._search.trim().toLowerCase();
    if (query) {
      events = events.filter((event) =>
        `${event.message || ""} ${this._groupLabel(event)} ${event.date_display || ""}`
          .toLowerCase()
          .includes(query)
      );
    }
    return events;
  }

  _computeSignature() {
    const state = this._entityState();
    if (!state) return `none|${this._hass ? this._hass.language : ""}`;
    const attrs = state.attributes || {};
    const events = attrs.events || [];
    const app = attrs.app || {};
    return [
      state.state,
      attrs.source,
      events.map((e) => e.id).join(","),
      JSON.stringify(attrs.notification_center || null),
      this._config && this._config.show_experimental ? "exp" : "",
      [app.version, app.latest_version, app.update_available, app.checked_at, app.check_failed].join(","),
      this._hass ? this._hass.language : "",
      this._isAdmin() ? "admin" : "user",
    ].join("|");
  }

  // CSS-Custom-Property-Deklarationen für die konfigurierbaren Farben.
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

  // Optionale, pro Kategorie feste Icon-Farbe für ein Zeilen-Icon.
  // `color_row_icon` (eine Farbe für ALLE Zeilen-Icons) gewinnt und gilt
  // bereits über die CSS-Variable - hier daher kein Inline-Style.
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

    this._controlsEl = document.createElement("div");
    this._controlsEl.className = "fbe-controls";

    this._tabsEl = document.createElement("div");
    this._tabsEl.className = "fbe-tabs";

    this._searchInputEl = document.createElement("input");
    this._searchInputEl.type = "search";
    this._searchInputEl.className = "fbe-search";
    // Nur die Zeilen neu rendern, NICHT die ganze Karte - sonst würde jeder
    // Tastenanschlag den Fokus aus dem Suchfeld werfen.
    this._searchInputEl.addEventListener("input", () => {
      this._search = this._searchInputEl.value;
      this._renderBody();
    });

    this._controlsEl.appendChild(this._tabsEl);
    this._controlsEl.appendChild(this._searchInputEl);

    this._noteEl = document.createElement("div");
    this._noteEl.className = "fbe-note";

    this._rowsEl = document.createElement("div");
    this._rowsEl.className = "fbe-rows";

    this._toastEl = document.createElement("div");
    this._toastEl.className = "fbe-toast";

    card.appendChild(this._headerEl);
    card.appendChild(this._controlsEl);
    card.appendChild(this._noteEl);
    card.appendChild(this._rowsEl);
    card.appendChild(this._toastEl);

    // Persistente Kindknoten des Shadow-Root (Style + Karte).
    this.shadowRoot.replaceChildren(this._styleEl, card);
  }

  _toast(message, isError) {
    if (!this._toastEl) return;
    this._toastEl.textContent = message;
    this._toastEl.className = `fbe-toast${isError ? " error" : ""}`;
    this._toastEl.style.display = "block";
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => {
      this._toastEl.style.display = "none";
    }, 5000);
  }

  _updateContent() {
    this._buildShell();

    // Farben können sich geändert haben (Karten-Editor), ohne dass die
    // Karte neu geladen wird - daher bei jedem Update neu berechnen.
    this._styleEl.textContent = this._styles();

    const zoom = Number(this._config.zoom);
    this._cardEl.style.zoom = zoom > 0 && zoom !== 100 ? String(zoom / 100) : "";

    this._headerEl.style.display = this._config.show_title === false ? "none" : "";
    this._headerEl.textContent = this._config.title || "";
    this._searchInputEl.placeholder = this._t("search");

    const state = this._entityState();
    if (!state) {
      this._tabsEl.replaceChildren();
      this._searchInputEl.style.display = "none";
      this._noteEl.style.display = "flex";
      this._noteEl.innerHTML = `<ha-icon icon="mdi:alert-circle-outline"></ha-icon><span>${escapeHtml(
        this._t("entity_missing", { entity: this._config.entity })
      )}</span>`;
      this._rowsEl.innerHTML = "";
      return;
    }

    this._renderTabs();
    this._renderBody();
  }

  _renderTabs() {
    const cfg = this._config || {};
    const { tabs, active } = this._resolveTabs();
    this._active = active;
    const app = this._attrs().app || {};

    // Mit nur einem sichtbaren Tab entfällt die Leiste.
    this._tabsEl.style.display = tabs.length <= 1 ? "none" : "";

    this._tabsEl.replaceChildren(
      ...tabs.map((tab) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `fbe-tab${tab.key === active ? " active" : ""}`;
        btn.title = tab.label;
        // Optionale, pro Kategorie feste Icon-Farbe - per Inline-Style, damit
        // sie die geerbte Tab-Farbe überschreibt.
        const iconColorKey = CATEGORY_ICON_COLOR_KEYS[tab.key];
        const iconColor = iconColorKey ? sanitizeColor(cfg[iconColorKey]) : "";
        const iconStyle = iconColor ? ` style="color: ${iconColor};"` : "";
        let suffix = "";
        if (tab.key === TAB_SETTINGS) {
          // "↑" am Zahnrad, wenn eine neue Version existiert (orange).
          suffix = "";
        } else {
          suffix = ` (${tab.count})`;
        }
        btn.innerHTML =
          `<ha-icon icon="${tabIcon(tab.key)}"${iconStyle}></ha-icon>` +
          `<span class="fbe-tab-label">${escapeHtml(tab.label)}${suffix}</span>` +
          (tab.key === TAB_SETTINGS && app.update_available ? '<span class="fbe-badge-up">↑</span>' : "");
        btn.addEventListener("click", () => {
          this._activeFilter = tab.key;
          this._renderTabs();
          this._renderBody();
        });
        return btn;
      })
    );
  }

  _renderBody() {
    const active = this._active || FILTER_ALL;
    const isSettings = active === TAB_SETTINGS;
    const showSearch = this._config.show_search !== false && !isSettings;
    this._searchInputEl.style.display = showSearch ? "" : "none";
    // Ist die Suche ausgeschaltet, gilt auch kein alter Suchtext mehr.
    if (!showSearch && this._search) {
      this._search = "";
      this._searchInputEl.value = "";
    }
    if (isSettings) {
      this._noteEl.style.display = "none";
      this._noteEl.textContent = "";
      this._renderSettings();
    } else {
      this._renderNote();
      this._renderRows(active);
    }
  }

  // Hinweis erscheint nur, wenn es Ereignisse gibt, aber ausnahmslos ALLE
  // unter "Sonstiges" landen.
  _renderNote() {
    const events = this._events();
    const allUncategorized =
      events.length > 0 && events.every((event) => (event.group || "sonstiges") === "sonstiges");
    if (allUncategorized) {
      this._noteEl.style.display = "flex";
      this._noteEl.innerHTML = `<ha-icon icon="mdi:information-outline"></ha-icon><span>${escapeHtml(
        this._t("all_uncategorized")
      )}</span>`;
    } else {
      this._noteEl.style.display = "none";
      this._noteEl.textContent = "";
    }
  }

  _renderRows(active) {
    const maxRows = Number(this._config.max_rows) || CONFIG_DEFAULTS.max_rows;
    const events = this._filteredEvents(active).slice(0, maxRows);

    if (!events.length) {
      this._rowsEl.innerHTML = `<div class="fbe-empty">${escapeHtml(this._t("none"))}</div>`;
      return;
    }

    this._rowsEl.innerHTML = events
      .map((event) => {
        const when = escapeHtml(
          formatDateTime(event.date, this._hass) || event.date_display || ""
        );
        const iconColor = this._rowIconColor(event.group);
        const iconStyle = iconColor ? ` style="color: ${iconColor};"` : "";
        return `
      <div class="fbe-row">
        <div class="fbe-row-icon"><ha-icon icon="${groupIcon(event.group)}"${iconStyle}></ha-icon></div>
        <div class="fbe-row-main">
          <div class="fbe-row-top">
            <span class="fbe-row-group">${escapeHtml(this._groupLabel(event))}</span>
            <span class="fbe-row-date">${when}</span>
          </div>
          <div class="fbe-row-message">${escapeHtml(event.message || "")}</div>
        </div>
      </div>`;
      })
      .join("");
  }

  // --- Einstellungen (Zahnrad) --------------------------------------------

  _accordion(key, icon, title, meta, body, cls) {
    const open = this._acc[key] ? " open" : "";
    return (
      `<details class="settings-accordion${cls ? ` ${cls}` : ""}" data-k="${key}"${open}>` +
      `<summary class="settings-accordion-summary"><ha-icon icon="${icon}"></ha-icon>` +
      `<span class="grow">${escapeHtml(title)}</span><span class="meta">${meta || ""}</span></summary>` +
      `<div class="settings-accordion-body">${body}</div></details>`
    );
  }

  _line(label, valueHtml) {
    return `<div class="settings-line"><span class="label">${escapeHtml(label)}</span><span class="value">${valueHtml}</span></div>`;
  }

  _versionAccordion() {
    const app = this._attrs().app;
    const mismatch = app && app.version && app.version !== CARD_VERSION;
    let statusCls = "status-info";
    let statusText = this._t("ver_status_unchecked");
    if (app && app.check_failed) {
      statusCls = "status-err";
      statusText = this._t("ver_status_failed");
    } else if (app && app.update_available) {
      statusCls = "status-warn";
      statusText = this._t("ver_status_update");
    } else if (app && app.checked_at) {
      statusCls = "status-ok";
      statusText = this._t("ver_status_ok");
    }

    const highlight = !!(app && (app.update_available || mismatch));
    let body = "";
    if (!app) {
      body += `<div class="fbe-hint warn">${escapeHtml(this._t("ver_old_integration"))}</div>`;
      body += this._line(this._t("ver_card"), escapeHtml(CARD_VERSION));
    } else {
      body += this._line(this._t("ver_integration"), escapeHtml(app.version || "?"));
      body += this._line(this._t("ver_card"), escapeHtml(CARD_VERSION));
      body += this._line(this._t("ver_latest"), escapeHtml(app.latest_version || "–"));
      body += this._line(
        this._t("ver_checked"),
        escapeHtml(formatDateTime(app.checked_at, this._hass) || "–")
      );
      body += `<div class="${statusCls}">${escapeHtml(statusText)}</div>`;
      if (app.update_available) {
        body += `<div class="fbe-hint warn">${escapeHtml(this._t("ver_update_hint"))}</div>`;
      }
      if (mismatch) {
        body += `<div class="fbe-hint warn">${escapeHtml(
          this._t("ver_mismatch", { card: CARD_VERSION, integration: app.version })
        )}</div>`;
      }
      // Release-Link nur, wenn er mit https://github.com/ beginnt.
      const url =
        typeof app.release_url === "string" && app.release_url.startsWith("https://github.com/")
          ? app.release_url
          : RELEASES_URL;
      body += '<div class="fbe-actions">';
      if (this._canEdit()) {
        body += `<button type="button" class="btn" data-act="check"><ha-icon icon="mdi:refresh"></ha-icon><span>${escapeHtml(
          this._t("ver_check_now")
        )}</span></button>`;
      }
      body += `<a class="btn" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer"><ha-icon icon="mdi:open-in-new"></ha-icon><span>${escapeHtml(
        this._t("ver_release")
      )}</span></a></div>`;
    }

    const meta = app ? `<span class="${statusCls}">${escapeHtml(app.version || CARD_VERSION)}</span>` : "";
    return this._accordion("version", "mdi:tag-outline", this._t("acc_version"), meta, body, highlight ? "update" : "");
  }

  _ncAccordion() {
    const nc = this._attrs().notification_center;
    let body = "";
    let meta = "";
    if (!nc) {
      body = `<div class="fbe-hint warn">${escapeHtml(this._t("nc_unavailable"))}</div>`;
    } else {
      const editable = this._canEdit();
      body += nc.available
        ? `<div class="status-ok">${escapeHtml(this._t("nc_detected"))}</div>`
        : `<div class="status-info">${escapeHtml(this._t("nc_missing"))}</div>` +
          `<div class="fbe-hint">${escapeHtml(this._t("nc_missing_hint"))}</div>`;
      if (!this._config.read_only && !this._isAdmin()) {
        body += `<div class="fbe-hint">${escapeHtml(this._t("nc_admin_only"))}</div>`;
      }
      const masterOn = !!nc.enabled;
      body +=
        `<div class="nc-row"><span class="grow">${escapeHtml(this._t("nc_master"))}</span>` +
        (this._config.read_only
          ? `<span class="${masterOn ? "status-ok" : "status-info"}">${masterOn ? "●" : "○"}</span>`
          : `<ha-switch data-nc="master" data-on="${masterOn ? "1" : "0"}" data-lock="${editable ? "0" : "1"}"></ha-switch>`) +
        `</div>`;
      body += `<div class="nc-title">${escapeHtml(this._t("nc_types"))}</div>`;
      const lang = String((this._hass && this._hass.language) || "en").slice(0, 2).toLowerCase();
      (nc.types || []).forEach((type) => {
        const labels = type.labels || {};
        const label = labels[lang] || labels.en || type.type;
        const color = SEVERITY_COLOR_VAR[type.severity] || SEVERITY_COLOR_VAR.info;
        const sev = this._t(`sev_${type.severity}`);
        const on = !!type.enabled;
        body +=
          `<div class="nc-row${masterOn ? "" : " off"}" title="${escapeHtml(sev)}">` +
          `<span class="dot" style="background:${color}"></span>` +
          `<ha-icon icon="${escapeHtml(type.icon || "mdi:bell-outline")}"></ha-icon>` +
          `<span class="grow">${escapeHtml(label)}</span>` +
          (this._config.read_only
            ? `<span class="${on ? "status-ok" : "status-info"}">${on ? "●" : "○"}</span>`
            : `<ha-switch data-nc="type" data-type="${escapeHtml(type.type)}" data-on="${on ? "1" : "0"}" data-lock="${
                editable && masterOn ? "0" : "1"
              }"></ha-switch>`) +
          `</div>`;
      });
    }
    // Orangefarbenes Badge: experimentelle Funktion (Regeln 07).
    meta = `<span class="badge-exp" title="${escapeHtml(this._t("exp_hint"))}">${escapeHtml(
      this._t("experimental")
    )}</span>`;
    return this._accordion("nc", "mdi:bell-outline", this._t("acc_nc"), meta, body, "");
  }

  // Experimentelle Funktionen sichtbar? Nur wenn die Integration sie freigibt
  // (Sensor-Attribut) UND die Karte "show_experimental" gesetzt hat.
  _experimentalVisible() {
    const nc = this._attrs().notification_center;
    return !!(this._config && this._config.show_experimental && nc && nc.experimental);
  }

  _renderSettings() {
    this._rowsEl.innerHTML =
      `<div class="fbe-settings">` +
      this._versionAccordion() +
      (this._experimentalVisible() ? this._ncAccordion() : "") +
      `</div>`;

    // Zustand der Akkordeons merken, OHNE neu zu zeichnen.
    this._rowsEl.querySelectorAll("details.settings-accordion").forEach((details) => {
      details.addEventListener("toggle", () => {
        this._acc[details.dataset.k] = details.open;
      });
    });

    const checkBtn = this._rowsEl.querySelector('[data-act="check"]');
    if (checkBtn) checkBtn.addEventListener("click", () => this._checkUpdate());

    this._rowsEl.querySelectorAll("ha-switch[data-nc]").forEach((sw) => {
      sw.checked = sw.dataset.on === "1";
      sw.disabled = sw.dataset.lock === "1";
      sw.addEventListener("change", () => {
        if (sw.dataset.nc === "master") {
          this._wsAction({ action: "nc_set_master", enabled: sw.checked });
        } else {
          this._wsAction({ action: "nc_set_type", nc_type: sw.dataset.type, enabled: sw.checked });
        }
      });
    });
  }

  async _wsAction(payload, successKey) {
    const attrs = this._attrs();
    const message = { type: WS_ACTION, ...payload };
    if (attrs.entry_id) message.entry_id = attrs.entry_id;
    try {
      await this._hass.callWS(message);
      this._toast(this._t(successKey || "toast_saved"), false);
    } catch (err) {
      this._toast(this._t("toast_error", { error: (err && err.message) || String(err) }), true);
      // Schalter auf den echten Zustand zurücksetzen.
      this._lastSignature = null;
      this._updateContent();
    }
  }

  _checkUpdate() {
    return this._wsAction({ action: "check_update" }, "toast_checked");
  }
}

// -----------------------------------------------------------------------
// fritzbox-ereignisse-card-editor
// -----------------------------------------------------------------------

const DEFAULT_TAB_OPTIONS = [
  { value: "alle", label: "Alle" },
  { value: "telefonie", label: "Telefonie" },
  { value: "internet", label: "Internetverbindung" },
  { value: "usb", label: "USB-Geräte" },
  { value: "wlan", label: "WLAN" },
  { value: "system", label: "System" },
  { value: "settings", label: "Einstellungen (Zahnrad)" },
];

// ha-form mit flatten: true, damit die YAML-Schlüssel flach bleiben.
const EDITOR_SCHEMA = [
  { name: "entity", selector: { entity: { domain: "sensor" } } },
  { name: "title", selector: { text: {} } },
  {
    type: "expandable",
    name: "",
    title: "Kategorien",
    flatten: true,
    expanded: true,
    schema: [
      { name: "show_alle", selector: { boolean: {} } },
      { name: "show_telefonie", selector: { boolean: {} } },
      { name: "show_internet", selector: { boolean: {} } },
      { name: "show_usb", selector: { boolean: {} } },
      { name: "show_wlan", selector: { boolean: {} } },
      { name: "show_system", selector: { boolean: {} } },
      { name: "show_settings", selector: { boolean: {} } },
      {
        name: "default_tab",
        selector: { select: { mode: "dropdown", options: DEFAULT_TAB_OPTIONS } },
      },
    ],
  },
  {
    type: "expandable",
    name: "",
    title: "Darstellung",
    flatten: true,
    schema: [
      { name: "show_title", selector: { boolean: {} } },
      { name: "show_search", selector: { boolean: {} } },
      { name: "max_rows", selector: { number: { min: 1, max: 100, mode: "box" } } },
      { name: "zoom", selector: { number: { min: 50, max: 200, step: 5, mode: "box", unit_of_measurement: "%" } } },
    ],
  },
  {
    type: "expandable",
    name: "",
    title: "Bearbeiten",
    flatten: true,
    schema: [{ name: "read_only", selector: { boolean: {} } }],
  },
  // Gruppe "Experimentell" (Regeln 07): nur vorhanden, wenn es experimentelle
  // Funktionen gibt. Steht bewusst als letzte Gruppe.
  ...(EXPERIMENTAL.length
    ? [
        {
          type: "expandable",
          name: "",
          title: "Experimentell",
          flatten: true,
          schema: [{ name: "show_experimental", selector: { boolean: {} } }],
        },
      ]
    : []),
];

const EDITOR_LABELS = {
  entity: "Ereignisse-Sensor",
  title: "Titel",
  show_alle: "Kategorie 'Alle' anzeigen",
  show_telefonie: "Kategorie 'Telefonie' anzeigen",
  show_internet: "Kategorie 'Internetverbindung' anzeigen",
  show_usb: "Kategorie 'USB-Geräte' anzeigen",
  show_wlan: "Kategorie 'WLAN' anzeigen",
  show_system: "Kategorie 'System' anzeigen",
  show_settings: "Zahnrad (Einstellungen, Version) anzeigen",
  default_tab: "Starttab",
  show_title: "Titel anzeigen",
  show_search: "Suchfeld anzeigen",
  max_rows: "Maximale Anzahl angezeigter Ereignisse",
  zoom: "Zoom (Skalierung der Karte)",
  read_only: "Nur lesen (alle Bedienelemente ausblenden)",
  show_experimental: "Experimentelle Funktionen anzeigen",
  // Farben sind hier absichtlich NICHT gelistet - siehe COLOR_EDITOR_FIELDS
  // und FritzboxEreignisseCardEditor._buildColorSection().
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
    // neu setzen, sonst würde jede Eingabe überschrieben.
    if (this._form) {
      this._form.hass = hass;
      this._updateVersionBlock();
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

    // Versionsblock ganz oben: "Karte 1.1.0 · Integration 1.1.0" + Status.
    if (!this._versionEl) {
      const style = document.createElement("style");
      style.textContent = COLOR_EDITOR_STYLES;
      this.appendChild(style);
      this._versionEl = document.createElement("div");
      this._versionEl.className = "fbe-editor-version";
      this.appendChild(this._versionEl);
    }

    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => this._valueChanged(ev));
      this._form.schema = EDITOR_SCHEMA;
      this._form.computeLabel = computeEditorLabel;
      this._form.computeHelper = (schema) => this._computeHelper(schema);
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.data = this._config;
    this._updateVersionBlock();

    // Farben-Sektion - nur bei einer ECHTEN externen Config-Änderung neu
    // befüllen, NICHT bei jedem hass-Tick.
    if (!this._colorSection) {
      this._colorSection = this._buildColorSection();
      this.appendChild(this._colorSection);
    }
    this._updateColorSection();
  }

  // Hinweistext zur Gruppe "Experimentell": ungeprüft, Anzahl, Namen.
  _computeHelper(schema) {
    if (schema.name !== "show_experimental") return "";
    const names = EXPERIMENTAL.map((feature) => translate(this._hass, feature.label)).join(", ");
    return (
      `Ungeprüfte Funktionen (${EXPERIMENTAL.length}): ${names}. Sie sind ausgeblendet, bis du sie hier ` +
      `UND in den Optionen der Integration einschaltest. Danach hat jede Funktion einen eigenen Schalter (Standard aus).`
    );
  }

  _updateVersionBlock() {
    if (!this._versionEl) return;
    const entity = this._config && this._config.entity;
    const state = entity && this._hass && this._hass.states ? this._hass.states[entity] : null;
    const app = state && state.attributes ? state.attributes.app : null;
    const integration = app && app.version ? app.version : "?";
    let statusCls = "status-info";
    let statusText = translate(this._hass, "ver_status_unchecked");
    let warn = false;
    if (app && app.check_failed) {
      statusCls = "status-err";
      statusText = translate(this._hass, "ver_status_failed");
    } else if (app && app.update_available) {
      statusCls = "status-warn";
      statusText = `${translate(this._hass, "ver_status_update")}: ${escapeHtml(app.latest_version || "")}`;
      warn = true;
    } else if (app && app.checked_at) {
      statusCls = "status-ok";
      statusText = translate(this._hass, "ver_status_ok");
    }
    let html =
      `<div><strong>${escapeHtml(translate(this._hass, "ver_card"))} ${escapeHtml(CARD_VERSION)}</strong> · ` +
      `<strong>${escapeHtml(translate(this._hass, "ver_integration"))} ${escapeHtml(integration)}</strong></div>` +
      `<div class="${statusCls}">${statusText}</div>`;
    if (warn) {
      html += `<div class="status-warn">${escapeHtml(translate(this._hass, "ver_update_hint"))}</div>`;
    }
    if (app && app.version && app.version !== CARD_VERSION) {
      warn = true;
      html += `<div class="status-warn">${escapeHtml(
        translate(this._hass, "ver_mismatch", { card: CARD_VERSION, integration: app.version })
      )}</div>`;
    }
    this._versionEl.className = `fbe-editor-version${warn ? " warn" : ""}`;
    this._versionEl.innerHTML = html;
  }

  // Baut die "Farben"-Sektion einmalig als natives <details>-Akkordeon mit
  // einer Zeile je COLOR_EDITOR_FIELDS-Eintrag: ein grafisches
  // <input type="color">-Swatch plus ein Textfeld für den vollen CSS-Wert
  // (var()/rgb()/hsl()/Farbnamen). Bewusst NICHT über <ha-form>, weil
  // <ha-form> keinen Selector kennt, der gleichzeitig beliebige CSS-Werte,
  // eine grafische Auswahl und den aktuell wirksamen Wert abbildet.
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

      // Swatch -> Textfeld: <input type="color"> liefert immer ein gültiges
      // #rrggbb, das direkt als CSS-Wert übernommen werden kann.
      swatch.addEventListener("input", () => {
        text.value = swatch.value;
        this._onColorFieldChange(field.key, swatch.value);
      });

      // Textfeld -> config: erst bei "change" (Verlassen des Felds/Enter).
      text.addEventListener("change", () => {
        this._onColorFieldChange(field.key, text.value);
      });
      // _updateColorSection() darf ein Feld, das der Nutzer gerade
      // bearbeitet, nicht überschreiben - eigene Fokus-Verfolgung statt
      // document.activeElement (über Shadow-DOM-Grenzen unzuverlässig).
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

  // "Alle Farben zurücksetzen" - leert alle color_*-Schlüssel in einem Zug,
  // mit einem einzigen config-changed-Event.
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
  // this._config.
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

// Nur registrieren, wenn noch nicht definiert: die Karte kann (Lovelace-
// Ressource + Frontend-Rückfall + evtl. manuell eingetragener Pfad) mehrfach
// geladen werden - ein zweites customElements.define würde sonst einen
// Fehler werfen.
if (!customElements.get("fritzbox-ereignisse-card")) {
  customElements.define("fritzbox-ereignisse-card", FritzboxEreignisseCard);
}
if (!customElements.get("fritzbox-ereignisse-card-editor")) {
  customElements.define("fritzbox-ereignisse-card-editor", FritzboxEreignisseCardEditor);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "fritzbox-ereignisse-card")) {
  window.customCards.push({
    type: "fritzbox-ereignisse-card",
    name: "FRITZ!Box Ereignisse",
    description:
      "Zeigt das FRITZ!Box-Ereignisprotokoll als durchsuchbare, nach Kategorie filterbare Liste - inkl. Versionsanzeige und konfigurierbarer Farben. Experimentelle Funktionen (Notification Center) sind ausgeblendet, bis sie ausdrücklich eingeschaltet werden.",
    preview: false,
  });
  // eslint-disable-next-line no-console
  console.info(
    `%c FRITZBOX-EREIGNISSE-CARD %c v${CARD_VERSION} `,
    "color: #fff; background: #3b6642; font-weight: 700;",
    "color: #3b6642; background: #fff; font-weight: 700;"
  );
}
