# Guía de demostración — Planificador PERT-CPM con IA

Cómo abrir la app: doble clic en `app/ejecutar.bat` y entrar a `http://127.0.0.1:8765`.
Los 8 ejemplos están dentro de la página, en el selector **«Cargar un ejemplo»** (arriba de la descripción).
Al elegir uno se llenan solos la descripción, el número de integrantes y el plazo. Luego se pulsa **Generar plan**.

> Los números de la columna «Observado» son de una corrida real con Gemini el día de la prueba.
> Gemini puede variar un poco entre ejecuciones (actividades y días); lo que no debe variar es el tipo de resultado.

## Los 8 ejemplos

| # | Ejemplo | Equipo | Qué demuestra | Observado |
|---|---|---|---|---|
| 1 | **Corto** · Portafolio de un fotógrafo | 1 | Proyecto trivial: pocos pasos, todo en secuencia | Complejidad 1, 7 actividades, 7.4 días. Equipo adecuado |
| 2 | **Pocos pasos** · Sitio web de una cafetería | 2 | Proyecto pequeño con algo de paralelismo | Complejidad 3, 8 actividades, 14.5 días |
| 3 | **Medio** · Gestión de citas de una clínica | 4 · plazo 60 | Roles, base de datos, probabilidad de cumplir el plazo | Complejidad 5-6, 10-12 actividades, 33-43 días. Incluye «Capacitación, entrega de manuales y cierre» |
| 4 | **Largo** · Plataforma de telemedicina | 6 · plazo 150 | Gran variedad de pasos, ramas en paralelo, grafo grande | Complejidad 9, 18 actividades, ~95 días. Incluye capacitación por clínica, soporte inicial y migración de datos; no ignora nada |
| 5 | **Con ruido** · App de peluquería + cosas personales | 3 | El sistema ignora lo que no es software y avisa | Planificó la app (9 actividades) e ignoró: pan, dentista, partido, boda de la prima |
| 6 | **Sin software** · Organizar una boda | 3 | Rechazo de lo que no es un proyecto de software | Rechazado: «No se detectó un proyecto de software» |
| 7 | **Muy vaga** · «Aplicación de ventas en línea» | 3 | Rechazo por descripción insuficiente, con pistas de qué añadir | Rechazado con 4 indicaciones (plataforma, usuarios, funciones, integraciones) |
| 8 | **Demasiado corta** · «quiero una app» | 3 | Rechazo inmediato, sin usar la IA | Rechazado al instante con 4 indicaciones generales |

## Guion sugerido (≈ 10 minutos)

1. **Ejemplo 8, 7 y 6** (1 minuto): muestran el filtro de entrada. No se genera nada y la app dice qué falta. Los ejemplos 6 y 7 usan la IA una vez; el 8 no usa nada.
2. **Ejemplo 5** (1 minuto): la app ignora lo que no es software y lo muestra en la página 2, «Análisis de la IA».
3. **Ejemplo 1** (2 minutos): el caso simple. Después, subir **Integrantes a 6** y mostrar que la página 2 pasa a «Sobran integrantes».
4. **Ejemplo 4** (4 minutos), el principal:
   - **Página 1 · Plan:** Gantt, tabla y ruta crítica. Editar una duración en la tabla y ver cómo se recalcula todo.
   - **Página 2 · Equipo y tiempos:** probabilidad, carga de cada integrante y evaluación del equipo.
   - **Página 3 · Grafo:** hacer clic en un nodo como predecesor y en otro como posterior, escribir un paso nuevo (por ejemplo «Auditoría externa de seguridad») y pulsar **Añadir y recalcular**.
5. **Cierre** (1 minuto): qué hace la IA y qué hace el código (ver abajo).

## Qué hace la IA y qué hace el código

| La IA (Gemini) | El código (determinista) |
|---|---|
| Filtra: ¿es software?, ¿cuánto detalle hay? | Valida y compara con los 16 proyectos de referencia (TF-IDF) |
| Propone actividades, precedencias, tiempos (a, m, b) y personas | Verifica reglas de sentido común y pide corregir |
| Estima la complejidad y opina sobre el equipo | Calcula te, varianza, ES, EF, LS, LF, holguras, ruta crítica, σ y probabilidad |
| | Reparte tareas por nombre, dibuja el Gantt y el grafo |

## Si algo falla durante la presentación

- **«Ningún modelo de Gemini está disponible»:** la capa gratuita tiene límites diarios y a veces saturación. La app prueba varios modelos en cadena (configurados en `app/.env`, línea `GEMINI_MODEL`). Espera un minuto y reintenta.
- **La ventana negra se cerró:** abrir `app/ejecutar.bat` otra vez.
- **Plan de respaldo:** genera los ejemplos 1, 3 y 4 **antes** de la presentación y deja la pestaña abierta; también puedes descargar el CSV de cada uno desde la página 1.
- Recomendación: no repetir el mismo ejemplo muchas veces. Cada plan usa entre 2 y 4 llamadas a Gemini.

## Limitaciones (para el análisis crítico)

- Los 16 proyectos de la base de conocimiento son referencias que armamos como ejemplos plausibles; no son datos medidos de proyectos reales.
- Los tiempos son estimaciones de la IA y no se validan contra proyectos terminados. Por eso se usa PERT con tres tiempos, que modela la incertidumbre.
- Un mismo ejemplo puede dar planes algo distintos entre ejecuciones.
- La capa gratuita de Gemini limita el uso diario por modelo.
