# Mercado laboral en Chile y sus regiones

Panel público con las cifras de empleo del INE para el país y para cada una de las 16 regiones: desocupación, personas ocupadas, informalidad, empleo en construcción, ramas de actividad y comparación entre regiones, desde 2010. Elaborado por la Cámara Chilena de la Construcción, Sede Región de O'Higgins (Estudios).

Se actualiza solo cuando el INE publica un trimestre móvil nuevo (hacia fines de cada mes). No hay que descargar ni cargar planillas.

## Qué muestra

- **Chile y cada región**: se elige arriba a la derecha, o tocando una región en el gráfico de la portada o en el ranking. El enlace conserva la región, por ejemplo `?reg=06` abre O'Higgins y `?reg=13` la Región Metropolitana.
- Cifras principales, lectura del trimestre, desocupación total y por sexo, mismo trimestre de cada año, construcción, ramas de actividad, ranking de las 16 regiones y tabla con todos los indicadores.
- Cualquier trimestre móvil desde 2010 y períodos de 2, 5 y 10 años en los gráficos.
- **Descargas** para lo que se está viendo (Chile o la región elegida): minuta en Word, Excel de cuatro hojas y serie en CSV. Se arman en el navegador, no pasan por ningún servidor.

## Cómo funciona

1. `actualizar_empleo.py` baja la Encuesta Nacional de Empleo desde SIMEL (`sdmx.ine.gob.cl`) y escribe tres archivos en `docs/data`: `serie.json` (país y O'Higgins), `regiones_t.json` (16 regiones por trimestre) y `sectores_t.json` (ramas de actividad, país y regiones).
2. `docs/index.html` es el panel. Lee esos archivos, calcula los resúmenes y dibuja los gráficos en el navegador. GitHub Pages lo publica.
3. `.github/workflows/actualizar.yml` ejecuta el paso 1 automáticamente entre el 24 y el 31 de cada mes (y el 1 al 3 como respaldo), guarda los datos si cambiaron y vuelve a publicar la página.

## Configuración (una sola vez)

1. `Settings > Pages > Source: GitHub Actions`.
2. Pestaña `Actions > Actualizar panel de empleo > Run workflow` para la primera publicación.

## Tareas del mes

- **Margen de error de O'Higgins.** El INE lo publica en las notas estadísticas de la ENE y no viene en SIMEL, así que no se actualiza solo. Cuando esté disponible, ejecuta el flujo a mano (`Run workflow`) y escribe en el campo, por ejemplo: `2026-08=9.4,12.3` (mes en que parte el trimestre = inferior, superior; varios se separan con espacio). Los que ya están se conservan. Mientras falte, la página muestra el margen solo para los trimestres que lo tienen.
- **Próximas fechas de publicación.** Se editan a mano en `docs/data/calendario.json` con la agenda del INE (fecha, hora, publicación y trimestre). Si no queda ninguna fecha futura, el aviso de «Próximo dato» aparece vacío.

## Ajustes frecuentes

| Qué | Dónde |
|---|---|
| Horario de revisión | `cron` en `.github/workflows/actualizar.yml` (hora UTC) |
| Textos y orden de las secciones | `docs/index.html` |
| Nombres de ramas y regiones | `actualizar_empleo.py` |

## Notas

- Trimestre móvil: promedio de tres meses consecutivos. «Julio–septiembre» incluye julio, agosto y septiembre.
- El margen de error existe solo para O'Higgins y solo para los trimestres recientes; en las demás regiones no se calcula.
- La ocupación informal está disponible desde 2017 y las ramas de actividad desde 2013.
- En regiones pequeñas varias ramas salen marcadas como poco fiables según el estándar de calidad del INE (con asterisco en los gráficos).
- Fuente de los datos: Instituto Nacional de Estadísticas (INE), Encuesta Nacional de Empleo, vía SIMEL.
- Tipografía Plus Jakarta Sans (licencia OFL) y biblioteca d3 (licencia ISC), incluidas en `docs`.
