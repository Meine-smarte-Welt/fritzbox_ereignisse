[🇩🇪 Deutsch](README.md) · [🇬🇧 English](README.en.md) · [🇳🇱 Nederlands](README.nl.md) · 🇫🇷 Français · [🇪🇸 Español](README.es.md)

# FRITZ!Box Événements

Intégration Home Assistant qui affiche le **journal des événements** de la FRITZ!Box (« Système → Événements ») sous forme de capteur et de carte de tableau de bord. Les nouvelles entrées peuvent aussi être envoyées au Notification Center. Intégration sœur de [FRITZ!Box Appels](https://github.com/Meine-smarte-Welt/fritzbox_anrufe).

<p>
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Meine-smarte-Welt&amp;repository=fritzbox_ereignisse&amp;category=integration"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Ouvrir le dépôt dans Home Assistant" height="32"></a>
</p>

![HACS](https://img.shields.io/badge/HACS-Custom-orange)

**Version 1.1.0.** État des tests : voir [Limites connues](#limites-connues). Les textes néerlandais, français et espagnols sont traduits automatiquement ; les corrections sont bienvenues. Le Notification Center est **expérimental** et désactivé par défaut (voir [EXPERIMENTELL.md](EXPERIMENTELL.md), en allemand).

## Fonctions

- Capteur avec toutes les entrées du journal, catégories comme dans la FRITZ!Box (téléphonie, connexion Internet, appareils USB, Wi-Fi, système)
- Carte avec onglets, recherche, zoom, `read_only` et couleurs réglables
- Messages vers le Notification Center (schéma 1), activables par type de message (expérimental, désactivé par défaut)
- Affichage de la version avec indication des nouvelles versions GitHub (vérification toutes les 12 heures)
- Cinq langues : allemand, anglais, néerlandais, français, espagnol

## Prérequis

- Home Assistant 2025.8 ou plus récent
- Dans la FRITZ!Box : **Réseau domestique → Réseau → Paramètres réseau → « Autoriser l'accès pour les applications »** activé
- Un utilisateur FRITZ!Box avec le droit **« Paramètres de la FRITZ!Box »** (Système → Utilisateurs FRITZ!Box)

## Installation

**HACS :** ajoute le dépôt personnalisé `https://github.com/Meine-smarte-Welt/fritzbox_ereignisse` (catégorie Intégration), télécharge « FRITZ!Box Ereignisse » et redémarre Home Assistant.

**Manuelle :** copie `custom_components/fritzbox_ereignisse` dans `<config>/custom_components/` et redémarre Home Assistant.

## Configuration

Paramètres → Appareils et services → Ajouter une intégration → « FRITZ!Box Ereignisse ». Saisis l'hôte, le port (49000 par défaut), le nom d'utilisateur et le mot de passe. Sous « Configurer », tu règles la profondeur de l'historique (nombre ou jours) et le Notification Center.

## La carte

La carte est fournie avec l'intégration et s'enregistre elle-même comme ressource Lovelace (en mode YAML, ajoute toi-même la ressource `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` de type `module`).

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

Onglets : Tous, les cinq catégories et, en dernier, la roue dentée (paramètres). Chaque catégorie peut être activée ou désactivée dans l'éditeur graphique avec `show_<catégorie>` ; une au moins reste visible. Un « ↑ » sur la roue dentée signale une nouvelle version.

## Couleurs

Dans la section « Farben » de l'éditeur (sélecteur de couleur + champ texte, « réinitialiser toutes les couleurs »). Hex, `rgb()`, `hsl()`, `var(--…)` et noms de couleurs sont autorisés ; le reste est rejeté.

| Clé | Effet |
|---|---|
| `color_tab_active` | onglet actif |
| `color_row_icon` | toutes les icônes de ligne (remplace les couleurs de catégorie) |
| `color_success` / `color_warning` / `color_error` / `color_info` | statut (à jour / mise à jour ou avertissement / erreur / remarque) |
| `color_icon_alle`, `_telefonie`, `_internet`, `_usb`, `_wlan`, `_system`, `_settings` | couleur d'icône par catégorie |

## Services

Cette intégration ne fournit pas de services propres.

## Événements

`fritzbox_ereignisse_new_event` est déclenché dès qu'une nouvelle entrée apparaît dans le journal (charge utile : `entry_id`, `id`, `code`, `group`, `group_label`, `date`, `date_display`, `message`). Aucun événement n'est volontairement déclenché lors de la première récupération après le démarrage. Exemple : [`examples/automation_new_event.yaml`](examples/automation_new_event.yaml). Nouveau dans 1.1.0 : `id` est désormais toujours unique ; le numéro d'origine de la FRITZ!Box se trouve dans `code` (si présent).

## Capteurs

`sensor.fritzbox_ereignisse_ereignisse` (état = nombre d'entrées). Attributs : `events`, `groups`, `source` (`query`, `xml` ou `text`), `app` (version, état de la mise à jour) et `notification_center`. Les gros attributs ne sont **pas** enregistrés dans la base de données (corrige l'avertissement du recorder « state attributes exceed 16384 bytes »). `notification_center` n'apparaît qu'avec `experimental: true` lorsque les fonctions expérimentales sont activées.

## Notification Center

> **Expérimental.** Cette fonction est masquée et désactivée par défaut. Activation : Paramètres → Appareils et services → FRITZ!Box Ereignisse → Configurer → activer « Fonctions expérimentales », puis activer le Notification Center à l'étape suivante. Dans la carte, activer aussi « Afficher les fonctions expérimentales » dans l'éditeur de carte. Avant de désactiver, coupe les messages dans le Notification Center ; les messages ouverts ne sont pas fermés à la désactivation. Détails : [EXPERIMENTELL.md](EXPERIMENTELL.md) (en allemand).

Si le Notification Center est installé, l'intégration envoie des messages selon le schéma 1. Réglage sous « Configurer » et dans la carte (roue dentée → Notification Center, administrateurs uniquement).

| Type de message | Urgence | Par défaut |
|---|---|---|
| Connexion à la FRITZ!Box perdue (résolu dès que la récupération refonctionne) | avertissement | activé |
| Événements : Système, Connexion Internet, Appareils USB (un message par nouvelle entrée) | info | activé |
| Événements : Téléphonie, Wi-Fi | info | désactivé (beaucoup d'entrées) |

L'urgence des entrées du journal est volontairement « info », car le texte seul ne dit pas si une entrée est un problème. Sans Notification Center, rien ne se passe ; les messages sont envoyés dès son installation.

## Affichage de la version et avis de mise à jour

La version apparaît à trois endroits : carte → roue dentée → « Version de l'app », en haut de l'éditeur de carte et dans la boîte « Configurer ». Au démarrage, puis toutes les 12 heures, l'intégration interroge `api.github.com` pour la dernière version. Une version plus récente est mise en évidence en orange. Si GitHub est injoignable, « Vérification impossible » s'affiche ; le reste fonctionne normalement.

## Paramètres

- **Profondeur de l'historique :** nombre d'événements (20–500, 100 par défaut) ou nombre de jours (1–90, 30 par défaut)
- **Fonctions expérimentales :** interrupteur général (désactivé par défaut) ; ensuite seulement le Notification Center apparaît (interrupteur général et une ligne par type de message)

## Sécurité

Les actions d'écriture de la carte (interrupteurs du Notification Center, « Vérifier maintenant ») passent par une action WebSocket que le backend n'autorise qu'aux administrateurs. Tous les textes de la carte sont échappés, les valeurs de couleur passent par une liste autorisée. Le diagnostic ne contient ni identifiants ni textes de messages. La FRITZ!Box utilise un certificat auto-signé ; il n'est donc pas vérifié pour le téléchargement HTTPS du journal (réseau local uniquement).

## Limites connues

- **Non testé sur une vraie FRITZ!Box.** Seules des données simulées ont servi (analyseur XML, forme de la réponse query.lua, pont Notification Center). Aucun retour d'installations réelles de cette version pour l'instant. Indique si le problème n° 1 est corrigé sur ta box (version de FRITZ!OS, attribut `source` et journal de débogage ; il ne contient que des types et des noms de champs, pas de contenu).
- L'interaction avec un vrai Notification Center n'a pas été vérifiée, c'est pourquoi la fonction est expérimentale.
- Le problème n° 2 (« Custom element doesn't exist ») n'a pas pu être reproduit. La carte est maintenant aussi chargée par un mécanisme de repli et protégée contre un double chargement. Si cela ne suffit pas : ajoute manuellement la ressource `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` (type module JavaScript) et recharge avec Ctrl+F5. Le problème n° 3 (404 au chargement de la carte) avait probablement la même cause : 1.1.0 n'était d'abord qu'une préversion, HACS continue donc de proposer 1.0.0. Non confirmé.
- Avec plusieurs FRITZ!Box, la roue dentée agit toujours sur la première entrée.
- La carte a été essayée dans un Chrome sans interface avec des données de test, mais pas dans un vrai Home Assistant.

## Dépannage

- **Carte introuvable :** voir ci-dessus (ajouter la ressource manuellement, Ctrl+F5).
- **Aucune entrée :** active le journal de débogage pour `custom_components.fritzbox_ereignisse` et vérifie l'attribut `source`.
- **Nouvelle fonction absente après la mise à jour :** redémarre Home Assistant, puis vide le cache du navigateur.

## Intégrité des fichiers

Chaque fichier `.py`, `.js` et `.yaml` porte sur sa première ligne un SHA-256 du fichier à partir de la ligne 2 (`tail -n +2 fichier.py | sha256sum`). Pour les fichiers JSON (sans commentaires), ce tableau couvre le fichier entier :

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

## Historique des versions

Voir [docs/VERSIONSHISTORIE.md](docs/VERSIONSHISTORIE.md) (allemand) et les [releases](https://github.com/Meine-smarte-Welt/fritzbox_ereignisse/releases).

## Licence

MIT, voir [LICENSE](LICENSE).
