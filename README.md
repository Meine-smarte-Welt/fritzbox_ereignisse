🇩🇪 Deutsch · [🇬🇧 English](README.en.md) · [🇳🇱 Nederlands](README.nl.md) · [🇫🇷 Français](README.fr.md) · [🇪🇸 Español](README.es.md)

# FRITZ!Box Ereignisse

Home-Assistant-Integration, die das **Ereignisprotokoll** der FRITZ!Box ("System → Ereignisse") als Sensor und Dashboard-Karte zeigt. Neue Einträge kannst du zusätzlich ans [Notification Center](https://github.com/Meine-smarte-Welt) senden. Schwester-Integration zu [FRITZ!Box Anrufe](https://github.com/Meine-smarte-Welt/fritzbox_anrufe).

<p>
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Meine-smarte-Welt&amp;repository=fritzbox_ereignisse&amp;category=integration"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Repository in Home Assistant öffnen" height="32"></a>
</p>

![HACS](https://img.shields.io/badge/HACS-Custom-orange)

**Version 1.1.0.** Teststand: siehe [Bekannte Einschränkungen](#bekannte-einschränkungen). Die Übersetzungen (nl, fr, es) sind maschinell erstellt, Korrekturen sind willkommen. Das Notification Center ist **experimentell** und standardmäßig aus (siehe [EXPERIMENTELL.md](EXPERIMENTELL.md)).

## Funktionsumfang

- Sensor mit allen Einträgen des Ereignisprotokolls, Kategorien wie in der FRITZ!Box (Telefonie, Internetverbindung, USB-Geräte, WLAN, System)
- Dashboard-Karte mit Reitern, Suche, Zoom, `read_only` und einstellbaren Farben
- Meldungen ans Notification Center (Schema 1), je Meldungsart einzeln schaltbar (experimentell, standardmäßig aus)
- Versionsanzeige mit Hinweis auf neue GitHub-Releases (Prüfung alle 12 Stunden)
- Fünf Sprachen: Deutsch, Englisch, Niederländisch, Französisch, Spanisch

## Voraussetzungen

- Home Assistant ab 2025.8
- In der FRITZ!Box: **Heimnetz → Netzwerk → Netzwerkeinstellungen → "Zugriff für Anwendungen zulassen"** aktivieren
- Ein FRITZ!Box-Benutzer mit der Berechtigung **"FRITZ!Box-Einstellungen"** (System → FRITZ!Box-Benutzer)

## Installation

**HACS:** Benutzerdefiniertes Repository `https://github.com/Meine-smarte-Welt/fritzbox_ereignisse` (Kategorie Integration) hinzufügen, "FRITZ!Box Ereignisse" herunterladen, Home Assistant neu starten.

**Manuell:** Ordner `custom_components/fritzbox_ereignisse` nach `<config>/custom_components/` kopieren, Home Assistant neu starten.

## Einrichtung

Einstellungen → Geräte & Dienste → Integration hinzufügen → "FRITZ!Box Ereignisse". Eingeben: Host, Port (Standard 49000), Benutzername, Passwort. Unter "Konfigurieren" stellst du die Verlaufstiefe (Anzahl oder Tage) und das Notification Center ein.

## Die Karte

Die Karte wird mit der Integration ausgeliefert und trägt sich selbst als Lovelace-Ressource ein (im YAML-Modus: Ressource `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` als `module` manuell eintragen).

```yaml
type: custom:fritzbox-ereignisse-card
entity: sensor.fritzbox_ereignisse_ereignisse
title: FRITZ!Box Ereignisse
max_rows: 15
default_tab: alle   # alle | telefonie | internet | usb | wlan | system | settings
show_search: true
read_only: false
zoom: 100
```

Reiter: Alle, die fünf Kategorien und als letzter das Zahnrad (Einstellungen). Jede Kategorie lässt sich im grafischen Editor mit `show_<kategorie>` ein- und ausschalten; mindestens eine bleibt sichtbar. Ein "↑" am Zahnrad zeigt eine neue Version an.

## Farben

Im Editor-Bereich "Farben" (Farbwähler + Textfeld, "Alle Farben zurücksetzen"). Erlaubt sind Hex, `rgb()`, `hsl()`, `var(--…)` und Farbnamen; alles andere wird verworfen.

| Schlüssel | Wirkung |
|---|---|
| `color_tab_active` | aktiver Reiter |
| `color_row_icon` | alle Zeilensymbole (überschreibt die Kategoriefarben) |
| `color_success` / `color_warning` / `color_error` / `color_info` | Status (aktuell / Update oder Warnung / Fehler / Hinweis) |
| `color_icon_alle`, `_telefonie`, `_internet`, `_usb`, `_wlan`, `_system`, `_settings` | Symbolfarbe je Kategorie |

## Services

Diese Integration stellt keine eigenen Services bereit.

## Ereignisse

`fritzbox_ereignisse_new_event` wird gefeuert, sobald ein neuer Eintrag im Protokoll erscheint (Payload: `entry_id`, `id`, `code`, `group`, `group_label`, `date`, `date_display`, `message`). Beim ersten Abruf nach dem Start wird bewusst kein Ereignis gefeuert. Beispiel: [`examples/automation_new_event.yaml`](examples/automation_new_event.yaml). Neu in 1.1.0: `id` ist jetzt immer eindeutig; die ursprüngliche Nummer der FRITZ!Box steht in `code` (falls vorhanden).

## Sensoren

`sensor.fritzbox_ereignisse_ereignisse` (Zustand = Anzahl der Einträge). Attribute: `events`, `groups`, `source` (`query`, `xml` oder `text`), `app` (Version, Update-Status) und `notification_center`. Die großen Attribute werden **nicht** in der Datenbank aufgezeichnet (behebt die Recorder-Warnung "state attributes exceed 16384 bytes"). `notification_center` erscheint nur mit `experimental: true`, wenn die experimentellen Funktionen eingeschaltet sind.

## Notification Center

> **Experimentell.** Diese Funktion ist standardmäßig ausgeblendet und aus. Einschalten: Einstellungen → Geräte & Dienste → FRITZ!Box Ereignisse → Konfigurieren → "Experimentelle Funktionen" aktivieren, im nächsten Schritt das Notification Center einschalten. In der Karte zusätzlich im Karten-Editor "Experimentelle Funktionen anzeigen" aktivieren. Vor dem Abschalten die Meldungen im Notification Center ausschalten, offene Meldungen werden beim Abschalten nicht geschlossen. Details: [EXPERIMENTELL.md](EXPERIMENTELL.md).

Ist das Notification Center installiert, sendet die Integration Meldungen nach Schema 1. Einstellbar unter "Konfigurieren" und in der Karte (Zahnrad → Notification Center, nur für Administratoren).

| Meldungsart | Dringlichkeit | Standard |
|---|---|---|
| Verbindung zur FRITZ!Box verloren (wird wieder geschlossen, sobald der Abruf klappt) | Warnung | an |
| Ereignisse: System, Internetverbindung, USB-Geräte (Einzelmeldung je neuem Eintrag) | Info | an |
| Ereignisse: Telefonie, WLAN | Info | aus (viele Einträge) |

Die Dringlichkeit der Protokolleinträge ist bewusst "Info", weil der Meldungstext allein nicht verrät, ob ein Eintrag ein Problem ist. Ohne Notification Center passiert nichts; die Meldungen werden gesendet, sobald es installiert ist.

## Versionsanzeige und Update-Hinweis

Die Version steht an drei Stellen: Karte → Zahnrad → "App-Version", oben im Karten-Editor und im Dialog "Konfigurieren". Beim Start und danach alle 12 Stunden fragt die Integration `api.github.com` nach der neuesten Version. Gibt es eine neuere, wird sie orange hervorgehoben. Ist GitHub nicht erreichbar, steht dort "Prüfung nicht möglich"; alles andere läuft normal weiter.

## Einstellungen

- **Verlaufstiefe:** Anzahl Ereignisse (20–500, Standard 100) oder Anzahl Tage (1–90, Standard 30)
- **Experimentelle Funktionen:** Hauptschalter (Standard aus); erst danach erscheinen Notification Center (Hauptschalter und eine Zeile je Meldungsart)

## Sicherheit

Schreibende Aktionen der Karte (Notification-Center-Schalter, "Jetzt prüfen") laufen über eine WebSocket-Aktion, die das Backend nur Administratoren erlaubt. Alle Texte in der Karte werden maskiert, Farbwerte laufen über eine Allowlist. Die Diagnose enthält keine Zugangsdaten und keine Meldungstexte. Die FRITZ!Box nutzt ein selbst signiertes Zertifikat; für den HTTPS-Abruf des Protokolls wird es deshalb nicht geprüft (nur im lokalen Netz).

## Bekannte Einschränkungen

- **Nicht an echter FRITZ!Box getestet.** Getestet wurde nur gegen simulierte Daten (XML-Parser, Form der query.lua-Antwort, Notification-Center-Brücke). Rückmeldungen aus echten Installationen zu diesem Stand liegen noch nicht vor. Ob Issue #1 auf deiner Box behoben ist, bitten wir dich zu melden (FRITZ!OS-Version, `source`-Attribut und Debug-Log; es enthält nur Typen und Feldnamen, keine Inhalte).
- Das Zusammenspiel mit einem echten Notification Center wurde nicht geprüft, deshalb ist die Funktion experimentell.
- Issue #2 ("Custom element doesn't exist") ließ sich nicht nachstellen. Die Karte wird jetzt zusätzlich über einen Rückfall geladen und ist gegen doppeltes Laden abgesichert. Hilft das nicht: Ressource `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` (Typ JavaScript-Modul) manuell eintragen und mit Strg+F5 neu laden. Issue #3 (404 beim Laden der Karte) hatte vermutlich dieselbe Ursache: 1.1.0 war zuerst nur eine Vorabversion, HACS bietet dann weiter 1.0.0 an. Das ist nicht bestätigt.
- Das Zahnrad schaltet für mehrere FRITZ!Boxen immer den ersten Eintrag.
- Die Karte wurde in einem Headless-Chrome mit Testdaten durchgespielt, aber nicht in einem echten Home Assistant.

## Fehlerbehebung

- **Karte nicht gefunden:** siehe oben (Ressource manuell eintragen, Strg+F5).
- **Keine Einträge:** Debug-Log für `custom_components.fritzbox_ereignisse` einschalten und das Attribut `source` prüfen.
- **Nach dem Update fehlt die neue Funktion:** Home Assistant neu starten, dann den Browser-Cache leeren.

## Datei-Integrität

Jede `.py`, `.js` und `.yaml` trägt in der ersten Zeile einen SHA-256 der Datei ab Zeile 2 (`tail -n +2 datei.py | sha256sum`). Für JSON-Dateien (ohne Kommentare) gilt diese Tabelle über die komplette Datei:

<!--HASHES-->
| Datei | SHA-256 |
|---|---|
| `custom_components/fritzbox_ereignisse/icons.json` | `67da9e1131e789f9c2ad831d81f8a524564790995018e9f99ec7b786ce2248ec` |
| `custom_components/fritzbox_ereignisse/manifest.json` | `ff522edb759c85195f495cba46f39cef141645568dd7116d250c1a7bff7b4b72` |
| `custom_components/fritzbox_ereignisse/strings.json` | `58c3dc20fba447321fa7544e555eed8502c7272e43ad8959429722d290c23faf` |
| `custom_components/fritzbox_ereignisse/translations/de.json` | `58c3dc20fba447321fa7544e555eed8502c7272e43ad8959429722d290c23faf` |
| `custom_components/fritzbox_ereignisse/translations/en.json` | `22781876e46fd9ed02be9eae843f2ad00953fd99eb988abaf6fe2329049558c0` |
| `custom_components/fritzbox_ereignisse/translations/es.json` | `bb59e5dbc9805250afd699a11af3858633d2a954898c443c4674304217439db1` |
| `custom_components/fritzbox_ereignisse/translations/fr.json` | `f3b6598bc1e48cd5dbb07282eb7c8b6dbc09eedfd84bb0be8913a9674a89d88b` |
| `custom_components/fritzbox_ereignisse/translations/nl.json` | `b542facabf656ecf976ce14c185707deb4afbf2ae9c2f6e11e7c9171373cef09` |
| `hacs.json` | `2fd69f483cbef3d0ddf94ed48b9e44b61002e02f266481c400c61bd8b1752890` |
<!--/HASHES-->

## Versionshistorie

Siehe [docs/VERSIONSHISTORIE.md](docs/VERSIONSHISTORIE.md) und die [Releases](https://github.com/Meine-smarte-Welt/fritzbox_ereignisse/releases).

## Lizenz

MIT, siehe [LICENSE](LICENSE).
