# Checklist de la rúbrica — qué está hecho y qué falta

Basado en la guía oficial del proyecto (`Proyecto_Final.pdf`). Calificación: **100 puntos** = Rúbrica A (40) + B (30) + C (30).

Leyenda: ✅ hecho · 🟡 parcial · ❌ falta

**Resumen:** la **herramienta** está terminada. Lo que falta es casi todo **documentación**: solución manual, casos de prueba
documentados, contrastación, el informe de 12 secciones y las diapositivas.

---

## Rúbrica A — Proyecto práctico experimental (40 pts)

| # | Criterio (paso de la guía) | Estado | Qué hay | Qué falta |
|---|---|---|---|---|
| 1 | **Planteamiento del problema y modelo** (pasos 1 y 2) | 🟡 | El sistema implementa el modelo PERT-CPM | **Redactarlo**: contexto real, datos, variables de decisión (duración de cada actividad, personas), supuestos y restricciones (precedencias, equipo disponible) y el modelo (red de actividades y fórmulas) |
| 2 | **Solución manual o analítica** (paso 3) | ❌ | Nada | Resolver **a mano, paso a paso**, una red pequeña (7 a 10 actividades): `te` y `σ²`, pasada hacia adelante (ES, EF), hacia atrás (LS, LF), holguras, ruta crítica, σ del proyecto y probabilidad con tabla normal. Mostrar todo el procedimiento |
| 3 | **Implementación con herramienta** (paso 4) | ✅ | App en Python/Flask (`app/`) | Capturas de pantalla para los anexos. Opcional: una **segunda herramienta independiente** (Excel o `networkx`) para reforzar la contrastación |
| 4 | **Diseño experimental y casos de prueba** (paso 5) | 🟡 | 35 pruebas automáticas y 8 ejemplos de demostración | **Documento con mínimo 3 casos**: datos de entrada y resultados esperados de cada uno, **incluido un caso límite** |
| 5 | **Contrastación y validación** (paso 6) | ❌ | Nada | Tabla **manual vs. herramienta** por cada caso y explicación de cualquier diferencia (p. ej. redondeo a 6 decimales) |
| 6 | **Análisis crítico** (paso 7) | 🟡 | Limitaciones listadas en `docs/EJEMPLOS_DEMO.md` | **Redactarlo con comprensión propia**: validez, limitaciones, implicaciones prácticas y mejoras |

### Casos de prueba sugeridos (mínimo 3, uno límite)

| Caso | Idea | Por qué sirve |
|---|---|---|
| 1 · Secuencial | Red lineal A→B→C→D (todas críticas) | Es el más fácil de resolver a mano |
| 2 · Con ramas y holguras | Dos ramas en paralelo, una con holgura | Comprueba ES/EF/LS/LF y holguras |
| 3 · **Límite** | Dos rutas críticas simultáneas (holgura cero en todas) **o** una actividad de duración 0 **o** equipo al límite de su capacidad | Es el caso límite que exige la guía |

Ya existen pruebas automáticas equivalentes en `app/test_cpm.py` y `app/test_edit.py` que puedes tomar como punto de partida.

### Para el análisis crítico (ideas que ya tiene el proyecto)

- Los tiempos son **estimaciones de la IA**, no medidas; se modelan con tres tiempos (PERT) para reflejar la incertidumbre.
- La base de conocimiento tiene **16 proyectos de referencia armados por el equipo**, no datos reales.
- Un mismo texto puede dar planes distintos entre ejecuciones; las reglas de sentido común reducen, pero no eliminan, ese problema.
- PERT supone actividades independientes y distribución normal de la duración total (teorema central del límite).
- La asignación de personas es una heurística (no minimiza costo ni nivela recursos de forma óptima).
- Mejoras posibles: aprender de las correcciones del ingeniero, calibrar con proyectos reales, costos, nivelación de recursos.

---

## Rúbrica B — Informe final (30 pts)

### Formato (todo ❌, aún no hay informe)

- 8 a 15 páginas · Times New Roman o Arial **12 pt** · interlineado **1.5**
- Márgenes: **3 cm izquierdo**, 2.5 cm superior, inferior y derecho
- **Ecuaciones con el editor de ecuaciones de Word**, numeradas consecutivamente
- Figuras y tablas **numeradas con título** y, si aplica, fuente
- Citas y referencias en **APA 7.ª edición**
- Redacción en **tercera persona o voz pasiva**, lenguaje técnico

### Las 12 secciones obligatorias, en orden

| # | Sección | Contenido esperado | Material disponible en este proyecto |
|---|---|---|---|
| 1 | Portada | Universidad, facultad, carrera, asignatura, título, integrantes, docente y fecha | Datos del equipo (completar) |
| 2 | Resumen | Máximo **200 palabras**: problema, modelo, resultados y conclusión | — |
| 3 | Introducción | Contexto, relevancia y organización del documento | Descripción del README |
| 4 | Objetivos | General y específicos, coherentes con el problema | — |
| 5 | Marco teórico | Fundamentos de PERT-CPM con citas | Fórmulas (abajo) y bibliografía del sílabo |
| 6 | Metodología | Problema, datos, modelo formulado y herramienta | Flujo de 6 pasos del README |
| 7 | Desarrollo | **Solución manual completa**, paso a paso | ❌ por hacer |
| 8 | Resultados y discusión | Herramienta, contraste con lo manual y casos de prueba (con el límite) | Pantallas de la app |
| 9 | Conclusiones | Hallazgos frente a los objetivos | — |
| 10 | Recomendaciones | Mejoras o extensiones | Ver «Mejoras posibles» |
| 11 | Referencias | APA 7, incluida la bibliografía del sílabo | Abajo |
| 12 | Anexos | Código fuente, capturas, datos y **declaración del uso de IA** | Repositorio y capturas |

### Ecuaciones que probablemente necesites (para el editor de Word)

1. `te = (a + 4m + b) / 6`
2. `σ² = ((b − a) / 6)²`
3. `ES_j = máx(EF_i)` para todas las predecesoras `i` de `j`
4. `EF_j = ES_j + te_j`
5. `LF_i = mín(LS_j)` para todas las sucesoras `j` de `i`
6. `LS_i = LF_i − te_i`
7. `H_i = LS_i − ES_i` (actividad crítica si `H_i = 0`)
8. `σ_T² = Σ σ_i²` sobre las actividades de la ruta crítica
9. `Z = (D − T_E) / σ_T` y `P(T ≤ D) = Φ(Z)`

### Referencias base (bibliografía del sílabo, a citar en APA 7)

- Taha, H. A. (2017). *Investigación de operaciones* (10.ª ed.). Pearson Educación.
- Project Management Institute. (2017). *A guide to the project management body of knowledge (PMBOK guide)* (6.ª ed.). Project Management Institute.
- Palacios Figueroa, R. (2017). *Investigación de operaciones I* (1.ª ed.) [versión digital]. Alfaomega.
- Martín, Q. (2006). *Investigación operativa* (1.ª ed.). Pearson.

### Declaración de uso de IA (obligatoria, al final de Anexos)

Un párrafo que indique **la herramienta, el propósito específico y la parte del trabajo**. En este proyecto aplica a:

- **Gemini**: componente del sistema (propone actividades y estimaciones de tiempo).
- **Claude (asistente de IA)**: apoyo para escribir y revisar el código y para armar la documentación.

La guía exige además que **el modelo matemático, la solución manual y el análisis crítico reflejen la comprensión propia del equipo**:
esas tres partes conviene que las redacten y entiendan los integrantes, y usar la IA solo para revisar.

---

## Rúbrica C — Presentación formal (30 pts)

| Aspecto | Estado | Pendiente |
|---|---|---|
| 15 min de exposición + 5 de preguntas | 🟡 | Ensayar con cronómetro |
| **Todos** los integrantes exponen una parte sustancial | ❌ | Repartir secciones |
| Diapositivas claras y sin texto excesivo | ❌ | **No existen aún** |
| Demostración en vivo o video de respaldo con al menos un caso de prueba | ✅ | Guion en `docs/EJEMPLOS_DEMO.md`; grabar un **video de respaldo** por si falla internet o la cuota de Gemini |
| Puntualidad, vestimenta formal, dominio del tema | — | Responsabilidad del equipo |

---

## Orden de trabajo recomendado

1. Definir el **caso de estudio** y la red que se resolverá a mano (la del ejemplo «Corto» sirve).
2. **Solución manual** de ese caso (paso 3).
3. **3 casos de prueba** con resultados esperados, incluido el límite (paso 5).
4. **Contrastación** manual vs. herramienta (paso 6).
5. **Análisis crítico** (paso 7).
6. Redactar el **informe** en Word con el formato exigido y las 12 secciones.
7. **Capturas** de pantalla y declaración de IA para Anexos.
8. **Diapositivas** y ensayo; grabar el video de respaldo.
