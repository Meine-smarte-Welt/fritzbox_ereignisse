# FRITZ!Box Ereignisse

Home-Assistant-Integration (Custom Component), die das FRITZ!Box-eigene
**Ereignisprotokoll** ("System > Ereignisse" in der FRITZ!Box-Oberfläche)
als Sensor mit Dashboard-Karte in Home Assistant anzeigt - Schwester-
Integration zu [FRITZ!Box Anrufe](https://github.com/Meine-smarte-Welt/fritzbox_anrufe).

**Status: v1.0.0 - erste offizielle Version**, veröffentlicht unter
[github.com/Meine-smarte-Welt/fritzbox_ereignisse](https://github.com/Meine-smarte-Welt/fritzbox_ereignisse).
Rückmeldungen (insbesondere FRITZ!OS-Version + welcher Wert im
`source`-Attribut steht + ob Kategorien angezeigt werden) sind als
GitHub-Issue willkommen.

## Voraussetzungen

### 1. TR-064-Zugriff aktivieren

FRITZ!Box-Oberfläche → **Heimnetz → Netzwerk → Netzwerkeinstellungen**
(Reiter) → Häkchen bei **"Zugriff für Anwendungen zulassen"** setzen und
speichern. Ohne diesen Schritt kann die Integration keine Verbindung
aufbauen.

### 2. FRITZ!Box-Benutzerkonto einrichten

Die Integration meldet sich mit einem regulären FRITZ!Box-Benutzerkonto an
(kein separater API-Schlüssel):

1. FRITZ!Box-Oberfläche → **System → FRITZ!Box-Benutzer** →
   "Benutzer hinzufügen" (oder ein bestehendes Konto verwenden).
2. Benutzername und Kennwort vergeben.
3. Unter "Berechtigungen für diesen Benutzer" mindestens
   **"FRITZ!Box-Einstellungen"** ankreuzen (Grundvoraussetzung für
   jeglichen TR-064-Zugriff - dieselbe Berechtigung, die auch
   FRITZ!Box Anrufe für seine Verlaufs-Sensoren benötigt).
4. Speichern.

## Installation

### Über HACS (empfohlen)

1. HACS → Integrationen → drei Punkte oben rechts → "Benutzerdefinierte
   Repositories" → URL `https://github.com/Meine-smarte-Welt/fritzbox_ereignisse`,
   Kategorie "Integration" hinzufügen (falls nicht bereits gelistet).
2. "FRITZ!Box Ereignisse" suchen und herunterladen.
3. Home Assistant **vollständig neu starten** (nicht nur neu laden).

### Manuell

1. Den Ordner `custom_components/fritzbox_ereignisse` aus diesem Repository
   nach `<Home-Assistant-Konfigurationsverzeichnis>/custom_components/fritzbox_ereignisse`
   kopieren.
2. Home Assistant vollständig neu starten.

## Einrichtung

1. Einstellungen → Geräte & Dienste → "+ Integration hinzufügen" →
   "FRITZ!Box Ereignisse" suchen.
2. Zugangsdaten eingeben: Host/IP, Port (Standard **49000**, der reguläre
   TR-064-Port - nicht der Callmonitor-Port 1012 aus FRITZ!Box Anrufe),
   Benutzername, Passwort des oben eingerichteten Kontos.
3. Nach erfolgreicher Einrichtung lässt sich unter "Konfigurieren"
   jederzeit die Verlaufstiefe anpassen (siehe [Einstellungen](#einstellungen)).

## Sensor

Es wird ein Sensor `sensor.fritzbox_ereignisse_ereignisse` angelegt:

| Zustand | Attribut | Bedeutung |
| --- | --- | --- |
| Anzahl gespeicherter Ereignisse | `events` | Liste aller Ereignisse (siehe unten) |
| | `groups` | Liste der im aktuellen Abruf vorkommenden Kategorie-Kürzel |
| | `source` | `query` (dieselbe interne Abfrage wie die Weboberfläche selbst), `xml` (vollständiges Protokoll via TR-064) oder `text` (älterer TR-064-Rückfall) |

Jeder Eintrag in `events` ist ein Objekt mit:

| Feld | Bedeutung |
| --- | --- |
| `id` | Stabile Kennung des Eintrags (von der FRITZ!Box, sonst intern gebildet) |
| `group` | Rohes Kategorie-Kürzel (z. B. `sys`, `internet`, `tel`, `wlan`) |
| `group_label` | Übersetzte Kategorie-Bezeichnung (z. B. "System", "Internet") |
| `date` | Zeitpunkt als ISO-Zeitstempel, falls auswertbar - sonst `null` |
| `date_display` | Zeitpunkt genau wie von der FRITZ!Box geliefert (Rohtext) |
| `message` | Meldungstext |

Der Sensor wird alle 5 Minuten aktualisiert. Zusätzlich feuert die
Integration ein Home-Assistant-Event `fritzbox_ereignisse_new_event`,
sobald ein gegenüber dem vorherigen Abruf neuer Eintrag entdeckt wird -
direkt als Automations-Auslöser nutzbar (Payload: `entry_id`, `id`,
`group`, `group_label`, `date`, `date_display`, `message`). Wie beim
entsprechenden Voicemail-Event in FRITZ!Box Anrufe wird beim allerersten
Abruf nach einem (Neu-)Start bewusst **kein** Event gefeuert, sonst gäbe es
bei jedem Home-Assistant-Neustart Events für längst bekannte Einträge.

## Dashboard-Karte

Die Karte `fritzbox-ereignisse-card` wird automatisch mit der Integration
ausgeliefert und registriert sich selbst als Lovelace-Ressource (kein
manueller Schritt nötig - nur einmal Home Assistant neu starten,
nachdem die Integration installiert/aktualisiert wurde).

```yaml
type: custom:fritzbox-ereignisse-card
entity: sensor.fritzbox_ereignisse_ereignisse
title: FRITZ!Box Ereignisse
show_title: true
max_rows: 15
```

Die Karte zeigt Reiter je Kategorie (mit Icon und Anzahl je Kategorie,
"Alle" zuerst), ein Suchfeld für den Meldungstext sowie die gefilterte
Liste (neueste zuerst). Die Kategorien entsprechen den fünf Reitern der
echten FRITZ!Box-Weboberfläche (Telefonie/Internetverbindung/USB-Geräte/
WLAN/System) - "System" ist dabei bewusst der Auffang-Wert für alles, was
keiner der anderen vier Kategorien zugeordnet werden kann. Nur wenn für
einen Eintrag GAR kein Meldungstext vorliegt, erscheint ein Hinweis in der
Karte und der Eintrag landet unter "Sonstiges".

Über den grafischen Karten-Editor (Zahnrad auf der Karte im
Dashboard-Bearbeitungsmodus) lassen sich Sensor, Titel (inkl. **Titel
komplett ausblenden** über den Schalter "Titel anzeigen"), Zeilenanzahl
sowie - seit Version 1.0.0 - die [Farben](#farben) der Karte einstellen,
ganz ohne YAML.

## Farben

Seit Version 1.0.0 lassen sich die Akzentfarben der Karte über eine
eigene "Farben"-Sektion im grafischen Karten-Editor anpassen (analog zu
[FRITZ!Box Anrufe](https://github.com/Meine-smarte-Welt/fritzbox_anrufe)):
je Farbe ein grafisches Auswahlfeld (öffnet den Farbwähler des
Betriebssystems/Browsers) sowie ein Textfeld für beliebige CSS-Werte
(`var(--irgendeine-theme-farbe)`, `rgb(...)`, `hsl(...)`, CSS-Farbnamen -
alles, was das grafische Feld selbst nicht abbilden kann). Einstellbar
sind die Farbe des aktiven Tabs, eine einheitliche Farbe für alle
Zeilen-Icons sowie je eine eigene Icon-Farbe für die Kategorien
Alle/Telefonie/Internetverbindung/USB-Geräte/WLAN/System (wirkt sowohl im
jeweiligen Tab als auch beim passenden Zeilen-Icon, sofern keine
einheitliche Zeilen-Icon-Farbe gesetzt ist). Ein leeres Feld oder ein
Klick auf "Alle Farben zurücksetzen" stellt die bisherige, feste
Theme-Farbe wieder her. Die Einstellungen werden wie jede andere
Karten-Konfiguration direkt in der jeweiligen Dashboard-Ansicht
gespeichert.

## Einstellungen

Über Einstellungen → Geräte & Dienste → FRITZ!Box Ereignisse →
"Konfigurieren" lässt sich die Verlaufstiefe einstellen - wahlweise:

- **Anzahl Ereignisse** (Standard): 20/50/100/200/500, Standard 100 -
  begrenzt clientseitig, wie viele der von der FRITZ!Box gelieferten
  Einträge im Sensor gehalten werden.
- **Anzahl Tage**: 1-90 Tage, Standard 30 - hält stattdessen alle
  Einträge, deren Zeitpunkt innerhalb der gewählten Anzahl Tage liegt,
  unabhängig davon, wie viele das im Einzelfall sind. Einträge ohne
  auswertbaren Zeitstempel (kann beim älteren Text-Rückfall vorkommen,
  siehe `source`-Attribut) werden in diesem Modus nicht angezeigt, da ihr
  Alter nicht beurteilt werden kann.

## Icon

Home Assistant unterstützt seit Version 2026.3 eigene Marken-Icons für
Custom Integrations über einen `brand/`-Unterordner (`icon.png`,
`logo.png`, jeweils mit `@2x`-Variante) - ganz ohne Eintrag in der
offiziellen `home-assistant/brands`-Sammlung (die für Custom Integrations
inzwischen keine Icons mehr annimmt). Dieses Repository liefert ab
Version 1.0.0 ein eigenes Icon (`brand/icon.png`, `brand/icon@2x.png`,
`brand/logo.png`, `brand/logo@2x.png`) mit aus - es wird ohne weitere
Konfiguration automatisch in der Integrationsliste sowie als Geräte-Icon
verwendet.

**Icon erscheint nicht auf der HACS-Downloads-Seite:** Das ist ein
bekannter, aktuell offener Fehler in HACS selbst, nicht in dieser
Integration. HACS' eigene Downloads-Übersicht lädt Icons weiterhin über
die alte öffentliche CDN (`data-v2.hacs.xyz`/`brands.home-assistant.io`),
kennt den seit Home Assistant 2026.3 unterstützten Weg für inline
mitgelieferte Icons (`brand/`-Ordner, wie oben beschrieben) aber noch
nicht - siehe [hacs/integration#5223](https://github.com/hacs/integration/issues/5223)
und [hacs/integration#5171](https://github.com/hacs/integration/issues/5171).
Wichtig: Das Icon wird davon unabhängig überall sonst in Home Assistant
korrekt angezeigt (Einstellungen → Geräte & Dienste, Geräteseite usw.) -
betroffen ist ausschließlich die HACS-eigene Downloads-Liste, bis die
dortigen Maintainer den Fehler beheben.

## Versionshistorie

- **1.0.0** (erste offizielle Version): eigenes Marken-Icon
  (`brand/icon.png`, `brand/logo.png`, siehe [Icon](#icon));
  Verlaufstiefe wahlweise nach Anzahl ODER Anzahl Tage einstellbar (siehe
  [Einstellungen](#einstellungen)); konfigurierbare Farben für Tabs und
  Zeilen-Icons über einen grafischen Editor-Abschnitt (siehe
  [Farben](#farben)); die Abschnitte "Bekannte Einschränkungen" und
  "Fehlerbehebung" wurden aus dieser README entfernt, da sie
  ausschließlich frühere, inzwischen behobene Probleme dokumentierten
  (siehe die jeweiligen Versionshistorie-Einträge unten für Details zu
  den drei Abrufwegen/der Text-Heuristik).
- **0.4.0**: Nach dem 0.3.0-Update meldete derselbe Nutzer, dass die
  Kategorie "System" weiterhin nicht erscheint, obwohl sie in der echten
  FRITZ!Box-Weboberfläche klar als Reiter sichtbar ist. Ursache: die
  0.3.0-Texterkennung behandelte "System" als ein weiteres, eng
  gefasstes Stichwort-Muster unter mehreren selbst erfundenen
  Zusatzkategorien ("Heimnetz"/"DECT"/"VPN"/"Smart Home"), die auf der
  echten Box gar nicht als eigene Reiter existieren (dort gibt es nur
  Telefonie/Internetverbindung/USB-Geräte/WLAN/System) - viele echte
  System-Meldungen trafen keines der engen Muster und landeten
  fälschlich unter "Sonstiges" statt unter "System". Fix: die
  Texterkennung prüft jetzt nur noch die vier Kategorien, die
  nachweislich als eigene Reiter existieren (Telefonie/
  Internetverbindung/USB-Geräte/WLAN), und ordnet ausnahmslos alles
  andere "System" zu - "System" ist damit der echte Auffang-Wert, exakt
  wie auf der echten Box, statt eine fünfte spezifische Kategorie neben
  "Sonstiges" zu sein. "Sonstiges" tritt dadurch praktisch nur noch bei
  komplett leerem Meldungstext auf.
- **0.3.0**: Ein Nutzer verglich die Karte direkt mit der echten
  FRITZ!Box-Weboberfläche und meldete zwei Probleme: (1) die Karte zeigte
  nur die Kategorie "Sonstiges" statt der auf der Box sichtbaren Reiter
  Telefonie/Internetverbindung/USB-Geräte/WLAN/System, und (2) der
  neueste Eintrag in der Karte war mehrere Stunden älter als in der
  echten Oberfläche. Diagnose: das `source`-Attribut des Sensors stand
  bei diesem Nutzer auf `text` - `X_AVM-DE_GetDeviceLogPath` (Weg 1)
  funktioniert auf dieser FRITZ!Box/Firmware also nicht, und der dann
  laufende textbasierte Rückfall (`GetDeviceLog`, Weg 2) kennt weder
  Kategorien noch liefert er zuverlässig jeden neueren Eintragstyp -
  beide gemeldeten Symptome hatten dieselbe Ursache. Zwei voneinander
  unabhängige Korrekturen: (1) ein neuer, jetzt zuerst versuchter Weg 0
  (`query.lua`, EXPERIMENTELL) - dieselbe interne, sitzungsbasierte
  Abfrage, die auch die FRITZ!Box-Weboberfläche selbst zum Befüllen von
  "System > Ereignisse" nutzt, und damit der plausibelste Weg zu
  tagesaktuellen, vollständigen Daten; (2) eine Text-Heuristik, die
  unabhängig vom Abrufweg versucht, aus dem Meldungstext eine der
  bekannten Kategorien zu erraten, falls die FRITZ!Box selbst keine
  liefert - das behebt "alles landet unter Sonstiges" auch dann, wenn
  Weg 0 sich auf einer bestimmten Hardware als nicht unterstützt
  herausstellt und weiterhin nur der Text-Rückfall läuft. Kategorie-
  Bezeichnungen zusätzlich an die tatsächliche FRITZ!Box-Oberfläche
  angeglichen ("Internetverbindung" statt "Internet", "USB-Geräte" statt
  "USB / Speicher"). Wie bei Weg 1 zuvor: rein defensiv abgesichert -
  schlägt Weg 0 fehl (fehlende Anmeldung, unerwartetes Antwortformat,
  von der Firmware nicht unterstützt, ...), fällt die Integration
  automatisch auf Weg 1 bzw. Weg 2 zurück, nie ein Absturz.
- **0.2.0**: Fix für einen dauerhaften Einrichtungsfehler
  (`not well-formed (invalid token)`), gemeldet von einem Nutzer direkt
  nach der Ersteinrichtung. Ursache: `X_AVM-DE_GetDeviceLogPath` lieferte
  auf dessen FRITZ!Box XML mit einem nicht escapten `&` im Meldungstext;
  der dadurch entstehende `xml.etree.ElementTree.ParseError` wurde bislang
  von keinem der Fehlerbehandlungspfade abgefangen und ließ das komplette
  Setup wiederholt fehlschlagen, obwohl der textbasierte Rückfall
  problemlos funktioniert hätte. Jetzt: (1) ein automatischer
  Reparaturversuch für genau diese Art von XML-Fehlern (bloßer `&`
  escapen, ungültige Steuerzeichen entfernen), (2) jeder verbleibende
  Fehler auf diesem Weg löst zuverlässig den Rückfall auf `GetDeviceLog`
  aus, statt das Setup abstürzen zu lassen.
- **0.1.0**: Initiale Version.
