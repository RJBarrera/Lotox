# Validación de lectura y motor — 2026-11-06

## Resultado comprobado

FastAPI consulta PostgreSQL real con `transaction_read_only=on`. Las columnas
numéricas y concurso son enteros, y fecha es de tipo date en las cuatro tablas.
No se modificaron datos, tablas, índices ni credenciales.

| Modalidad | Registros | Desde | Hasta |
|---|---:|---|---|
| Chispazo | 11 986 | 1999-01-05 | 2026-05-04 |
| Melate | 4 208 | 1984-08-19 | 2026-05-03 |
| Revancha | 2 882 | 1997-08-06 | 2024-04-21 |
| Revanchita | 1 520 | 2010-08-25 | 2024-04-21 |

No se encontraron números principales nulos, fuera de rango o repetidos dentro
del mismo sorteo, fechas nulas ni concursos duplicados. Los números principales
están ordenados en las columnas, requisito de la búsqueda exacta actual.

Las frecuencias de todo el historial y ventanas de 100 y 500 sorteos coinciden
con un conteo independiente en Python. R7 se excluye del conteo principal.
Ambas estrategias generan combinaciones válidas y diferentes dentro de la
solicitud en las cuatro modalidades. Esto valida funcionamiento, no capacidad
predictiva ni ventaja frente al azar.

## Pruebas ejecutadas

[Integración de lectura](../backend/tests/test_integracion_lectura.py): cinco
pruebas aprobadas en 66,180 segundos, con subcasos por modalidad y estrategia:

- Salud de API y base, catálogo y transacción de solo lectura.
- Calidad, resumen, historial paginado y frecuencias contra consultas directas.
- Verificación del último sorteo introducido en orden inverso.
- Generación mediante los endpoints reales para ambas estrategias.
- Rechazo de modalidad, números y parámetros inválidos.

Se utilizó un servidor HTTP local en puerto efímero, detenido al finalizar.
No se instalaron dependencias. La suite original de pytest no se ejecutó;
pytest y httpx no estaban disponibles en el entorno inspeccionado.

Para repetir, desde la carpeta backend, con acceso a la base configurada:

```powershell
$env:LOTOX_TEST_DATABASE = '1'
try {
  .\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_integracion_lectura.py -v
} finally {
  Remove-Item Env:LOTOX_TEST_DATABASE
}
```

Sin la variable de activación, las pruebas reales se omiten. No crean fixtures
en PostgreSQL ni necesitan pytest/httpx; usan las dependencias existentes y la
biblioteca estándar. Las comprobaciones fallan si los datos dejan de cumplir
las condiciones requeridas, en lugar de modificar o filtrar silenciosamente filas.

## Correcciones de frontend

- [App.jsx](../frontend/src/App.jsx) invalida y cancela solicitudes al cambiar
  modalidad, ventana o estrategia, navegar o editar la combinación consultada.
- [api.js](../frontend/src/api.js) conserva mensajes de error de FastAPI y
  permite descartar respuestas tardías incluso si la red ignora la cancelación.
- [Pruebas del cliente](../frontend/src/api.test.js) cubren errores, respuestas y
  sustitución de solicitudes mediante el runner integrado de Node, sin paquetes nuevos.
- [Plan reproducible](../frontend/.tsupgrader/runtime-validation/eval-plan.json)
  contempla compilación, pruebas y comprobación HTTP en el puerto 5175.

El editor no reportó errores en estos archivos ni en la nueva prueba Python.
La herramienta de validación del frontend fue cancelada antes de producir un
resultado. No se confirmó la compilación, la ejecución de sus nuevas pruebas
ni el comportamiento visual en navegador. No se generó standalone-result.json.

Comandos del frontend disponibles desde su carpeta: `npm test` y `npm run build`.

## Pendientes

1. Completar la validación del frontend y comprobar cambios rápidos de modalidad
   durante generación y búsqueda.
2. Actualización manual de históricos por el propietario, especialmente Revancha
   y Revanchita, cuyo último sorteo cargado es de abril de 2024.
3. Comparación con scripts originales cuando estén disponibles y evaluación
   cronológica del motor frente a selección aleatoria uniforme.

No se cambiaron las consultas SQL ni los algoritmos: las comprobaciones actuales
pasaron con el esquema y los datos existentes. No hubo commits ni despliegues
realizados por el agente.
