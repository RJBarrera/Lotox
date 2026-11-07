# Backtesting cronológico del motor

La nueva sección **Backtesting del motor**, dentro de cada modalidad, reconstruye
qué propuestas habría generado el motor actual antes de cada sorteo y cuenta sus
aciertos. No guarda predicciones ni resultados y no modifica PostgreSQL.

## Procedimiento

1. Leer la tabla de la modalidad mediante un único `SELECT`, exclusivamente con
   concurso, fecha y números principales. Melate excluye R7; Revanchita usa f1–f6.
2. Validar fechas, concursos únicos, cantidad, rango y unicidad de los números.
   Si hay datos inválidos se devuelve un error; no se corrigen ni eliminan filas.
3. Ordenar cronológicamente por fecha y concurso. Dentro de una misma fecha se
   asume que el concurso mayor sucedió después; no hay hora del sorteo disponible.
4. Evaluar los últimos N sorteos. Antes de cada uno, calcular el ranking solo
   con los anteriores, limitado por la ventana seleccionada. Ventana cero usa
   todos los anteriores. Se exige un mínimo de entrenamiento.
5. Generar igual cantidad de combinaciones con `clasica`, `frecuencia` y
   `equilibrada`, mediante la misma función que usa el generador habitual.
6. Compararlas con el resultado real mediante la intersección de números.
   Solo después incorporar ese sorteo al entrenamiento del siguiente.
7. Repetir la referencia aleatoria uniforme con igual cantidad de combinaciones
   por sorteo, sin números repetidos ni combinaciones duplicadas dentro de cada
   solicitud. Cada réplica representa una evaluación completa del mismo período.

No hay búsqueda de parámetros ni selección automática de la mejor estrategia.
La estrategia clásica conserva su desempate por número ascendente y sus ventanas
consecutivas dentro del ranking. Las ponderadas conservan sus pesos anteriores.
El generador habitual sigue usando `SystemRandom`; el backtesting utiliza
`Random` con semillas estables por modalidad, concurso, fecha, estrategia y réplica.

## API

`GET /api/v1/modalidades/{modalidad}/backtesting`

| Parámetro | Por defecto | Valores |
|---|---:|---|
| `sorteos` | 100 | 1–500; últimos sorteos a evaluar |
| `ventana` | 500 | 0–20000; máximo de sorteos anteriores por evaluación |
| `entrenamiento_minimo` | 100 | 1–20000; no puede superar una ventana positiva |
| `cantidad` | 3 | 1–5 combinaciones por sorteo y estrategia |
| `semilla` | 42 | Entero entre 0 y 4294967295 |
| `repeticiones` | 30 | 2–100 réplicas de la referencia uniforme |

Ejemplo: `/api/v1/modalidades/chispazo/backtesting?sorteos=100&ventana=500&semilla=42`.

La interfaz permite elegir N, ventana y semilla. Mantiene tres combinaciones,
30 réplicas y mínimo de 100 sorteos de entrenamiento. Si no hay suficientes datos,
el backend devuelve 422 en lugar de reducir silenciosamente la muestra. Una
modalidad desconocida devuelve 404; los errores de conexión mantienen el 503
existente y no revelan credenciales.

## Interpretación

- `media_aciertos`: suma de aciertos / número de combinaciones evaluadas.
- `media_mejor_por_sorteo`: promedio del mayor número de aciertos entre las
  combinaciones de cada sorteo. No debe compararse con una sola apuesta aleatoria.
- `distribucion_aciertos`: conteos de combinaciones con 0, 1, …, 5 o 6 aciertos.
- `distribucion_mejor_por_sorteo`: conteos de sorteos por su mejor resultado.
- `diferencia_media_vs_uniforme`: media de la estrategia menos la media de las
  réplicas uniformes; puede ser negativa. No es un porcentaje ni una probabilidad.
- La referencia incluye medias, desviación poblacional de las medias, mínimo,
  máximo, distribuciones promedio y métricas separadas de cada réplica. Los
  conteos promedio pueden ser fraccionarios. Todas las réplicas tienen el mismo
  presupuesto de combinaciones que cada estrategia.

El detalle conserva propuestas y aciertos de las tres estrategias, el resultado
real, el número de sorteos de entrenamiento y su último concurso. También incluye
las propuestas de la **primera réplica uniforme**, identificada expresamente;
los totales de la referencia usan todas las réplicas.

La respuesta incorpora parámetros, período, versión `walk-forward-v1` y huella
SHA-256 del historial ordenado leído. Mismos datos, parámetros, implementación y
entorno Python reproducen el resultado. Si se cargan nuevos sorteos, «últimos N»
selecciona otro período. La huella permite detectar un cambio de datos, pero no
reconstruye un historial previo: no existe persistencia de instantáneas.

## Límites metodológicos

- Es una simulación retrospectiva del motor actual, no evidencia de predicciones
  realmente emitidas en aquellas fechas.
- Se presuponen las reglas actuales (5/28 o 6/56). No se modelan cambios históricos
  del universo de números. Comparaciones sobre épocas con reglas distintas no
  deben interpretarse como prueba justa de rendimiento; revisar el período.
- Una diferencia favorable en esta muestra puede deberse al azar. El rango
  mínimo–máximo entre réplicas no es un intervalo de confianza ni una prueba
  de significación. Las estrategias ponderadas se ejecutan una vez por semilla;
  sus propios resultados también varían entre semillas.
- Modificar parámetros después de observar el resultado introduce selección
  sobre la muestra: esa elección necesita otro período todavía no utilizado.
- No se calculan premios, rentabilidad, porcentajes de ganar ni se garantiza
  ventaja futura. Los aciertos se refieren solo a números principales.
- El resultado depende de la calidad y actualidad de los datos cargados.

## Archivos

- [backtesting.py](../backend/app/backtesting.py): lectura, simulación y métricas.
- [historial.py](../backend/app/historial.py): función de generación compartida.
- [main.py](../backend/app/main.py): nueva ruta REST.
- [BacktestingPanel.jsx](../frontend/src/BacktestingPanel.jsx): controles, tabla
  comparativa, distribución y detalle por sorteo; se desmonta al cambiar modalidad.
- [App.jsx](../frontend/src/App.jsx) y [styles.css](../frontend/src/styles.css):
  integración del panel y estilos de sus tablas.
- [test_backtesting.py](../backend/tests/test_backtesting.py): 12 pruebas
  deterministas de lógica y API, sin red, PostgreSQL ni dependencias adicionales.

## Validación de esta implementación

- `npm test`: **5 pruebas del cliente API aprobadas**.
- `npm run build`: **compilación de React/Vite aprobada**, 32 módulos transformados.
- Editor: sin errores reportados en los archivos Python y el panel nuevo.
- Pruebas Python nuevas: **pendientes de ejecución**. El entorno restringido
  bloqueó el intérprete y la solicitud de ejecución ampliada fue rechazada.
- Validación del nuevo endpoint contra PostgreSQL y flujo visual completo:
  **pendientes**. No se presentan resultados de backtesting reales como ya medidos.

Para ejecutar las pruebas nuevas desde backend con el entorno existente:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_backtesting.py -v
```

Cubren ausencia de fuga del resultado actual y futuro, incorporación cronológica,
ventana móvil y expansiva, reproducibilidad, presupuesto igual, conteos de aciertos
conocidos, las cuatro modalidades, exclusión de R7, SQL SELECT, parámetros y
respuestas HTTP. La suite anterior de pytest sigue disponible por separado.
