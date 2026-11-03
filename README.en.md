[🇩🇪 Deutsch](README.md) · 🇬🇧 English · [🇳🇱 Nederlands](README.nl.md) · [🇫🇷 Français](README.fr.md) · [🇪🇸 Español](README.es.md)

# FRITZ!Box Events

Home Assistant integration that shows the FRITZ!Box **event log** ("System → Events") as a sensor and dashboard card. New entries can also be sent to the Notification Center. Sister integration of [FRITZ!Box Calls](https://github.com/Meine-smarte-Welt/fritzbox_anrufe).

<p>
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Meine-smarte-Welt&amp;repository=fritzbox_ereignisse&amp;category=integration"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open the repository in Home Assistant" height="32"></a>
</p>

![HACS](https://img.shields.io/badge/HACS-Custom-orange)

**Version 1.1.0.** For the test status see [Known limitations](#known-limitations). The Dutch, French and Spanish texts are machine-translated; corrections are welcome. The Notification Center is **experimental** and off by default (see [EXPERIMENTELL.md](EXPERIMENTELL.md), German).

## Features

- Sensor with all event log entries, categories as in the FRITZ!Box (telephony, internet connection, USB devices, Wi-Fi, system)
- Dashboard card with tabs, search, zoom, `read_only` and configurable colours
- Messages to the Notification Center (schema 1), each message type switchable (experimental, off by default)
- Version display with a hint about new GitHub releases (checked every 12 hours)
- Five languages: German, English, Dutch, French, Spanish

## Requirements

- Home Assistant 2025.8 or newer
- In the FRITZ!Box: **Home Network → Network → Network Settings → "Allow access for applications"** enabled
- A FRITZ!Box user with the permission **"FRITZ!Box settings"** (System → FRITZ!Box Users)

## Installation

**HACS:** add the custom repository `https://github.com/Meine-smarte-Welt/fritzbox_ereignisse` (category Integration), download "FRITZ!Box Ereignisse", restart Home Assistant.

**Manual:** copy `custom_components/fritzbox_ereignisse` to `<config>/custom_components/` and restart Home Assistant.

## Setup

Settings → Devices & services → Add integration → "FRITZ!Box Ereignisse". Enter host, port (default 49000), user name and password. Under "Configure" you set the history depth (count or days) and the Notification Center.

## The card

The card ships with the integration and registers itself as a Lovelace resource (in YAML mode add the resource `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` as `module` yourself).

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

Tabs: All, the five categories and, last, the gear (settings). Each category can be switched on and off in the visual editor with `show_<category>`; at least one stays visible. An "↑" on the gear shows a new version.

## Colours

In the editor section "Farben" (colour picker + text field, "reset all colours"). Hex, `rgb()`, `hsl()`, `var(--…)` and colour names are allowed; anything else is discarded.

| Key | Effect |
|---|---|
| `color_tab_active` | active tab |
| `color_row_icon` | all row icons (overrides the category colours) |
| `color_success` / `color_warning` / `color_error` / `color_info` | status (up to date / update or warning / error / hint) |
| `color_icon_alle`, `_telefonie`, `_internet`, `_usb`, `_wlan`, `_system`, `_settings` | icon colour per category |

## Services

This integration provides no services of its own.

## Events

`fritzbox_ereignisse_new_event` is fired when a new entry appears in the log (payload: `entry_id`, `id`, `code`, `group`, `group_label`, `date`, `date_display`, `message`). Deliberately no event is fired on the first fetch after startup. Example: [`examples/automation_new_event.yaml`](examples/automation_new_event.yaml). New in 1.1.0: `id` is now always unique; the original number from the FRITZ!Box is in `code` (if present).

## Sensors

`sensor.fritzbox_ereignisse_ereignisse` (state = number of entries). Attributes: `events`, `groups`, `source` (`query`, `xml` or `text`), `app` (version, update status) and `notification_center`. The large attributes are **not** recorded in the database (fixes the recorder warning "state attributes exceed 16384 bytes"). `notification_center` only appears with `experimental: true` when experimental features are switched on.

## Notification Center

> **Experimental.** This feature is hidden and off by default. To enable: Settings → Devices & services → FRITZ!Box Events → Configure → turn on "Experimental features", then enable the Notification Center in the next step. In the card, also turn on "Show experimental features" in the card editor. Before switching it off, disable the messages in the Notification Center; open messages are not closed when it is switched off. Details: [EXPERIMENTELL.md](EXPERIMENTELL.md) (German).

If the Notification Center is installed, the integration sends messages using schema 1. Configure under "Configure" and in the card (gear → Notification Center, administrators only).

| Message type | Severity | Default |
|---|---|---|
| Connection to FRITZ!Box lost (resolved as soon as fetching works again) | warning | on |
| Events: System, Internet connection, USB devices (one message per new entry) | info | on |
| Events: Telephony, Wi-Fi | info | off (many entries) |

The severity of log entries is deliberately "info" because the message text alone does not reveal whether an entry is a problem. Without the Notification Center nothing happens; messages are sent as soon as it is installed.

## Version display and update hint

The version appears in three places: card → gear → "App version", at the top of the card editor, and in the "Configure" dialog. At startup and every 12 hours the integration asks `api.github.com` for the latest version. A newer one is highlighted in orange. If GitHub cannot be reached it says "Check not possible"; everything else keeps working.

## Settings

- **History depth:** number of events (20–500, default 100) or number of days (1–90, default 30)
- **Experimental features:** master switch (default off); only then the Notification Center appears (master switch and one row per message type)

## Security

Write actions of the card (Notification Center switches, "Check now") use a WebSocket action that the backend allows for administrators only. All texts in the card are escaped, colour values go through an allow-list. Diagnostics contain no credentials and no message texts. The FRITZ!Box uses a self-signed certificate, so it is not verified for the HTTPS log download (local network only).

## Known limitations

- **Not tested on a real FRITZ!Box.** Only simulated data was used (XML parser, shape of the query.lua response, Notification Center bridge). There is no feedback from real installations of this version yet. Please report whether issue #1 is fixed on your box (FRITZ!OS version, the `source` attribute and the debug log; it contains only types and field names, no contents).
- Interaction with a real Notification Center has not been verified, which is why the feature is experimental.
- Issue #2 ("Custom element doesn't exist") could not be reproduced. The card is now additionally loaded through a fallback and is safe against being loaded twice. If it still fails: add the resource `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` (type JavaScript module) manually and reload with Ctrl+F5. Issue #3 (404 when loading the card) probably had the same cause: 1.1.0 was first only a pre-release, so HACS keeps offering 1.0.0. This is not confirmed.
- With several FRITZ!Boxes the gear always switches the first entry.
- The card was exercised in headless Chrome with test data, but not in a real Home Assistant.

## Troubleshooting

- **Card not found:** see above (add the resource manually, Ctrl+F5).
- **No entries:** enable debug logging for `custom_components.fritzbox_ereignisse` and check the `source` attribute.
- **New feature missing after the update:** restart Home Assistant, then clear the browser cache.

## File integrity

Every `.py`, `.js` and `.yaml` file carries a SHA-256 of the file from line 2 in its first line (`tail -n +2 file.py | sha256sum`). For JSON files (no comments) this table covers the complete file:

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

## Version history

See [docs/VERSIONSHISTORIE.md](docs/VERSIONSHISTORIE.md) (German) and the [releases](https://github.com/Meine-smarte-Welt/fritzbox_ereignisse/releases).

## License

MIT, see [LICENSE](LICENSE).
