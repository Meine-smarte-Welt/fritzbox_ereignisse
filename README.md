# FRITZ!Box Ereignisse

Home-Assistant-Integration (Custom Component), die das FRITZ!Box-eigene
**Ereignisprotokoll** ("System > Ereignisse" in der FRITZ!Box-Oberfläche)
als Sensor mit Dashboard-Karte in Home Assistant anzeigt - Schwester-
Integration zu [FRITZ!Box Anrufe](https://github.com/Meine-smarte-Welt/fritzbox_anrufe).

**Status: v0.4.0.** Die Abfrage versucht der Reihe nach drei Wege, von
denen keiner an dieser Stelle vollständig gegen echte FRITZ!Box-Hardware
verifiziert ist (siehe [Bekannte Einschränkungen](#bekannte-einschränkungen)).
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
| | `source` | `query` (seit v0.3.0, dieselbe interne Abfrage wie die Weboberfläche selbst), `xml` (vollständiges Protokoll via TR-064) oder `text` (älterer TR-064-Rückfall) - siehe [Bekannte Einschränkungen](#bekannte-einschränkungen) |

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

Die Karte zeigt Reiter je Kategorie (mit Anzahl je Kategorie, "Alle"
zuerst), ein Suchfeld für den Meldungstext sowie die gefilterte Liste
(neueste zuerst). Die Kategorien entsprechen den fünf Reitern der echten
FRITZ!Box-Weboberfläche (Telefonie/Internetverbindung/USB-Geräte/WLAN/
System) - "System" ist dabei seit v0.4.0 bewusst der Auffang-Wert für
alles, was keiner der anderen vier Kategorien zugeordnet werden kann
(siehe unten). Nur wenn für einen Eintrag GAR kein Meldungstext vorliegt,
erscheint ein Hinweis in der Karte und der Eintrag landet unter
"Sonstiges".

## Einstellungen

Über Einstellungen → Geräte & Dienste → FRITZ!Box Ereignisse →
"Konfigurieren" lässt sich die **Anzahl gespeicherter Ereignisse**
einstellen (20/50/100/200/500, Standard 100) - begrenzt clientseitig, wie
viele der von der FRITZ!Box gelieferten Einträge im Sensor gehalten
werden.

## Bekannte Einschränkungen

- **Drei Abrufwege.** Die Integration versucht der Reihe nach: (0, seit
  v0.3.0, EXPERIMENTELL) `query.lua` - dieselbe sitzungsbasierte,
  interne Abfrage, die auch die FRITZ!Box-Weboberfläche selbst für
  "System > Ereignisse" verwendet; (1) `X_AVM-DE_GetDeviceLogPath`
  (FRITZ!OS 7.90+, TR-064, liefert das vollständige Protokoll als XML);
  (2) das ältere `GetDeviceLog` (TR-064, liefert nur eine flache
  Textliste ohne native Kategorie - laut Community-Berichten fehlen hier
  sogar einzelne Eintragstypen, z. B. fehlgeschlagene Anmeldeversuche).
  Alle drei Wege sind durch Community-Referenzen belegt (siehe
  Quellcode-Kommentare in `events.py`); Weg 1 wurde durch eine reale
  Nutzerrückmeldung (siehe [Versionshistorie](#versionshistorie), v0.2.0)
  bestätigt grundsätzlich Daten liefern zu können, Weg 0 und Weg 2 bleiben
  bisher unbestätigt. Ein zweiter Nutzerbericht (v0.3.0) legt nahe, dass
  Weg 1 nicht auf jeder FRITZ!Box/Firmware funktioniert und dann
  stillschweigend auf Weg 2 zurückgefallen wird (erkennbar am
  `source`-Attribut, siehe [Sensor](#sensor)) - Weg 0 wurde genau dafür
  ergänzt. Schlagen alle drei Wege fehl, wird der Sensor "nicht
  verfügbar" - bitte mit FRITZ!OS-Version als GitHub-Issue melden.
- **`query.lua` ist ein undokumentierter, interner Endpunkt.** Weg 0
  nutzt denselben Mechanismus, den auch die FRITZ!Box-Weboberfläche
  selbst verwendet, ist aber von AVM nicht öffentlich als stabile
  Schnittstelle dokumentiert und kann sich mit einem Firmware-Update
  jederzeit ändern oder ganz entfallen - schlägt er fehl, greift
  automatisch Weg 1 bzw. Weg 2, kein Fehlerfall.
- **Devicelog-XML kann leicht fehlerhaft sein.** Manche FRITZ!OS-Stände
  liefern bei `X_AVM-DE_GetDeviceLogPath` XML, das einen nicht escapten
  bloßen `&` in einem Meldungstext oder ein laut XML 1.0 ungültiges
  Steuerzeichen enthält. Seit v0.2.0 unternimmt die Integration hierfür
  automatisch einen Reparaturversuch (siehe Versionshistorie); schlägt
  auch dieser fehl, greift automatisch der nächste Weg - kein Fehlerfall.
- **Kategorien sind teils eine Vermutung.** Von der FRITZ!Box selbst
  gelieferte Kürzel (`sys`/`internet`/`tel`/...) werden übernommen; ein
  unbekanntes Kürzel wird nie verworfen, sondern lediglich unübersetzt
  (großgeschrieben) angezeigt. Liefert die FRITZ!Box KEIN Kürzel (das
  betrifft grundsätzlich Weg 2 und ggf. auch Weg 0/1), versucht die
  Integration zusätzlich, die Kategorie anhand des Meldungstexts zu
  erraten: "Anruf"/"Anrufbeantworter"/... -> Telefonie, "WLAN" -> WLAN,
  "USB" -> USB-Geräte, "Internetverbindung"/"DSL-Synchronisierung"/... ->
  Internetverbindung - und seit v0.4.0 **alles, was zu keinem dieser
  vier Muster passt, wird als "System" eingeordnet** (nicht als
  "Sonstiges"), weil das genau der Kategorisierung entspricht, die auch
  die echte FRITZ!Box-Oberfläche selbst verwendet (nur fünf Reiter
  insgesamt: die vier oben plus System als Rest). "Sonstiges" tritt
  dadurch praktisch nur noch bei einem leeren Meldungstext auf. Diese
  Texterkennung basiert ausschließlich auf bekannten, typischen
  FRITZ!Box-Formulierungen (deutsch), ohne Garantie auf Richtigkeit -
  wird eine Telefonie-/Internet-/USB-/WLAN-Meldung fälschlich unter
  "System" einsortiert, gerne mit dem genauen Meldungstext als
  GitHub-Issue melden, damit sich die Mustererkennung erweitern lässt.
- **Kein Löschen/Bearbeiten.** Das FRITZ!Box-Ereignisprotokoll wird
  ausschließlich lesend abgerufen.

## Fehlerbehebung

- **Sensor zeigt `unavailable`**: Kontoberechtigung
  "FRITZ!Box-Einstellungen" prüfen (siehe [Voraussetzungen](#voraussetzungen));
  Fehlermeldung dazu erscheint im Home-Assistant-Log
  (`custom_components.fritzbox_ereignisse`).
- **Karte erscheint nach Update nicht**: Ordner
  `custom_components/fritzbox_ereignisse` komplett neu installieren, Home
  Assistant vollständig neu starten, Browser-Cache leeren (Strg+Shift+R).
- **Alle Ereignisse ohne Kategorie ("Sonstiges")**: seit v0.4.0 praktisch
  ausgeschlossen, außer bei komplett leerem Meldungstext (siehe
  [Bekannte Einschränkungen](#bekannte-einschränkungen)) - jede sonstige
  Meldung landet mindestens unter "System". Erscheint der Hinweis
  trotzdem, gerne mit FRITZ!OS-Version und ein paar Beispiel-
  Meldungstexten als GitHub-Issue melden.
- **Kategorie "System" fehlt/erscheint nicht** (behoben in v0.4.0, siehe
  Versionshistorie): trat auf, weil "System" bis v0.3.0 selbst nur ein
  eng gefasstes Stichwort-Muster war (neben mehreren erfundenen
  Zusatzkategorien, die auf der echten FRITZ!Box gar nicht existieren) -
  viele echte System-Meldungen trafen keines der Muster und landeten
  fälschlich unter "Sonstiges". Auf Version 0.4.0 oder neuer
  aktualisieren und die Integration neu laden - "System" ist jetzt der
  Auffang-Wert für alles, was nicht eindeutig Telefonie/
  Internetverbindung/USB-Geräte/WLAN ist, genau wie auf der echten Box.
- **Ereignisse in der Karte sind älter als in der echten
  FRITZ!Box-Oberfläche** (behoben in v0.3.0, siehe Versionshistorie):
  trat auf, wenn Weg 1 auf der jeweiligen FRITZ!Box/Firmware nicht
  funktionierte und der textbasierte Rückfall (`GetDeviceLog`) bestimmte,
  neuere Eintragstypen gar nicht liefert. Auf Version 0.3.0 oder neuer
  aktualisieren und die Integration neu laden - der neue Weg 0
  (`query.lua`) nutzt dieselbe Abfrage wie die FRITZ!Box-Weboberfläche
  selbst und sollte daher tagesaktuelle Daten liefern, sofern die eigene
  FRITZ!Box/Firmware diesen Weg unterstützt.
- **Einrichtungsfehler "not well-formed (invalid token): line X, column Y"**
  (behoben in v0.2.0): trat auf, wenn das devicelog-XML einen nicht
  escapten `&` oder ein ungültiges Steuerzeichen enthielt - siehe
  [Bekannte Einschränkungen](#bekannte-einschränkungen) und
  [Versionshistorie](#versionshistorie). Auf Version 0.2.0 oder neuer
  aktualisieren und die Integration neu laden (Einstellungen → Geräte &
  Dienste → FRITZ!Box Ereignisse → drei Punkte → "Neu laden" - ein
  vollständiger Neustart ist dafür nicht nötig, nur bei einem
  Datei-Update über HACS/manuell).

## Versionshistorie

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
