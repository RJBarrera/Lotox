# LotoX v0.4 — Recuperación de funciones de los cuatro Python originales

## Revisión del código recibido

Los scripts `_chispazo.py`, `_melate.py`, `_revancha.py` y `_revanchita.py` incluían, entre otros:

1. Obtener frecuencia individual de números.
2. Generar cinco combinaciones desplazando una ventana por el ranking de los números más frecuentes.
3. Verificar si una combinación exacta apareció en el histórico.
4. Buscar las cinco combinaciones más repetidas.
5. Asignar un supuesto porcentaje de probabilidad mediante el producto de frecuencias individuales.

La versión 0.3 ya cubría los puntos 1 y 3, y ofrecía dos estrategias de generación ponderada. La versión 0.4 añade los puntos 2 y 4, sin reproducir el punto 5 porque NO es una fórmula válida de probabilidad de ganar.

## Cambios de la v0.4

- `GET /api/v1/modalidades/{modalidad}/predicciones?cantidad=3&ventana=500&estrategia=clasica`
  - Método determinista de los scripts originales: ordenar por frecuencia descendente (desempate por número ascendente) y seleccionar ventanas consecutivas de tamaño 5 o 6.
  - Mantiene `frecuencia` y `equilibrada` intactas, con el mismo formato de respuesta.
- `GET /api/v1/modalidades/{modalidad}/combinaciones-repetidas?limite=5`
  - Lista hasta cinco combinaciones principales que se repitieron al menos dos veces, con sus apariciones y última fecha.
  - Cuando ninguna combinación se repitió, devuelve lista vacía. No dice que combinaciones con una sola aparición sean 'repetidas'.
  - Melate excluye R7; Revanchita utiliza `f1` a `f6`.
- Frontend: nueva estrategia en el selector y sección de combinaciones repetidas.
- Nuevas pruebas automatizadas aisladas de PostgreSQL.

## Restricciones de seguridad

- Todas las consultas nuevas a PostgreSQL son `SELECT`.
- Tablas y columnas se obtienen de un catálogo estático; el usuario no introduce identificadores SQL arbitrarios.
- No crea tablas, no escribe predicciones ni importa históricos.
- **No se incluyen archivos `.env` en este paquete.** Deben conservarse únicamente en la instalación local.

## Validación en entorno de revisión

- Pruebas cliente API (`npm test`): 5 aprobadas.
- Pruebas Python de motor y API: 16 aprobadas con la importación de `psycopg` simulada, sin conexiones externas.
- Sintaxis Python: comprobada.
- **Pendiente**: compilar frontend (`npm run build`) en un equipo con dependencias de npm instaladas; validar la nueva ruta contra PostgreSQL real; revisar navegación visual.

## Siguientes módulos recomendados

1. Sistema de análisis de combinaciones ingresadas por el usuario: frecuencia de cada número y métricas descriptivas, sin 'probabilidad' falsa.
2. Backtesting cronológico por modalidad, usando solamente datos anteriores a cada sorteo, y referencia uniforme con semilla reproducible.
3. Registro de evaluaciones/predicciones solo si el usuario autoriza después un diseño de almacenamiento (sin creación automática de tablas).

Los históricos actuales de Revancha y Revanchita terminan en abril de 2024 y los de Melate/Chispazo en mayo de 2026; no deben presentarse como resultados oficiales actualizados.
