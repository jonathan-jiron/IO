# Planificador PERT-CPM asistido por IA

Proyecto final de **Investigación Operativa** (Universidad Técnica de Ambato, carrera de Software).

El sistema recibe la descripción de un proyecto de software y genera, de inicio a fin, su plan de trabajo:
actividades, tiempos estimados (PERT), **ruta crítica**, holguras, **diagrama de Gantt**, **grafo de la red** y
**asignación del equipo** por integrante. Una IA (Gemini) propone las actividades y las estimaciones; **todo el
cálculo PERT-CPM lo hace código propio, determinista y verificable a mano**.

> Integrantes: _(completar con los nombres del equipo)_ · Docente: _(completar)_

---

## Qué hace

| Página | Contenido |
|---|---|
| **1 · Plan** | Diagrama de Gantt, tabla PERT-CPM editable (a, m, b, personas) y ruta crítica |
| **2 · Equipo y tiempos** | Duración, σ y probabilidad de cumplir un plazo; carga por integrante; evaluación de si el equipo sobra o falta; análisis de la IA |
| **3 · Grafo** | Grafo de la red (ruta crítica en coral). Permite **añadir, editar, reubicar y eliminar pasos**, fijar un **responsable** (p. ej. un especialista) y aplicar un factor de tiempo |

Además: filtro de entrada (rechaza lo que no es software o está muy poco descrito e ignora el ruido), verificación
de reglas de sentido común con corrección automática, y 8 ejemplos de demostración cargables con un clic.

## Cómo funciona

```
Descripción ──► 1. Validación local (¿muy corta?)
            ──► 2. IA: filtro (¿es software? ¿cuánto detalle? ¿qué se ignora?)
            ──► 3. Código: busca los 3 proyectos más parecidos en la base de conocimiento (TF-IDF + coseno)
            ──► 4. IA: propone actividades, precedencias, tiempos (a, m, b), personas y complejidad
            ──► 5. Código: verifica reglas de sentido común → si falla, la IA corrige (hasta 3 intentos)
            ──► 6. Código: te, σ², ES/EF/LS/LF, holguras, ruta crítica, probabilidad, asignación, Gantt, grafo
```

| La IA (Gemini) | El código (determinista) |
|---|---|
| Filtra la entrada | Valida y recupera referencias (TF-IDF) |
| Propone actividades, precedencias, tiempos y personas | Verifica reglas y pide correcciones |
| Estima complejidad y opina sobre el equipo | Calcula todo el PERT-CPM, reparte el trabajo, dibuja Gantt y grafo |

Fórmulas usadas: `te = (a + 4m + b) / 6`, `σ² = ((b − a) / 6)²`, pasada hacia adelante y hacia atrás
(ES, EF, LS, LF), holgura `H = LS − ES` y `P(T ≤ D) = Φ((D − T_E) / σ_T)`.

## Requisitos

- **Python 3.10 o superior**
- Una **API key de Gemini** (gratuita en [Google AI Studio](https://aistudio.google.com/apikey))
- Dependencias: `flask` y `requests`

## Instalación y uso

```bash
git clone <URL-del-repositorio>
cd <carpeta-del-repositorio>/app
pip install -r requirements.txt
```

**1. Configura tu key** (el archivo `.env` es privado y **nunca se sube al repositorio**):

```bash
copy .env.example .env      # en Windows (en Linux/Mac: cp .env.example .env)
```

Abre `app/.env` y escribe tu clave:

```
GEMINI_API_KEY=tu_clave_aqui
GEMINI_MODEL=gemini-3.1-flash-lite,gemini-3.5-flash,gemini-3.5-flash-lite
```

`GEMINI_MODEL` admite **varios modelos separados por comas**: si uno agota su cuota o está saturado, se usa el siguiente.
No hace falta reiniciar al editar el archivo.

**2. Arranca el servidor:**

```bash
python server.py
```

(o doble clic en `app/ejecutar.bat` en Windows). Se abre `http://127.0.0.1:8765`. Deja la ventana abierta mientras uses la app.

**3. Úsala:** pega una descripción o elige un ejemplo en **«Cargar un ejemplo»**, indica el número de integrantes
(y sus nombres) y pulsa **Generar plan**.

## Ejemplos de demostración

Hay 8 ejemplos dentro de la página (corto, pocos pasos, medio, largo, con ruido, sin software, muy vago y demasiado corto).
La guía con el guion y los resultados observados está en [`docs/EJEMPLOS_DEMO.md`](docs/EJEMPLOS_DEMO.md).

## Pruebas

Las pruebas no gastan cuota de Gemini (usan respuestas simuladas). Desde la carpeta `app/`:

```bash
python test_cpm.py       # motor PERT-CPM
python test_edit.py      # eliminar, reubicar y responsable fijo
python test_rules.py     # reglas de sentido común
python test_intake.py    # que la capacitación y el ciclo de vida no se pierdan
python test_server.py    # rutas de rechazo del servidor
python test_models.py    # cadena de modelos de Gemini
python check_kb.py       # valida los 16 proyectos de la base de conocimiento
```

## Estructura

```
app/
  server.py          Servidor Flask y API (/api/generate, /compute, /add, /move, /delete)
  cpm.py             Motor PERT-CPM, edición de la red y asignación del equipo
  gemini_client.py   Cliente de Gemini: filtro, planificación, esquema estricto, reintentos y cadena de modelos
  intake.py          Reconcilia el filtro de la IA con el texto original
  rules.py           Reglas de sentido común del plan
  kb.py, kb_extra.py Base de conocimiento (16 proyectos de referencia) y búsqueda TF-IDF
  config.py          Lectura de .env (la key nunca llega al navegador)
  static/            Interfaz (HTML, CSS, JS, ejemplos.json, favicon)
  test_*.py          Pruebas
docs/
  EJEMPLOS_DEMO.md   Guía de demostración
  CHECKLIST_RUBRICA.md  Qué cubre el proyecto y qué falta para el informe
```

## Limitaciones

- Los **16 proyectos** de la base de conocimiento son referencias plausibles armadas por el equipo, **no datos medidos** de proyectos reales.
- Los tiempos son **estimaciones de la IA**; no se validan contra proyectos terminados. Por eso se usa PERT con tres tiempos.
- Un mismo texto puede producir planes algo distintos entre ejecuciones.
- La capa gratuita de Gemini limita el uso **diario por modelo**; cada plan usa entre 2 y 4 llamadas.

## Solución de problemas

| Problema | Solución |
|---|---|
| «No se pudo contactar con el servidor local» | El servidor no está corriendo. Ejecuta `python server.py` y entra a `http://127.0.0.1:8765` (no abras `index.html` directo). |
| «Falta la API key» / indicador rojo | Revisa que `app/.env` exista y tenga `GEMINI_API_KEY=...` |
| «Ningún modelo de Gemini está disponible» | Cuota diaria o saturación. Espera un minuto, agrega más modelos en `GEMINI_MODEL` o usa otra key. |
| El puerto 8765 está ocupado | Cierra el otro programa o cambia el puerto al final de `app/server.py`. |

## Uso de inteligencia artificial

Este proyecto usa **Gemini** como componente del sistema (estimación de actividades y tiempos) y se desarrolló con
apoyo de un asistente de IA (**Claude**) para escribir y revisar código. Esto debe declararse en el informe, en el
párrafo final de **Anexos**, según la guía del proyecto.
