[🇩🇪 Deutsch](README.md) · [🇬🇧 English](README.en.md) · [🇳🇱 Nederlands](README.nl.md) · [🇫🇷 Français](README.fr.md) · 🇪🇸 Español

# FRITZ!Box Eventos

Integración de Home Assistant que muestra el **registro de eventos** de la FRITZ!Box («Sistema → Eventos») como sensor y tarjeta de panel. Las entradas nuevas también pueden enviarse al Notification Center. Integración hermana de [FRITZ!Box Llamadas](https://github.com/Meine-smarte-Welt/fritzbox_anrufe).

**Versión 1.1.0.** Estado de las pruebas: véase [Limitaciones conocidas](#limitaciones-conocidas). Los textos en neerlandés, francés y español están traducidos automáticamente; se agradecen las correcciones.

## Funciones

- Sensor con todas las entradas del registro, categorías como en la FRITZ!Box (telefonía, conexión a Internet, dispositivos USB, Wi-Fi, sistema)
- Tarjeta con pestañas, búsqueda, zoom, `read_only` y colores configurables
- Avisos al Notification Center (esquema 1), activables por tipo de aviso
- Indicación de versión con aviso de nuevas versiones en GitHub (comprobación cada 12 horas)
- Cinco idiomas: alemán, inglés, neerlandés, francés, español

## Requisitos

- Home Assistant 2025.8 o posterior
- En la FRITZ!Box: **Red doméstica → Red → Configuración de red → «Permitir acceso a aplicaciones»** activado
- Un usuario de la FRITZ!Box con el permiso **«Configuración de la FRITZ!Box»** (Sistema → Usuarios de FRITZ!Box)

## Instalación

**HACS:** añade el repositorio personalizado `https://github.com/Meine-smarte-Welt/fritzbox_ereignisse` (categoría Integración), descarga «FRITZ!Box Ereignisse» y reinicia Home Assistant.

**Manual:** copia `custom_components/fritzbox_ereignisse` a `<config>/custom_components/` y reinicia Home Assistant.

## Configuración

Ajustes → Dispositivos y servicios → Añadir integración → «FRITZ!Box Ereignisse». Introduce host, puerto (49000 por defecto), usuario y contraseña. En «Configurar» ajustas la profundidad del historial (número o días) y el Notification Center.

## La tarjeta

La tarjeta se entrega con la integración y se registra sola como recurso de Lovelace (en modo YAML añade tú mismo el recurso `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` como `module`).

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

Pestañas: Todos, las cinco categorías y, al final, la rueda dentada (ajustes). Cada categoría se puede activar o desactivar en el editor gráfico con `show_<categoría>`; al menos una permanece visible. Una «↑» en la rueda dentada indica una versión nueva.

## Colores

En la sección «Farben» del editor (selector de color + campo de texto, «restablecer todos los colores»). Se permiten hex, `rgb()`, `hsl()`, `var(--…)` y nombres de color; lo demás se descarta.

| Clave | Efecto |
|---|---|
| `color_tab_active` | pestaña activa |
| `color_row_icon` | todos los iconos de fila (sustituye los colores por categoría) |
| `color_success` / `color_warning` / `color_error` / `color_info` | estado (actualizado / actualización o advertencia / error / aviso) |
| `color_icon_alle`, `_telefonie`, `_internet`, `_usb`, `_wlan`, `_system`, `_settings` | color de icono por categoría |

## Servicios

Esta integración no ofrece servicios propios.

## Eventos

`fritzbox_ereignisse_new_event` se dispara cuando aparece una entrada nueva en el registro (carga: `entry_id`, `id`, `group`, `group_label`, `date`, `date_display`, `message`). En la primera consulta tras el arranque no se dispara ningún evento a propósito. Ejemplo: [`examples/automation_new_event.yaml`](examples/automation_new_event.yaml).

## Sensores

`sensor.fritzbox_ereignisse_ereignisse` (estado = número de entradas). Atributos: `events`, `groups`, `source` (`query`, `xml` o `text`), `app` (versión, estado de actualización) y `notification_center`. Los atributos grandes **no** se guardan en la base de datos (corrige la advertencia del recorder «state attributes exceed 16384 bytes»).

## Notification Center

Si el Notification Center está instalado, la integración envía avisos según el esquema 1. Se ajusta en «Configurar» y en la tarjeta (rueda dentada → Notification Center, solo administradores).

| Tipo de aviso | Urgencia | Por defecto |
|---|---|---|
| Conexión con la FRITZ!Box perdida (se cierra en cuanto la consulta vuelve a funcionar) | advertencia | activado |
| Eventos: Sistema, Conexión a Internet, Dispositivos USB (un aviso por entrada nueva) | info | activado |
| Eventos: Telefonía, Wi-Fi | info | desactivado (muchas entradas) |

La urgencia de las entradas del registro es a propósito «info», porque el texto por sí solo no revela si una entrada es un problema. Sin Notification Center no ocurre nada; los avisos se envían en cuanto se instale.

## Indicación de versión y aviso de actualización

La versión aparece en tres sitios: tarjeta → rueda dentada → «Versión de la app», arriba en el editor de la tarjeta y en el diálogo «Configurar». Al arrancar y luego cada 12 horas la integración pregunta a `api.github.com` por la última versión. Una versión más nueva se resalta en naranja. Si GitHub no está accesible, aparece «Comprobación no posible»; todo lo demás sigue funcionando.

## Ajustes

- **Profundidad del historial:** número de eventos (20–500, 100 por defecto) o número de días (1–90, 30 por defecto)
- **Notification Center:** interruptor general y una fila por tipo de aviso

## Seguridad

Las acciones de escritura de la tarjeta (interruptores del Notification Center, «Comprobar ahora») usan una acción WebSocket que el backend solo permite a administradores. Todos los textos de la tarjeta se escapan y los valores de color pasan por una lista permitida. El diagnóstico no contiene credenciales ni textos de avisos. La FRITZ!Box usa un certificado autofirmado, por lo que no se verifica en la descarga HTTPS del registro (solo red local).

## Limitaciones conocidas

- **No probado en una FRITZ!Box real.** Solo se usaron datos simulados (analizador XML, puente del Notification Center). Indica si el problema n.º 1 está resuelto en tu caja (versión de FRITZ!OS y atributo `source`).
- La interacción con un Notification Center real no se ha verificado.
- El problema n.º 2 («Custom element doesn't exist») no se pudo reproducir. La tarjeta ahora también se carga mediante un mecanismo alternativo y está protegida frente a una carga doble. Si no basta: añade a mano el recurso `/fritzbox_ereignisse_files/fritzbox-ereignisse-card.js` (tipo módulo JavaScript) y recarga con Ctrl+F5.
- Con varias FRITZ!Box, la rueda dentada actúa siempre sobre la primera entrada.
- La tarjeta no se ha probado en un navegador con datos de prueba, solo se ha comprobado su sintaxis.

## Solución de problemas

- **Tarjeta no encontrada:** véase arriba (añadir el recurso a mano, Ctrl+F5).
- **Sin entradas:** activa el registro de depuración para `custom_components.fritzbox_ereignisse` y revisa el atributo `source`.
- **Falta la función nueva tras actualizar:** reinicia Home Assistant y vacía la caché del navegador.

## Integridad de archivos

Cada archivo `.py`, `.js` y `.yaml` lleva en su primera línea un SHA-256 del archivo desde la línea 2 (`tail -n +2 archivo.py | sha256sum`). Para los archivos JSON (sin comentarios) esta tabla cubre el archivo completo:

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

## Historial de versiones

Véase [docs/VERSIONSHISTORIE.md](docs/VERSIONSHISTORIE.md) (alemán) y [RELEASE_NOTES_v1.1.0.md](RELEASE_NOTES_v1.1.0.md).

## Licencia

MIT, véase [LICENSE](LICENSE).
