import sys
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import xbmcgui
import xbmcplugin
import xbmc

# Variables del sistema
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urllib.parse.parse_qs(sys.argv[2][1:])

JSON_URL = "https://raw.githubusercontent.com/eortas/Kodi_BC/refs/heads/main/data.json"

# Caché en sesión
_data_cache = None
_rss_cache = {}

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
    """Obtiene los últimos 15 vídeos de un canal via RSS (sin API key)."""
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
        root = ET.fromstring(xml_data)
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

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def add_youtube_item(video_id, title, thumbnail=''):
    """Añade un item de vídeo de YouTube a la lista."""
    url   = f"plugin://plugin.video.youtube/play/?video_id={video_id}"
    li    = xbmcgui.ListItem(title)
    thumb = thumbnail if thumbnail else f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
    li.setProperty('IsPlayable', 'true')
    li.setArt({'thumb': thumb})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

def router():
    data = get_remote_data()
    mode = args.get('mode',     [None])[0]
    cat  = args.get('category', [None])[0]
    mod  = args.get('module',   [None])[0]

    if not data:
        li = xbmcgui.ListItem("⚠️ Error cargando datos remotos")
        xbmcplugin.addDirectoryItem(handle=addon_handle, url="", listitem=li, isFolder=False)
        xbmcplugin.endOfDirectory(addon_handle)
        return

    # ------------------------------------------------------------------ #
    # NIVEL 1 — Categorías principales                                     #
    # ------------------------------------------------------------------ #
    if mode is None:
        for category in data.keys():
            url = build_url({'mode': 'list_modules', 'category': category})
            li  = xbmcgui.ListItem(category)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)

    # ------------------------------------------------------------------ #
    # NIVEL 2 — Módulos o canales dentro de una categoría                 #
    # ------------------------------------------------------------------ #
    elif mode == 'list_modules':
        if cat not in data:
            xbmcplugin.endOfDirectory(addon_handle)
            return

        category_data = data[cat]
        cat_type      = category_data.get('type')

        if cat_type == 'static_collection':
            for module_name in category_data['modules'].keys():
                url = build_url({'mode': 'list_videos', 'category': cat, 'module': module_name})
                li  = xbmcgui.ListItem(module_name)
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

        elif cat_type == 'channel_collection':
            for channel_name in category_data['channels'].keys():
                url = build_url({'mode': 'list_videos', 'category': cat, 'module': channel_name})
                li  = xbmcgui.ListItem(channel_name)
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(addon_handle)

    # ------------------------------------------------------------------ #
    # NIVEL 3 — Vídeos dentro de un módulo o canal                        #
    # ------------------------------------------------------------------ #
    elif mode == 'list_videos':
        if cat not in data:
            xbmcplugin.endOfDirectory(addon_handle)
            return

        category_data = data[cat]
        cat_type      = category_data.get('type')

        if cat_type == 'static_collection':
            videos = category_data['modules'].get(mod, [])
            for video in videos:
                add_youtube_item(video['video_id'], video['title'])

        elif cat_type == 'channel_collection':
            channel_info = category_data['channels'].get(mod, {})
            channel_id   = channel_info.get('channel_id', '')

            # Primero intentamos el historial acumulado (actualizado por GitHub Actions)
            videos = channel_info.get('videos', [])

            # Fallback: si el historial está vacío, tiramos del RSS en tiempo real
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