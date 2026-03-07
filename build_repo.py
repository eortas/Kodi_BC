"""
build_repo.py
-------------
Genera los artefactos necesarios para un repositorio de Kodi:
  - plugin.video.bootcamp_data_science-X.Y.Z.zip  (en la raíz)
  - repository.bootcamp_ds-1.0.0.zip              (en la raíz)
  - addons.xml
  - addons.xml.md5
  - index.html

Se ejecuta automáticamente via GitHub Actions al hacer push de cambios
en plugin.video.bootcamp_data_science/.
"""

import hashlib
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# ── Rutas ──────────────────────────────────────────────────────────────────
ADDON_DIR   = Path("plugin.video.bootcamp_data_science")
REPO_DIR    = Path("repository.bootcamp_ds")
ADDONS_XML  = Path("addons.xml")
ADDONS_MD5  = Path("addons.xml.md5")
INDEX_HTML  = Path("index.html")

EXCLUDE = {".git", ".github", "__pycache__", "*.pyc", ".DS_Store"}


def get_version(addon_xml_path: Path) -> str:
    root = ET.parse(addon_xml_path).getroot()
    return root.get("version")


def zip_addon(source_dir: Path) -> Path:
    """Empaqueta un directorio de addon en un zip en la RAÍZ del repo."""
    addon_id = source_dir.name
    version  = get_version(source_dir / "addon.xml")
    zip_name = Path(f"{addon_id}-{version}.zip")  # ← raíz, no subcarpeta

    # Eliminar zips anteriores de este addon en la raíz
    for old in Path(".").glob(f"{addon_id}-*.zip"):
        old.unlink()

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in source_dir.rglob("*"):
            if file.suffix == ".zip":
                continue
            if any(file.match(pat) for pat in EXCLUDE):
                continue
            arcname = file.relative_to(source_dir.parent)
            zf.write(file, arcname)

    print(f"  ✅ Creado: {zip_name}")
    return zip_name


def build_addons_xml(*addon_dirs: Path) -> str:
    root = ET.Element("addons")
    for addon_dir in addon_dirs:
        addon_xml = addon_dir / "addon.xml"
        if not addon_xml.exists():
            print(f"  ⚠️  No encontrado: {addon_xml}")
            continue
        addon_root = ET.parse(addon_xml).getroot()
        root.append(addon_root)
        print(f"  📦 Añadido al índice: {addon_dir.name} v{addon_root.get('version')}")
    ET.indent(root, space="    ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def write_md5(content: str, path: Path) -> None:
    md5 = hashlib.md5(content.encode("utf-8")).hexdigest()
    path.write_text(md5)
    print(f"  🔑 MD5: {md5}")


def build_index_html(*addon_dirs: Path) -> str:
    """Genera index.html con los zips en la raíz para que Kodi los encuentre."""
    links = []
    for addon_dir in addon_dirs:
        addon_id = addon_dir.name
        version  = get_version(addon_dir / "addon.xml")
        zip_name = f"{addon_id}-{version}.zip"
        links.append(f'    <a href="{zip_name}">{zip_name}</a>')

    links.append('    <a href="addons.xml">addons.xml</a>')
    links.append('    <a href="addons.xml.md5">addons.xml.md5</a>')

    return "<html>\n<body>\n" + "\n".join(links) + "\n</body>\n</html>\n"


def main():
    print("🏗️  Construyendo repositorio Kodi...\n")

    print("📦 Empaquetando addon principal:")
    zip_addon(ADDON_DIR)

    print("\n📦 Empaquetando addon repositorio:")
    zip_addon(REPO_DIR)

    print("\n📄 Generando addons.xml:")
    addons_xml_content = build_addons_xml(ADDON_DIR, REPO_DIR)
    ADDONS_XML.write_text(addons_xml_content, encoding="utf-8")

    print("\n🔑 Generando addons.xml.md5:")
    write_md5(addons_xml_content, ADDONS_MD5)

    print("\n🌐 Generando index.html:")
    INDEX_HTML.write_text(build_index_html(ADDON_DIR, REPO_DIR), encoding="utf-8")
    print("  ✅ index.html generado")

    print("\n✅ Repositorio generado correctamente.")


if __name__ == "__main__":
    main()