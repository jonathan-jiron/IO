# Caso de estudio: planificación de la construcción de este proyecto

Este es el caso que se resuelve **a mano** en el informe (paso 3 de la guía) y que luego se contrasta con la herramienta (paso 6).
Es la planificación PERT-CPM de **construir este mismo sistema**: el equipo conoce las actividades, así que puede justificar sus estimaciones.

> Las respuestas calculadas están en `docs/CASO_DE_ESTUDIO_CLAVE.md`. **Resuélvanlo primero a mano** y luego comparen.

## 1. Datos del problema

- **Proyecto:** desarrollo y entrega del Planificador PERT-CPM asistido por IA.
- **Equipo:** 4 integrantes. **Unidad de tiempo:** días laborables.
- **Plazo objetivo:** `D = 42` días (para calcular la probabilidad de cumplirlo).
- **Variables:** duración de cada actividad (tres estimaciones PERT) y personas necesarias.
- **Restricciones:** las precedencias de la tabla y un equipo de 4 personas.

### Supuestos

- Las duraciones siguen una distribución beta; se resumen con `te = (a + 4m + b) / 6` y `σ² = ((b − a) / 6)²`.
- Las actividades son independientes entre sí.
- La duración total es aproximadamente normal (teorema central del límite).
- Una actividad no empieza hasta que terminan **todas** sus predecesoras.

## 2. Red de actividades

`a` = optimista, `m` = más probable, `b` = pesimista (en días).

| ID | Actividad | Predecesoras | a | m | b | Personas |
|---|---|---|---|---|---|---|
| A | Levantamiento de requisitos y alcance | — | 2 | 3 | 5 | 2 |
| B | Diseño de la arquitectura y del flujo del sistema | A | 2 | 3 | 4 | 2 |
| C | Motor PERT-CPM (cálculo y asignación) | B | 4 | 5 | 8 | 1 |
| D | Base de conocimiento y búsqueda de referencias | B | 3 | 4 | 6 | 1 |
| E | Integración con la IA (cliente de Gemini) | B | 3 | 5 | 8 | 1 |
| F | Filtro de entrada y reglas de calidad | D, E | 3 | 4 | 6 | 1 |
| G | Interfaz web: Gantt y tabla | C | 4 | 6 | 9 | 2 |
| H | Interfaz web: grafo y edición de la red | G | 4 | 6 | 10 | 2 |
| I | Integración del servidor con la interfaz | F, H | 2 | 3 | 5 | 2 |
| J | Pruebas y ejemplos de demostración | I | 3 | 4 | 6 | 2 |
| K | Informe, README y diapositivas | J | 5 | 7 | 10 | 3 |
| L | Presentación y demostración | K | 1 | 1 | 2 | 4 |

```
            ┌── D ──┐
A ── B ──┬──┤       ├── F ──┐
         │  └── E ──┘       │
         └── C ── G ── H ───┴── I ── J ── K ── L
```

> **Importante:** los tiempos son una **propuesta**. Ajústenlos con su experiencia real de cuánto tomó cada parte, para que el caso sea
> propio. Si cambian valores, actualicen `app/caso_estudio.py` y los valores esperados en `app/test_caso_estudio.py`.

## 3. Qué hay que resolver a mano (con todo el procedimiento)

1. **Tiempo esperado y varianza** de cada actividad: `te` y `σ²`.
2. **Pasada hacia adelante:** ES y EF de cada actividad (`ES = máx EF de las predecesoras`, `EF = ES + te`).
3. **Duración esperada del proyecto** `T_E`.
4. **Pasada hacia atrás:** LF y LS (`LF = mín LS de las sucesoras`, `LS = LF − te`).
5. **Holguras** `H = LS − ES` y **ruta crítica** (actividades con `H = 0`).
6. **Desviación estándar del proyecto:** `σ_T = √(Σ σ²)` sobre la ruta crítica.
7. **Probabilidad de cumplir el plazo:** `Z = (D − T_E) / σ_T` y `P(T ≤ D) = Φ(Z)` con la tabla normal.
8. Responder: ¿qué actividades se pueden retrasar sin afectar el plazo y cuánto? ¿Qué pasaría si **E** tardara más de lo previsto?

## 4. Cargarlo en la herramienta

En la app, elige en **«Cargar un ejemplo»** la opción **«Caso de estudio · Construcción de este proyecto (sin IA)»**.
Se calcula al instante con el motor PERT-CPM, **sin usar la IA ni la cuota de Gemini**, y sirve para contrastar con lo manual.

Verificación adicional: `python test_caso_estudio.py` (desde `app/`) recalcula el caso con un método independiente
(enumerando todos los caminos de la red) y comprueba que coincide con el motor.

## 5. Qué entregar de este caso

- El procedimiento completo a mano (sección **Desarrollo** del informe), con una tabla de resultados.
- Captura de la herramienta con el mismo caso (sección **Resultados y discusión**).
- La tabla **manual vs. herramienta** y la explicación de cualquier diferencia.
