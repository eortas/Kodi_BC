import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import xbmcgui
import xbmcplugin
import xbmc
import xbmcaddon
import xbmcvfs
import os

# Variables del sistema
base_url     = sys.argv[0]
addon_handle = int(sys.argv[1])
args         = urllib.parse.parse_qs(sys.argv[2][1:])

JSON_URL = "https://raw.githubusercontent.com/eortas/Kodi_BC/refs/heads/main/data.json"
# dpaste.com no requiere API key

# Caché en sesión
_data_cache = None
_rss_cache  = {}


# ═══════════════════════════════════════════════════════════════════════════ #
# DATOS REMOTOS                                                               #
# ═══════════════════════════════════════════════════════════════════════════ #

def get_remote_data():
    global _data_cache
    if _data_cache:
        return _data_cache
    try:
        req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            _data_cache = json.loads(response.read().decode('utf-8'))
            return _data_cache
    except Exception as e:
        xbmc.log(f"Error cargando JSON remoto: {e}", xbmc.LOGERROR)
        return {}


def get_channel_videos_rss(channel_id):
    if channel_id in _rss_cache:
        return _rss_cache[channel_id]
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read().decode('utf-8')

        ns = {
            'atom':  'http://www.w3.org/2005/Atom',
            'yt':    'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/'
        }
        root   = ET.fromstring(xml_data)
        videos = []
        for entry in root.findall('atom:entry', ns):
            video_id  = entry.find('yt:videoId', ns).text
            title     = entry.find('atom:title', ns).text
            thumbnail = entry.find('media:group/media:thumbnail', ns)
            thumb_url = thumbnail.attrib.get('url', '') if thumbnail is not None else ''
            videos.append({'video_id': video_id, 'title': title, 'thumbnail': thumb_url})

        _rss_cache[channel_id] = videos
        return videos
    except Exception as e:
        xbmc.log(f"Error cargando RSS del canal {channel_id}: {e}", xbmc.LOGERROR)
        return []


# ═══════════════════════════════════════════════════════════════════════════ #
# EXPORTAR FAVORITOS CON QR                                                   #
# ═══════════════════════════════════════════════════════════════════════════ #

def read_favourites():
    """Lee los favoritos de Kodi desde favourites.xml."""
    fav_path = xbmcvfs.translatePath('special://userdata/favourites.xml')
    favourites = []

    if not xbmcvfs.exists(fav_path):
        return favourites

    try:
        with xbmcvfs.File(fav_path) as f:
            xml_data = f.read()
        root = ET.fromstring(xml_data)
        for fav in root.findall('favourite'):
            name  = fav.attrib.get('name', 'Sin nombre')
            thumb = fav.attrib.get('thumb', '')
            path  = fav.text or ''
            favourites.append({'name': name, 'thumb': thumb, 'path': path})
    except Exception as e:
        xbmc.log(f"Error leyendo favourites.xml: {e}", xbmc.LOGERROR)

    return favourites


def upload_to_paste(data):
    """Sube los datos a dpaste.com (sin API key) y devuelve la URL pública."""
    try:
        content = json.dumps(data, ensure_ascii=False, indent=2)
        form_data = urllib.parse.urlencode({
            'content':   content,
            'syntax':    'json',
            'expiry_days': 7,
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://dpaste.com/api/v2/',
            data=form_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent':   'Mozilla/5.0'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            url = response.read().decode('utf-8').strip().rstrip('/')
            return url + '.txt'
    except Exception as e:
        xbmc.log(f"Error subiendo a dpaste.com: {e}", xbmc.LOGERROR)
        return None


def download_qr_image(url):
    """Descarga la imagen QR y la guarda en la caché de Kodi."""
    try:
        qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={urllib.parse.quote(url)}"
        req    = urllib.request.Request(qr_api, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            img_data = response.read()

        # Guardar en caché temporal de Kodi
        cache_dir = xbmcvfs.translatePath('special://temp/')
        qr_path   = os.path.join(cache_dir, 'kodi_favourites_qr.png')
        with xbmcvfs.File(qr_path, 'w') as f:
            f.write(bytearray(img_data))

        return qr_path
    except Exception as e:
        xbmc.log(f"Error descargando QR: {e}", xbmc.LOGERROR)
        return None


def export_favourites():
    """Flujo completo: leer favoritos → subir → mostrar QR."""
    dialog = xbmcgui.Dialog()

    # 1. Leer favoritos
    favourites = read_favourites()
    if not favourites:
        dialog.notification(
            'Exportar favoritos',
            'No se encontraron favoritos en Kodi.',
            xbmcgui.NOTIFICATION_WARNING
        )
        return

    # 2. Confirmar
    ok = dialog.yesno(
        'Exportar favoritos',
        f'Se encontraron {len(favourites)} favoritos.\n¿Subir y generar código QR?\n\n(Escanea el QR con tu móvil para acceder a ellos desde cualquier navegador)'
    )
    if not ok:
        return

    # 3. Subir a dpaste.com
    xbmc.log("Subiendo favoritos...", xbmc.LOGINFO)
    export_data = {
        'exported_from': 'Kodi Bootcamp DS Addon',
        'total':         len(favourites),
        'favourites':    favourites
    }
    url = upload_to_paste(export_data)
    if not url:
        dialog.notification(
            'Exportar favoritos',
            'Error al subir los datos. Comprueba tu conexión.',
            xbmcgui.NOTIFICATION_ERROR
        )
        return

    # 4. Generar y descargar QR
    qr_path = download_qr_image(url)
    if not qr_path:
        # Si falla el QR, mostrar la URL en texto
        dialog.ok('Favoritos exportados', f'URL de tus favoritos:\n{url}')
        return

    # 5. Mostrar QR en pantalla
    show_qr_dialog(url, qr_path)


def show_qr_dialog(url, qr_path):
    """Muestra el QR en un diálogo personalizado con la URL debajo."""
    class QRDialog(xbmcgui.WindowDialog):
        def __init__(self, url, qr_path):
            super().__init__()
            sw = self.getWidth()
            sh = self.getHeight()

            # Fondo semitransparente
            bg = xbmcgui.ControlImage(0, 0, sw, sh, '')
            self.addControl(bg)

            # Título
            title = xbmcgui.ControlLabel(
                sw // 2 - 400, sh // 2 - 280, 800, 60,
                'Escanea para ver tus favoritos',
                font='font20', alignment=6
            )
            self.addControl(title)

            # Imagen QR
            qr_size = 400
            qr = xbmcgui.ControlImage(
                sw // 2 - qr_size // 2,
                sh // 2 - qr_size // 2 - 20,
                qr_size, qr_size, qr_path
            )
            self.addControl(qr)

            # URL en texto
            url_label = xbmcgui.ControlLabel(
                sw // 2 - 500, sh // 2 + qr_size // 2,
                1000, 50, url,
                font='font14', alignment=6
            )
            self.addControl(url_label)

            # Instrucción para cerrar
            close_label = xbmcgui.ControlLabel(
                sw // 2 - 300, sh // 2 + qr_size // 2 + 60,
                600, 40,
                'Pulsa ATRÁS para cerrar',
                font='font14', alignment=6
            )
            self.addControl(close_label)

        def onAction(self, action):
            if action.getId() in (92, 10):  # BACK o B
                self.close()

    win = QRDialog(url, qr_path)
    win.doModal()
    del win


# ═══════════════════════════════════════════════════════════════════════════ #
# HELPERS                                                                     #
# ═══════════════════════════════════════════════════════════════════════════ #

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)


def add_youtube_item(video_id, title, thumbnail=''):
    url   = f"plugin://plugin.video.youtube/play/?video_id={video_id}"
    li    = xbmcgui.ListItem(title)
    thumb = thumbnail if thumbnail else f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
    li.setProperty('IsPlayable', 'true')
    li.setArt({'thumb': thumb})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)


# ═══════════════════════════════════════════════════════════════════════════ #
# ROUTER                                                                      #
# ═══════════════════════════════════════════════════════════════════════════ #

def router():
    data = get_remote_data()
    mode = args.get('mode',     [None])[0]
    cat  = args.get('category', [None])[0]
    mod  = args.get('module',   [None])[0]

    # ── Acción especial: exportar favoritos ─────────────────────────────── #
    if mode == 'export_favourites':
        export_favourites()
        return

    if not data:
        li = xbmcgui.ListItem("Error cargando datos remotos")
        xbmcplugin.addDirectoryItem(handle=addon_handle, url="", listitem=li, isFolder=False)
        xbmcplugin.endOfDirectory(addon_handle)
        return

    # ── NIVEL 1 — Categorías + botón exportar ───────────────────────────── #
    if mode is None:
        for category in data.keys():
            url = build_url({'mode': 'list_modules', 'category': category})
            li  = xbmcgui.ListItem(category)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

        # Botón exportar favoritos al final del menú principal
        url_export = build_url({'mode': 'export_favourites'})
        li_export  = xbmcgui.ListItem('Exportar favoritos (QR)')
        li_export.setArt({'thumb': 'DefaultAddonRepository.png'})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url_export, listitem=li_export, isFolder=False)

        xbmcplugin.endOfDirectory(addon_handle)

    # ── NIVEL 2 — Módulos o canales ─────────────────────────────────────── #
    elif mode == 'list_modules':
        if cat not in data:
            xbmcplugin.endOfDirectory(addon_handle)
            return

        category_data = data[cat]
        cat_type      = category_data.get('type')

        if cat_type == 'static_collection':
            for module_name, module_data in category_data['modules'].items():
                url = build_url({'mode': 'list_videos', 'category': cat, 'module': module_name})
                li  = xbmcgui.ListItem(module_name)
                if isinstance(module_data, dict) and module_data.get('thumbnail'):
                    li.setArt({'thumb': module_data['thumbnail']})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

        elif cat_type == 'channel_collection':
            for channel_name in category_data['channels'].keys():
                url = build_url({'mode': 'list_videos', 'category': cat, 'module': channel_name})
                li  = xbmcgui.ListItem(channel_name)
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(addon_handle)

    # ── NIVEL 3 — Vídeos ────────────────────────────────────────────────── #
    elif mode == 'list_videos':
        if cat not in data:
            xbmcplugin.endOfDirectory(addon_handle)
            return

        category_data = data[cat]
        cat_type      = category_data.get('type')

        if cat_type == 'static_collection':
            module_data = category_data['modules'].get(mod, {})
            videos = module_data.get('videos', []) if isinstance(module_data, dict) else module_data
            thumb  = module_data.get('thumbnail', '') if isinstance(module_data, dict) else ''
            for video in videos:
                add_youtube_item(video['video_id'], video['title'], thumb)

        elif cat_type == 'channel_collection':
            channel_info = category_data['channels'].get(mod, {})
            channel_id   = channel_info.get('channel_id', '')
            videos       = channel_info.get('videos', [])

            if not videos:
                xbmc.log(f"Historial vacío para {mod}, usando RSS en tiempo real", xbmc.LOGINFO)
                videos = get_channel_videos_rss(channel_id)

            if not videos:
                xbmcgui.Dialog().notification(
                    mod, 'No se pudieron cargar los vídeos.', xbmcgui.NOTIFICATION_WARNING
                )
            for video in videos:
                add_youtube_item(video['video_id'], video['title'], video.get('thumbnail', ''))

        xbmcplugin.endOfDirectory(addon_handle)


if __name__ == '__main__':
    router()