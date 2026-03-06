import sys
import json
import urllib.request
import xbmcgui
import xbmcplugin
import xbmc

addon_handle = int(sys.argv[1])

# Sustituye esto por la URL directa a tu archivo JSON (ej. GitHub Raw)
JSON_URL = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/data.json"

def get_remote_data():
    try:
        # Petición HTTP para obtener el JSON
        req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        # Registra el error en el log de Kodi (útil para depurar)
        xbmc.log(f"Error cargando JSON remoto: {e}", xbmc.LOGERROR)
        return {}

def build_menu():
    bootcamp_playlists = get_remote_data()
    
    if not bootcamp_playlists:
        # Elemento de error visual si falla la descarga
        li = xbmcgui.ListItem("Error de conexión o JSON no disponible")
        xbmcplugin.addDirectoryItem(handle=addon_handle, url="", listitem=li, isFolder=False)
    else:
        # Generación dinámica del menú desde el JSON
        for modulo, playlist_id in bootcamp_playlists.items():
            youtube_url = f"plugin://plugin.video.youtube/playlist/{playlist_id}/"
            li = xbmcgui.ListItem(modulo)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=youtube_url, listitem=li, isFolder=True)
    
    xbmcplugin.endOfDirectory(addon_handle)

if __name__ == '__main__':
    build_menu()