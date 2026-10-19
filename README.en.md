[🇩🇪 Deutsch](README.md) · 🇬🇧 English · [🇳🇱 Nederlands](README.nl.md) · [🇫🇷 Français](README.fr.md) · [🇪🇸 Español](README.es.md)

# FRITZ!Box Events

Home Assistant integration that shows the FRITZ!Box **event log** ("System → Events") as a sensor and dashboard card. New entries can also be sent to the Notification Center. Sister integration of [FRITZ!Box Calls](https://github.com/Meine-smarte-Welt/fritzbox_anrufe).

**Version 1.1.0.** For the test status see [Known limitations](#known-limitations). The Dutch, French and Spanish texts are machine-translated; corrections are welcome.

## Features

- Sensor with all event log entries, categories as in the FRITZ!Box (telephony, internet connection, USB devices, Wi-Fi, system)
- Dashboard card with tabs, search, zoom, `read_only` and configurable colours
- Messages to the Notification Center (schema 1), each message type switchable
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

`fritzbox_ereignisse_new_event` is fired when a new entry appears in the log (payload: `entry_id`, `id`, `group`, `group_label`, `date`, `date_display`, `message`). Deliberately no event is fired on the first fetch after startup. Example: [`examples/automation_new_event.yaml`](examples/automation_new_event.yaml).

## Sensors

`sensor.fritzbox_ereignisse_ereignisse` (state = number of entries). Attributes: `events`, `groups`, `source` (`query`, `xml` or `text`), `app` (version, update status) and `notification_center`. The large attributes are **not** recorded in the database (fixes the recorder warning "state attributes exceed 16384 bytes").

## Notification Center

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
- **Notification Center:** master switch and one row per message type

## Security

Write actions of the card (Notification Center switches, "Check now") use a WebSocket action that the backend allows for administrators only. All texts in the card are escaped, colour values go through an allow-list. Diagnostics contain no credentials and no message texts. The FRITZ!Box uses a self-signed certificate, so it is not verified for the HTTPS log download (local network only).

## Known limitations

- **Not tested on a real FRITZ!Box.** Only simulated data was used (XML parser, Notification Center bridge). Please report whether issue #1 is fixed on your box (FRITZ!OS version and the `source` attribute).
- Interaction with a real Notification Center has not been verified.
- Issue #2 ("Custom element doesn't exist") could not be reproduced. The card is now additionally loaded through a fallback and is safe against being loaded twice. If it still fails: add the resource `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` (type JavaScript module) manually and reload with Ctrl+F5.
- With several FRITZ!Boxes the gear always switches the first entry.
- The card was not exercised in a browser with test data, only syntax-checked.

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
| `custom_components/fritzbox_ereignisse/strings.json` | `4fe7b456dd2cc0662c3d20459fd637f26f305d5761ef722deef4426d796aed66` |
| `custom_components/fritzbox_ereignisse/translations/de.json` | `4fe7b456dd2cc0662c3d20459fd637f26f305d5761ef722deef4426d796aed66` |
| `custom_components/fritzbox_ereignisse/translations/en.json` | `dffe0880e487e99f1f615211ef0ccb70150ef807b561501c7820f5adc47e05a9` |
| `custom_components/fritzbox_ereignisse/translations/es.json` | `e58bf729230fe91a1f25fb39f18bfbf7e97e69754c00243cef71a6047744655d` |
| `custom_components/fritzbox_ereignisse/translations/fr.json` | `e48cc3a08a936c6a8c1021cbcfe52959a9527ef1e0bdbf3cde057a4645cf2b72` |
| `custom_components/fritzbox_ereignisse/translations/nl.json` | `2ceb0276ac22409266b8c6af97ae885e4b275a10d2f99c4da223b820d7133713` |
| `hacs.json` | `2fd69f483cbef3d0ddf94ed48b9e44b61002e02f266481c400c61bd8b1752890` |
<!--/HASHES-->

## Version history

See [docs/VERSIONSHISTORIE.md](docs/VERSIONSHISTORIE.md) (German) and [RELEASE_NOTES_v1.1.0.md](RELEASE_NOTES_v1.1.0.md).

## License

MIT, see [LICENSE](LICENSE).
