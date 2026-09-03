# FRITZ!Box Ereignisse

Home-Assistant-Integration (Custom Component), die das FRITZ!Box-eigene
**Ereignisprotokoll** ("System > Ereignisse" in der FRITZ!Box-Oberfläche)
als Sensor mit Dashboard-Karte in Home Assistant anzeigt - Schwester-
Integration zu [FRITZ!Box Anrufe](https://github.com/Meine-smarte-Welt/fritzbox_anrufe).

**Status: v0.2.0.** Die Abfrage nutzt zwei dokumentierte, aber an dieser
Stelle noch NICHT vollständig gegen echte FRITZ!Box-Hardware verifizierte
TR-064-Wege (siehe [Bekannte Einschränkungen](#bekannte-einschränkungen)).
Rückmeldungen (insbesondere FRITZ!OS-Version + ob Kategorien angezeigt
werden) sind als GitHub-Issue willkommen.

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
| | `source` | `xml` (vollständiges, kategorisiertes Protokoll) oder `text` (älterer Rückfall ohne Kategorie) |

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
(neueste zuerst). Liefert die FRITZ!OS-Version keine Kategorien (Rückfall
`GetDeviceLog`, siehe unten), erscheint ein Hinweis in der Karte, und alle
Einträge werden unter "Sonstiges" geführt.

## Einstellungen

Über Einstellungen → Geräte & Dienste → FRITZ!Box Ereignisse →
"Konfigurieren" lässt sich die **Anzahl gespeicherter Ereignisse**
einstellen (20/50/100/200/500, Standard 100) - begrenzt clientseitig, wie
viele der von der FRITZ!Box gelieferten Einträge im Sensor gehalten
werden.

## Bekannte Einschränkungen

- **Zwei TR-064-Wege.** Die Integration versucht zuerst
  `X_AVM-DE_GetDeviceLogPath` (FRITZ!OS 7.90+, liefert das vollständige,
  kategorisierte Protokoll als XML), und fällt bei Fehlschlag auf das
  ältere `GetDeviceLog` zurück (liefert nur eine flache Textliste ohne
  Kategorie - laut Community-Berichten fehlen hier sogar einzelne
  Eintragstypen, z. B. fehlgeschlagene Anmeldeversuche). Beide Aktionen
  sind öffentlich dokumentiert bzw. durch Community-Referenzen belegt
  (siehe Quellcode-Kommentare in `events.py`); Weg 1 wurde inzwischen
  durch eine reale Nutzerrückmeldung (siehe
  [Versionshistorie](#versionshistorie), v0.2.0) bestätigt tatsächlich
  Daten zu liefern, Weg 2 bleibt bisher unbestätigt. Schlagen beide Wege
  fehl, wird der Sensor "nicht verfügbar" - bitte mit FRITZ!OS-Version als
  GitHub-Issue melden.
- **Devicelog-XML kann leicht fehlerhaft sein.** Manche FRITZ!OS-Stände
  liefern bei `X_AVM-DE_GetDeviceLogPath` XML, das einen nicht escapten
  bloßen `&` in einem Meldungstext oder ein laut XML 1.0 ungültiges
  Steuerzeichen enthält. Seit v0.2.0 unternimmt die Integration hierfür
  automatisch einen Reparaturversuch (siehe Versionshistorie); schlägt
  auch dieser fehl, greift automatisch der textbasierte Rückfall
  (`GetDeviceLog`) - kein Fehlerfall, nur mit weniger Details (keine
  Kategorien).
- **Kategorie-Bezeichnungen sind eine Vermutung.** Welche Kürzel
  (`sys`/`internet`/`tel`/...) eine reale FRITZ!Box tatsächlich liefert,
  konnte in dieser Entwicklungsumgebung nicht gegen Hardware geprüft
  werden - ein unbekanntes Kürzel wird nie verworfen, sondern lediglich
  unübersetzt (großgeschrieben) angezeigt.
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
- **Alle Ereignisse ohne Kategorie ("Sonstiges")**: die FRITZ!OS-Version
  liefert vermutlich `X_AVM-DE_GetDeviceLogPath` nicht - die Integration
  läuft dann im textbasierten Rückfall (siehe
  [Bekannte Einschränkungen](#bekannte-einschränkungen)). Kein Fehler,
  aber gerne mit FRITZ!OS-Version als GitHub-Issue melden, damit sich die
  Verbreitung einschätzen lässt.
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
