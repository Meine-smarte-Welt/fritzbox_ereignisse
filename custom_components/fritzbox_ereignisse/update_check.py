# SHA256 (Inhalt ab Zeile 2, d.h. dieser Datei ohne diese erste Zeile): 5e4cdedbd359096b5a0d534c034d28b8465e9317395644cb33e6832a19440804
"""GitHub-Versionsabfrage (Pflicht laut Design-Master, Abschnitt 6).

Beim Start und danach alle 12 Stunden wird bei GitHub nach der neuesten
Version gefragt. Ergebnis: ``latest_version``, ``release_url``,
``update_available``, ``checked_at``, ``check_failed``.

* Normale Version (z. B. ``1.1.0``): ``releases/latest`` (liefert nie
  Pre-releases), ersatzweise das höchste Versions-Tag.
* Beta/Release Candidate (z. B. ``1.1.0b1``, ``1.1.0rc1``): zusätzlich die
  Liste ``releases?per_page=5``, sonst erfährt ein Beta-Nutzer nie von der
  nächsten Beta.
* GitHub nicht erreichbar: ``check_failed`` = ``True``, die Karte läuft
  normal weiter.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import logging
import re
from typing import Any, Final

from aiohttp import ClientTimeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import GITHUB_RELEASES_URL, GITHUB_REPO

_LOGGER = logging.getLogger(__name__)

CHECK_INTERVAL: Final = timedelta(hours=12)
REQUEST_TIMEOUT: Final = 15
API_BASE: Final = f"https://api.github.com/repos/{GITHUB_REPO}"
GITHUB_URL_PREFIX: Final = "https://github.com/"

_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-.]?(a|b|rc)(\d+))?$", re.IGNORECASE)
_STAGE_RANK: Final = {"a": 0, "b": 1, "rc": 2}
_FINAL_RANK: Final = 3

VersionKey = tuple[int, int, int, int, int]


def parse_version(text: str | None) -> VersionKey | None:
    """Versionstext (``v1.2.3``, ``1.2.3b1``, ``1.2.3rc2``) in einen Sortierschlüssel."""
    match = _VERSION_RE.match((text or "").strip())
    if not match:
        return None
    major, minor, patch, stage, number = match.groups()
    if stage is None:
        return (int(major), int(minor), int(patch), _FINAL_RANK, 0)
    return (int(major), int(minor), int(patch), _STAGE_RANK[stage.lower()], int(number))


def is_prerelease(text: str | None) -> bool:
    """True bei Beta/Release-Candidate (``b``/``rc``/``a``)."""
    key = parse_version(text)
    return key is not None and key[3] != _FINAL_RANK


def safe_release_url(url: object) -> str:
    """Release-Link nur, wenn er auf github.com zeigt, sonst die Releases-Seite."""
    if isinstance(url, str) and url.startswith(GITHUB_URL_PREFIX):
        return url
    return GITHUB_RELEASES_URL


def format_update_info(data: dict[str, Any], language: str) -> str:
    """Kurzer, mehrsprachiger Statustext für den Optionen-Dialog."""
    texts = {
        "de": ("Noch nicht geprüft.", "Prüfung nicht möglich.", "Du hast die neueste Version.",
               "Neue Version {latest} verfügbar: {url}"),
        "en": ("Not checked yet.", "Check not possible.", "You are on the latest version.",
               "New version {latest} available: {url}"),
        "nl": ("Nog niet gecontroleerd.", "Controle niet mogelijk.", "Je hebt de nieuwste versie.",
               "Nieuwe versie {latest} beschikbaar: {url}"),
        "fr": ("Pas encore vérifié.", "Vérification impossible.", "Tu utilises la dernière version.",
               "Nouvelle version {latest} disponible : {url}"),
        "es": ("Aún no comprobado.", "Comprobación no posible.", "Tienes la última versión.",
               "Nueva versión {latest} disponible: {url}"),
    }
    not_checked, failed, current, available = texts.get(language[:2], texts["en"])
    if data.get("check_failed"):
        return failed
    if not data.get("checked_at"):
        return not_checked
    if data.get("update_available"):
        return available.format(latest=data.get("latest_version"), url=data.get("release_url"))
    return current


class UpdateChecker:
    """Fragt GitHub nach der neuesten Version und hält das Ergebnis."""

    def __init__(
        self,
        hass: HomeAssistant,
        current_version: str,
        *,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        self.hass = hass
        self.current_version = current_version
        self._on_change = on_change
        self.latest_version: str | None = None
        self.release_url: str = GITHUB_RELEASES_URL
        self.update_available = False
        self.checked_at: datetime | None = None
        self.check_failed = False

    def as_dict(self) -> dict[str, Any]:
        """Für die Sensor-Attribute und die Diagnose."""
        return {
            "version": self.current_version,
            "latest_version": self.latest_version,
            "release_url": self.release_url,
            "update_available": self.update_available,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
            "check_failed": self.check_failed,
        }

    @callback
    def async_start(self, entry: ConfigEntry) -> None:
        """Erste Prüfung im Hintergrund, danach alle 12 Stunden."""
        entry.async_create_background_task(
            self.hass, self.async_check(), name="fritzbox_ereignisse update check"
        )
        unsub: CALLBACK_TYPE = async_track_time_interval(
            self.hass, self._async_interval, CHECK_INTERVAL
        )
        entry.async_on_unload(unsub)

    async def _async_interval(self, _now: datetime) -> None:
        await self.async_check()

    async def async_check(self) -> None:
        """Eine Abfrage ausführen (nie eine Ausnahme nach außen)."""
        try:
            latest, url = await self._async_fetch_latest()
        except Exception as ex:  # noqa: BLE001 - die Karte läuft auch ohne Prüfung
            _LOGGER.debug("Update-Prüfung fehlgeschlagen (%s: %s)", type(ex).__name__, ex)
            self.check_failed = True
            self.checked_at = dt_util.utcnow()
        else:
            self.check_failed = False
            self.checked_at = dt_util.utcnow()
            self.latest_version = latest
            self.release_url = url
            current_key = parse_version(self.current_version)
            latest_key = parse_version(latest)
            self.update_available = (
                current_key is not None and latest_key is not None and latest_key > current_key
            )
        if self._on_change is not None:
            self._on_change()

    async def _async_get_json(self, path: str) -> Any:
        session = async_get_clientsession(self.hass)
        async with session.get(
            f"{API_BASE}/{path}",
            headers={"Accept": "application/vnd.github+json"},
            timeout=ClientTimeout(total=REQUEST_TIMEOUT),
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def _async_fetch_latest(self) -> tuple[str, str]:
        """Neueste Version und Release-Link ermitteln."""
        candidates: list[tuple[VersionKey, str, str]] = []

        if is_prerelease(self.current_version):
            releases = await self._async_get_json("releases?per_page=5")
            for release in releases if isinstance(releases, list) else []:
                if release.get("draft"):
                    continue
                tag = str(release.get("tag_name") or "")
                key = parse_version(tag)
                if key is not None:
                    candidates.append((key, tag, safe_release_url(release.get("html_url"))))
        else:
            try:
                release = await self._async_get_json("releases/latest")
                tag = str(release.get("tag_name") or "")
                key = parse_version(tag)
                if key is not None:
                    candidates.append((key, tag, safe_release_url(release.get("html_url"))))
            except Exception as ex:  # noqa: BLE001 - Rückfall auf Tags
                _LOGGER.debug("releases/latest nicht nutzbar (%s) - versuche Tags", ex)

        if not candidates:
            tags = await self._async_get_json("tags?per_page=20")
            for item in tags if isinstance(tags, list) else []:
                tag = str(item.get("name") or "")
                key = parse_version(tag)
                if key is not None and (is_prerelease(self.current_version) or key[3] == _FINAL_RANK):
                    candidates.append((key, tag, f"{GITHUB_RELEASES_URL}/tag/{tag}"))

        if not candidates:
            raise ValueError("Keine Version gefunden")
        _, tag, url = max(candidates, key=lambda item: item[0])
        return tag.lstrip("vV"), url
