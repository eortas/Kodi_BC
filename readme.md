# Addon Kodi: Bootcamp Data Science

Un addon de vídeo personalizado para Kodi diseñado para acceder de forma estructurada, rápida y directa a las grabaciones de las clases del Bootcamp de Data Science & Machine Learning (The Bridge, Vitoria-Gasteiz - Abril 2025).

## Características Principales

* **Estructura Dinámica:** El menú del addon se construye en tiempo real consumiendo un archivo `data.json` remoto. Esto permite actualizar el contenido y añadir nuevos contenidos sin que los usuarios tengan que reinstalar o actualizar el addon en sus dispositivos.
* **Reproducción Directa:** Configurado para extraer los IDs únicos de cada vídeo y enviarlos directamente al reproductor interno de Kodi. Esto evita el error de cuota de la API de Google Cloud y no requiere que el usuario configure credenciales propias.
* **Interfaz Personalizada:** Incluye *screenshots* personalizados integrados.

## Tecnologías y Lenguajes

* **Python 3:** Lógica principal de enrutamiento y consumo HTTP (`urllib.request`).
* **JSON:** Estructuración de datos (módulos, títulos y URL videos).


## Instalación Directa en Kodi

El addon está alojado mediante GitHub Pages para permitir su descarga directa desde el gestor de archivos de Kodi.

1. Abre Kodi y ve a **Ajustes** (el icono del engranaje) > **Gestor de archivos**.
2. Haz clic en **Añadir fuente**.
3. En la ruta (donde pone `<Ninguno>`), introduce exactamente esta URL:
   `https://eortas.github.io/Kodi_BC/`
4. Ponle un nombre a la fuente (por ejemplo, "Repo Bootcamp" o déjalo por defecto) y dale a **OK**.
5. Vuelve al menú principal de Kodi y entra en **Add-ons**.
6. Haz clic en el icono de la caja abierta (arriba a la izquierda) > **Instalar desde un archivo .zip**.
7. Selecciona la fuente que creaste ("Repo Bootcamp").
8. Haz clic en `plugin.video.bootcamp_data_science.zip` para instalarlo.

*Nota: Para volver atrás en Kodi mantén pulsada la tecla de borrar **Backspace**, para seleccionar algo puedes hacerlo con **Intro** o con el ratón. Mantener pulsado **Intro** te mostrará sus ajustes (por si quieres desinstarlo)*



---
*Desarrollado para optimizar el acceso al material de estudio del stack tecnológico (Python, Pandas, Machine Learning, AWS, Docker, etc).*