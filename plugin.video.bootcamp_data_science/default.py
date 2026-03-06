import sys
import json
import urllib.request
import urllib.parse
import xbmcgui
import xbmcplugin
import xbmc

# Variables del sistema
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urllib.parse.parse_qs(sys.argv[2][1:])

JSON_URL = "URL_RAW_DE_TU_DATA_JSON"

def get_remote_data():
    try:
        req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        xbmc.log(f"Error cargando JSON remoto: {e}", xbmc.LOGERROR)
        return {}

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def router():
    bootcamp_data = get_remote_data()
    mode = args.get('mode', [None])[0]

    if not bootcamp_data:
        li = xbmcgui.ListItem("Error cargando datos remotos")
        xbmcplugin.addDirectoryItem(handle=addon_handle, url="", listitem=li, isFolder=False)
        xbmcplugin.endOfDirectory(addon_handle)
        return

    if mode is None:
        # NIVEL 1: Mostrar los módulos
        for module in bootcamp_data.keys():
            url = build_url({'mode': 'list_videos', 'module': module})
            li = xbmcgui.ListItem(module)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)

    elif mode == 'list_videos':
        # NIVEL 2: Mostrar los vídeos del módulo seleccionado
        module = args.get('module', [None])[0]
        
        if module in bootcamp_data:
            for video in bootcamp_data[module]:
                # Endpoint de reproducción directa (suele evadir la API)
                youtube_url = f"plugin://plugin.video.youtube/play/?video_id={video['video_id']}"
                
                li = xbmcgui.ListItem(video['title'])
                li.setProperty('IsPlayable', 'true')
                
                # isFolder=False dispara el reproductor en lugar de abrir un submenú
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=youtube_url, listitem=li, isFolder=False)
                
        xbmcplugin.endOfDirectory(addon_handle)

if __name__ == '__main__':
    router()