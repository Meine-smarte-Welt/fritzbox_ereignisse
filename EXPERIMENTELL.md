# Experimentelle Funktionen

Experimentelle Funktionen sind **nicht geprüft**. Sie sind standardmäßig ausgeblendet und aus. Ob eine Funktion geprüft ist, entscheidet allein Thorsten nach eigenem Test.

**So schaltest du sie ein:**
1. Integration: Einstellungen → Geräte & Dienste → FRITZ!Box Ereignisse → Konfigurieren → "Experimentelle Funktionen" aktivieren, dann im nächsten Schritt die einzelne Funktion einschalten.
2. Karte: im Karten-Editor die Gruppe "Experimentell" öffnen und "Experimentelle Funktionen anzeigen" aktivieren (`show_experimental: true`).

## Aktuell experimentell

| Funktion | Schlüssel | Seit | Warum experimentell | Testschritte |
|---|---|---|---|---|
| Notification Center | `notification_center` | 1.1.0 | Nur gegen simulierte Daten geprüft, nicht mit einem echten Notification Center. | 1. Experimentelle Funktionen in der Integration einschalten, Notification Center aktivieren. 2. In der Karte (Zahnrad → Notification Center) "Verbindung verloren" einschalten und prüfen, ob die Meldung erscheint. 3. Einen Eintrag der Art "System" auslösen und prüfen, ob genau eine Meldung ankommt. 4. Verbindung wiederherstellen und prüfen, ob die Verbindungsmeldung geschlossen wird. 5. Rückmeldung mit FRITZ!OS-Version geben. |

**Vor dem Abschalten:** Schalte zuerst die Meldungsarten im Notification Center aus. Beim Abschalten der experimentellen Funktionen werden offene Meldungen nicht geschlossen.

## Geprüft (ehemals experimentell)

Noch keine.
