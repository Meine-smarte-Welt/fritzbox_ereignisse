[🇩🇪 Deutsch](README.md) · [🇬🇧 English](README.en.md) · 🇳🇱 Nederlands · [🇫🇷 Français](README.fr.md) · [🇪🇸 Español](README.es.md)

# FRITZ!Box Gebeurtenissen

Home Assistant-integratie die het **gebeurtenislogboek** van de FRITZ!Box ("Systeem → Gebeurtenissen") toont als sensor en dashboardkaart. Nieuwe meldingen kunnen ook naar het Notification Center worden gestuurd. Zusterintegratie van [FRITZ!Box Gesprekken](https://github.com/Meine-smarte-Welt/fritzbox_anrufe).

**Versie 1.1.0.** Teststatus: zie [Bekende beperkingen](#bekende-beperkingen). De Nederlandse, Franse en Spaanse teksten zijn automatisch vertaald; correcties zijn welkom.

## Functies

- Sensor met alle logboekregels, categorieën zoals in de FRITZ!Box (telefonie, internetverbinding, USB-apparaten, WLAN, systeem)
- Dashboardkaart met tabbladen, zoekfunctie, zoom, `read_only` en instelbare kleuren
- Meldingen naar het Notification Center (schema 1), per meldingstype schakelbaar
- Versieweergave met melding van nieuwe GitHub-releases (controle elke 12 uur)
- Vijf talen: Duits, Engels, Nederlands, Frans, Spaans

## Vereisten

- Home Assistant 2025.8 of nieuwer
- In de FRITZ!Box: **Thuisnetwerk → Netwerk → Netwerkinstellingen → "Toegang voor toepassingen toestaan"** inschakelen
- Een FRITZ!Box-gebruiker met het recht **"FRITZ!Box-instellingen"** (Systeem → FRITZ!Box-gebruikers)

## Installatie

**HACS:** voeg de aangepaste repository `https://github.com/Meine-smarte-Welt/fritzbox_ereignisse` toe (categorie Integratie), download "FRITZ!Box Ereignisse" en herstart Home Assistant.

**Handmatig:** kopieer `custom_components/fritzbox_ereignisse` naar `<config>/custom_components/` en herstart Home Assistant.

## Instellen

Instellingen → Apparaten en diensten → Integratie toevoegen → "FRITZ!Box Ereignisse". Geef host, poort (standaard 49000), gebruikersnaam en wachtwoord op. Onder "Configureren" stel je de geschiedenisdiepte (aantal of dagen) en het Notification Center in.

## De kaart

De kaart wordt met de integratie meegeleverd en registreert zichzelf als Lovelace-resource (in YAML-modus voeg je de resource `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` zelf toe als `module`).

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

Tabbladen: Alle, de vijf categorieën en als laatste het tandwiel (instellingen). Elke categorie kun je in de grafische editor met `show_<categorie>` aan- en uitzetten; minstens één blijft zichtbaar. Een "↑" op het tandwiel toont een nieuwe versie.

## Kleuren

In het editorgedeelte "Farben" (kleurkiezer + tekstveld, "alle kleuren herstellen"). Toegestaan zijn hex, `rgb()`, `hsl()`, `var(--…)` en kleurnamen; al het andere wordt genegeerd.

| Sleutel | Effect |
|---|---|
| `color_tab_active` | actief tabblad |
| `color_row_icon` | alle regelpictogrammen (overschrijft de categoriekleuren) |
| `color_success` / `color_warning` / `color_error` / `color_info` | status (actueel / update of waarschuwing / fout / opmerking) |
| `color_icon_alle`, `_telefonie`, `_internet`, `_usb`, `_wlan`, `_system`, `_settings` | pictogramkleur per categorie |

## Services

Deze integratie biedt geen eigen services.

## Gebeurtenissen

`fritzbox_ereignisse_new_event` wordt afgevuurd zodra een nieuwe regel in het logboek verschijnt (payload: `entry_id`, `id`, `group`, `group_label`, `date`, `date_display`, `message`). Bij het eerste ophalen na het opstarten wordt bewust geen gebeurtenis afgevuurd. Voorbeeld: [`examples/automation_new_event.yaml`](examples/automation_new_event.yaml).

## Sensoren

`sensor.fritzbox_ereignisse_ereignisse` (status = aantal regels). Attributen: `events`, `groups`, `source` (`query`, `xml` of `text`), `app` (versie, updatestatus) en `notification_center`. De grote attributen worden **niet** in de database vastgelegd (verhelpt de recorder-waarschuwing "state attributes exceed 16384 bytes").

## Notification Center

Is het Notification Center geïnstalleerd, dan stuurt de integratie meldingen volgens schema 1. Instelbaar onder "Configureren" en in de kaart (tandwiel → Notification Center, alleen beheerders).

| Meldingstype | Urgentie | Standaard |
|---|---|---|
| Verbinding met FRITZ!Box verbroken (wordt gesloten zodra ophalen weer lukt) | waarschuwing | aan |
| Gebeurtenissen: Systeem, Internetverbinding, USB-apparaten (één melding per nieuwe regel) | info | aan |
| Gebeurtenissen: Telefonie, WLAN | info | uit (veel regels) |

De urgentie van logboekregels is bewust "info", omdat de tekst alleen niet verraadt of een regel een probleem is. Zonder Notification Center gebeurt er niets; meldingen worden verstuurd zodra het is geïnstalleerd.

## Versieweergave en updatemelding

De versie staat op drie plaatsen: kaart → tandwiel → "App-versie", bovenaan de kaarteditor en in het dialoogvenster "Configureren". Bij het starten en daarna elke 12 uur vraagt de integratie `api.github.com` om de nieuwste versie. Een nieuwere versie wordt oranje gemarkeerd. Is GitHub onbereikbaar, dan staat er "Controle niet mogelijk"; al het andere werkt gewoon door.

## Instellingen

- **Geschiedenisdiepte:** aantal gebeurtenissen (20–500, standaard 100) of aantal dagen (1–90, standaard 30)
- **Notification Center:** hoofdschakelaar en één rij per meldingstype

## Beveiliging

Schrijvende acties van de kaart (Notification Center-schakelaars, "Nu controleren") lopen via een WebSocket-actie die de backend alleen voor beheerders toestaat. Alle teksten in de kaart worden gemaskeerd, kleurwaarden gaan via een toegestane lijst. Diagnose bevat geen inloggegevens en geen meldingsteksten. De FRITZ!Box gebruikt een zelfondertekend certificaat; voor het HTTPS-ophalen van het logboek wordt dat daarom niet gecontroleerd (alleen lokaal netwerk).

## Bekende beperkingen

- **Niet getest op een echte FRITZ!Box.** Alleen met gesimuleerde gegevens getest (XML-parser, Notification Center-brug). Meld of issue #1 op jouw box is opgelost (FRITZ!OS-versie en attribuut `source`).
- Samenwerking met een echt Notification Center is niet gecontroleerd.
- Issue #2 ("Custom element doesn't exist") kon niet worden nagebootst. De kaart wordt nu ook via een terugvaloptie geladen en is beveiligd tegen dubbel laden. Helpt dat niet: voeg de resource `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` (type JavaScript-module) handmatig toe en herlaad met Ctrl+F5.
- Bij meerdere FRITZ!Boxen schakelt het tandwiel altijd de eerste vermelding.
- De kaart is niet met testgegevens in een browser doorlopen, alleen syntactisch gecontroleerd.

## Probleemoplossing

- **Kaart niet gevonden:** zie hierboven (resource handmatig toevoegen, Ctrl+F5).
- **Geen regels:** zet debug-logging aan voor `custom_components.fritzbox_ereignisse` en controleer het attribuut `source`.
- **Nieuwe functie ontbreekt na de update:** herstart Home Assistant en wis daarna de browsercache.

## Bestandsintegriteit

Elk `.py`-, `.js`- en `.yaml`-bestand heeft op de eerste regel een SHA-256 van het bestand vanaf regel 2 (`tail -n +2 bestand.py | sha256sum`). Voor JSON-bestanden (geen opmerkingen) geldt deze tabel over het volledige bestand:

<!--HASHES-->
| Datei | SHA-256 |
|---|---|
| `custom_components/fritzbox_ereignisse/icons.json` | `67da9e1131e789f9c2ad831d81f8a524564790995018e9f99ec7b786ce2248ec` |
| `custom_components/fritzbox_ereignisse/manifest.json` | `ff522edb759c85195f495cba46f39cef141645568dd7116d250c1a7bff7b4b72` |
| `custom_components/fritzbox_ereignisse/strings.json` | `4fe7b456dd2cc0662c3d20459fd637f26f305d5761ef722deef4426d796aed66` |
| `custom_components/fritzbox_ereignisse/translations/de.json` | `4fe7b456dd2cc0662c3d20459fd637f26f305d5761ef722deef4426d796aed66` |
| `custom_components/fritzbox_ereignisse/translations/en.json` | `dffe0880e487e99f1f615211ef0ccb70150ef807b561501c7820f5adc47e05a9` |
| `custom_components/fritzbox_ereignisse/translations/es.json` | `e58bf729230fe91a1f25fb39f18bfbf7e97e69754c00243cef71a6047744655d` |
| `custom_components/fritzbox_ereignisse/translations/fr.json` | `e48cc3a08a936c6a8c1021cbcfe52959a9527ef1e0bdbf3cde057a4645cf2b72` |
| `custom_components/fritzbox_ereignisse/translations/nl.json` | `2ceb0276ac22409266b8c6af97ae885e4b275a10d2f99c4da223b820d7133713` |
| `hacs.json` | `2fd69f483cbef3d0ddf94ed48b9e44b61002e02f266481c400c61bd8b1752890` |
<!--/HASHES-->

## Versiegeschiedenis

Zie [docs/VERSIONSHISTORIE.md](docs/VERSIONSHISTORIE.md) (Duits) en [RELEASE_NOTES_v1.1.0.md](RELEASE_NOTES_v1.1.0.md).

## Licentie

MIT, zie [LICENSE](LICENSE).
