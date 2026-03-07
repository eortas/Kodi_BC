"""
update_rss.py
-------------
Descarga los últimos vídeos de cada canal RSS definido en data.json,
los combina con el historial acumulado (sin duplicados) y guarda el resultado.

Se ejecuta automáticamente via GitHub Actions cada 24 horas.
"""

import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DATA_FILE = Path("data.json")
MAX_VIDEOS_PER_CHANNEL = 500


def fetch_rss(channel_id: str) -> list[dict]:
    """Obtiene los últimos 15 vídeos de un canal via RSS feed."""
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read().decode("utf-8")
    except Exception as e:
        print(f"  ⚠️  Error fetching RSS for {channel_id}: {e}")
        return []

    ns = {
        "atom":  "http://www.w3.org/2005/Atom",
        "yt":    "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    root = ET.fromstring(xml_data)
    videos = []
    for entry in root.findall("atom:entry", ns):
        video_id  = entry.find("yt:videoId", ns).text
        title     = entry.find("atom:title", ns).text
        thumbnail = entry.find("media:group/media:thumbnail", ns)
        thumb_url = thumbnail.attrib.get("url", "") if thumbnail is not None else ""
        videos.append({"video_id": video_id, "title": title, "thumbnail": thumb_url})

    return videos


def merge_videos(new: list[dict], existing: list[dict]) -> list[dict]:
    """
    Combina nuevos vídeos con el historial existente
    - Los vídeos nuevos van AL PRINCIPIO de la lista
    - Los duplicados (mismo video_id) se descartan.
    - El orden del historial existente se preserva.
    """
    existing_ids = {v["video_id"] for v in existing}
    truly_new    = [v for v in new if v["video_id"] not in existing_ids]

    if truly_new:
        print(f"    ✅ {len(truly_new)} vídeo(s) nuevo(s) encontrado(s)")
    else:
        print(f"    ℹ️  Sin vídeos nuevos")

    merged = truly_new + existing
    return merged[:MAX_VIDEOS_PER_CHANNEL]


def main():
    print(f"📂 Cargando {DATA_FILE}...")
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    updated = False

    for category_name, category_data in data.items():
        if not isinstance(category_data, dict):
            continue
        if category_data.get("type") != "channel_collection":
            continue

        print(f"\n📁 Categoría: {category_name}")

        for channel_name, channel_info in category_data["channels"].items():
            channel_id = channel_info.get("channel_id", "")
            print(f"  📺 Canal: {channel_name} ({channel_id})")

            # Vídeos ya guardados en el historial
            existing = channel_info.get("videos", [])

            # Últimos 15 del RSS
            new_videos = fetch_rss(channel_id)
            if not new_videos:
                continue

            # Merge: nuevos primero sin duplicados
            merged = merge_videos(new_videos, existing)

            if len(merged) != len(existing):
                channel_info["videos"] = merged
                updated = True

    if updated:
        DATA_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )
        print(f"\n💾 {DATA_FILE} actualizado correctamente.")
    else:
        print(f"\n✅ Sin cambios. {DATA_FILE} no modificado.")


if __name__ == "__main__":
    main()

