# Clave de respuestas del caso de estudio (solo para VERIFICAR)

> Úsenla **después** de resolver el caso a mano. La guía exige que la solución manual refleje la comprensión del equipo:
> copiar esta tabla no cuenta como solución. Sirve para comprobar el resultado y para el contraste del paso 6.

Calculada con el motor (`app/cpm.py`) y **verificada con un método independiente** (enumeración de todos los caminos de la red,
`app/test_caso_estudio.py`). Ambos coinciden. Valores con 2 decimales (el motor guarda 6).

## Resultados por actividad

| ID | te | σ² | ES | EF | LS | LF | H | Crítica |
|---|---|---|---|---|---|---|---|---|
| A | 3.17 | 0.2500 | 0.00 | 3.17 | 0.00 | 3.17 | 0.00 | Sí |
| B | 3.00 | 0.1111 | 3.17 | 6.17 | 3.17 | 6.17 | 0.00 | Sí |
| C | 5.33 | 0.4444 | 6.17 | 11.50 | 6.17 | 11.50 | 0.00 | Sí |
| D | 4.17 | 0.2500 | 6.17 | 10.33 | 15.67 | 19.83 | 9.50 | No |
| E | 5.17 | 0.6944 | 6.17 | 11.33 | 14.67 | 19.83 | 8.50 | No |
| F | 4.17 | 0.2500 | 11.33 | 15.50 | 19.83 | 24.00 | 8.50 | No |
| G | 6.17 | 0.6944 | 11.50 | 17.67 | 11.50 | 17.67 | 0.00 | Sí |
| H | 6.33 | 1.0000 | 17.67 | 24.00 | 17.67 | 24.00 | 0.00 | Sí |
| I | 3.17 | 0.2500 | 24.00 | 27.17 | 24.00 | 27.17 | 0.00 | Sí |
| J | 4.17 | 0.2500 | 27.17 | 31.33 | 27.17 | 31.33 | 0.00 | Sí |
| K | 7.17 | 0.6944 | 31.33 | 38.50 | 31.33 | 38.50 | 0.00 | Sí |
| L | 1.17 | 0.0278 | 38.50 | 39.67 | 38.50 | 39.67 | 0.00 | Sí |

## Resultados del proyecto

- **Duración esperada:** `T_E = 39.67` días.
- **Ruta crítica:** **A → B → C → G → H → I → J → K → L** (única).
- **Varianza de la ruta crítica:** `σ_T² = 0.25 + 0.1111 + 0.4444 + 0.6944 + 1.0 + 0.25 + 0.25 + 0.6944 + 0.0278 = 3.7222`
- **Desviación estándar:** `σ_T = 1.93` días.
- **Probabilidad de cumplir el plazo** (`Z = (D − 39.67) / 1.93`):

| Plazo D | Z | P(T ≤ D) |
|---|---|---|
| 40 días | 0.17 | 56.9 % |
| **42 días** | **1.21** | **88.7 %** |
| 45 días | 2.76 | 99.7 % |

## Lectura de los resultados

- Las actividades **D, E y F** (base de conocimiento, integración con la IA y filtro de entrada) tienen holgura de **9.5, 8.5 y 8.5 días**:
  pueden retrasarse sin afectar el plazo.
- Esa rama **no** es crítica: el camino `A-B-C-G-H` (motor y dos interfaces) es el que fija la duración. Un retraso de la **interfaz** sí retrasa todo el proyecto.
- Si **E** se retrasara **8.5 días o más**, la rama `B-E-F` pasaría a ser crítica (con 8.5 exactos habría dos rutas críticas a la vez).

## Nota sobre el redondeo

Un cálculo manual con 2 decimales puede diferir en centésimas del motor (que trabaja con 6). Eso **no** es un error: debe
mencionarse en la contrastación (paso 6) como causa de las diferencias.
