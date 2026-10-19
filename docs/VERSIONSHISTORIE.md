# Versionshistorie

Zurück zur [README](../README.md).

- **1.1.0**: Behebt die Issues #1 und #2, sendet Meldungen ans Notification Center, zeigt die Version samt Update-Hinweis an und bringt die Karte in fünf Sprachen. Details: [Release Note](../RELEASE_NOTES_v1.1.0.md).

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
