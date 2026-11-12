# Prompt para NotebookLM: diapositivas de la exposición

## Cómo usarlo

1. En NotebookLM crea un cuaderno y **sube como fuentes** (en este orden de importancia):
   - `README.md`
   - `docs/CASO_DE_ESTUDIO.md`
   - `docs/EJEMPLOS_DEMO.md`
   - `docs/CASO_DE_ESTUDIO_CLAVE.md` **solo cuando ya hayan hecho la solución manual** (para que la presentación use sus resultados)
   - Opcional: la guía del proyecto (`Proyecto_Final.pdf`) para que ajuste lo que pide la rúbrica.
   - **No subas** el archivo `.env` (contiene tu clave).
2. Si tu NotebookLM tiene la función de **presentación / diapositivas**, pega el prompt en el cuadro de instrucciones personalizadas.
   Si no, pégalo en el chat: te devolverá el contenido de cada diapositiva para pasarlo a PowerPoint o Google Slides.
3. Revisa el resultado contra tus datos reales, reemplaza los `[COMPLETAR]` y **ensayen con cronómetro**.

---

## El prompt (cópialo completo)

```
Actúa como diseñador de presentaciones académicas. Usando SOLO las fuentes cargadas, crea una presentación de 16
diapositivas para una exposición de 15 minutos (más 5 de preguntas) de la asignatura Investigación Operativa, ante el docente
y compañeros de la carrera de Software. Expondrán 4 personas.

TEMA: "Planificador de proyectos de software con PERT-CPM asistido por IA". Es un sistema que recibe la descripción de un
proyecto de software y genera su plan: actividades, tiempos, ruta crítica, diagrama de Gantt, grafo de la red y asignación del
equipo. Una IA (Gemini) propone las actividades y los tiempos; el cálculo PERT-CPM lo hace código propio y se puede verificar a mano.

REGLAS DE ESTILO
- Lenguaje simple y directo, fácil de entender y fácil de practicar. Evita jerga innecesaria y explica cada término técnico la primera vez.
- Una sola idea por diapositiva. Máximo 4 viñetas, de máximo 12 palabras cada una. Nada de párrafos.
- Para cada diapositiva sugiere UN visual (diagrama, tabla pequeña, captura, esquema) y descríbelo entre corchetes.
- Diseño: fondo claro, títulos grandes (mínimo 32 pt) y texto mínimo de 20 pt. Colores: índigo #4F46E5 para títulos y acentos,
  coral #FF6B5E para la RUTA CRÍTICA, azul #3B82F6 para actividades con holgura. Tipografía sans-serif.
- Para cada diapositiva entrega: Título · Viñetas · Visual sugerido · Notas del orador (2 o 3 frases en tono natural, fáciles de
  decir en voz alta) · Tiempo · Quién expone (Persona 1, 2, 3 o 4).
- NO inventes datos, cifras ni resultados. Si un dato no está en las fuentes (por ejemplo el resultado de la solución manual),
  escribe [COMPLETAR].
- Los tiempos deben sumar 15 minutos. Reparte las partes de forma equilibrada entre las 4 personas.

ESTRUCTURA (adáptala si las fuentes lo requieren)
1. Portada: título, integrantes, docente, fecha. (Persona 1 · 0:20)
2. El problema: por qué es difícil planificar un proyecto de software. (P1 · 0:45)
3. Objetivos del proyecto: general y 3 específicos. (P1 · 0:45)
4. ¿Qué es PERT-CPM?: actividad, precedencia, ruta crítica y holgura, con un dibujo simple. (P1 · 1:00)
5. Las fórmulas que usamos: te, varianza, ES/EF/LS/LF, holgura y probabilidad, con un mini ejemplo. (P1 · 1:00)
6. Nuestra idea: la IA estima y el código calcula. (P2 · 1:00)
7. Cómo funciona el sistema en 6 pasos (diagrama de flujo): validar, filtrar, buscar referencias, estimar con IA, verificar reglas,
   calcular. (P2 · 1:15)
8. Qué hace la IA y qué hace el código (tabla de dos columnas) y por qué no confiamos solo en la IA. (P2 · 0:45)
9. Caso de estudio: la construcción de este mismo proyecto como red de 12 actividades (mostrar la red). (P2 · 1:00)
10. Solución manual paso a paso: pasada hacia adelante, pasada hacia atrás, holguras y ruta crítica. (P3 · 1:15)
11. Resultados: tabla comparando lo manual con la herramienta, ruta crítica y probabilidad de cumplir el plazo. (P3 · 1:00)
12. Casos de prueba: al menos 3, incluido un caso límite, con lo esperado y lo obtenido. (P3 · 1:00)
13. Demostración en vivo: guion de 2 minutos (cargar un ejemplo, ver Gantt, tabla, ruta crítica, grafo y editar un paso). (P4 · 2:00)
14. Análisis crítico: validez y limitaciones (estimaciones de la IA, base de conocimiento no real, cuota de Gemini). (P4 · 0:45)
15. Conclusiones y recomendaciones. (P4 · 0:45)
16. Gracias / Preguntas. (P4 · 0:25)

ANEXO (diapositivas extra, no cuentan para el tiempo): declaración de uso de IA (Gemini como componente del sistema; Claude como
apoyo para escribir y revisar el código) y referencias en formato APA 7.

SALIDA: primero un índice con número, título, persona y tiempo de cada diapositiva; después el contenido completo de cada una.
Al final agrega 5 posibles preguntas del docente con una respuesta corta para cada una.
```

---

## Después de generar las diapositivas

- **Verifiquen cada cifra** contra su solución manual y la herramienta; NotebookLM solo conoce lo que está en las fuentes.
- Sustituyan todos los `[COMPLETAR]` (integrantes, docente, fecha, resultados manuales, casos de prueba).
- Pongan **capturas reales de la app** en las diapositivas de resultados y de la demostración (Gantt, grafo, tabla).
- Graben un **video de respaldo** de la demostración por si falla internet o se agota la cuota de Gemini. Alternativa sin IA:
  el ejemplo **«Caso de estudio»** de la app funciona sin conexión a Gemini.
- Ensayen completo con cronómetro: 15 minutos exactos, todos hablando una parte sustancial.
