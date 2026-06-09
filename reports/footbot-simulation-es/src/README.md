# Logo de la universidad

Coloca aquí el logo de la universidad (UNET) para la portada del reporte.

- **Nombre de archivo esperado:** `logo-unet.png` (también sirve `.pdf` vectorial,
  ajustando la extensión en `main.tex`).
- El reporte lo incluye **automáticamente** en la portada si el archivo existe
  (ver el bloque `\IfFileExists{src/logo-unet.png}{...}{...}` en `main.tex`).
- Si el archivo no está, la portada muestra un recuadro de marcador de posición,
  de modo que el documento **compila igual** con o sin logo.

Formato recomendado: PNG con fondo transparente o PDF vectorial, ~300–600 px de ancho.
