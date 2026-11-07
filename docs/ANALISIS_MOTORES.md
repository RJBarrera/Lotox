# LotoX · Análisis de los cuatro scripts originales

Fecha de revisión: 2026-11-06. Origen: archivos facilitados por el usuario.

## Historial disponible en los archivos proporcionados

| Modalidad | Registros | Primera fecha | Última fecha | Selección principal | Cabeceras CSV |
|---|---:|---|---|---|---|
| Chispazo | 11 986 | 1999-01-05 | 2026-05-04 | R1-R5, 5/28 | CONCURSO,R1-R5,FECHA |
| Melate | 4 208 | 1984-08-19 | 2026-05-03 | R1-R6, 6/56 | NPRODUCTO,CONCURSO,R1-R7,BOLSA,FECHA |
| Revancha | 2 882 | 1997-08-06 | 2024-04-21 | R1-R6, 6/56 | NPRODUCTO,CONCURSO,R1-R6,BOLSA,FECHA |
| Revanchita | 1 520 | 2010-08-25 | 2024-04-21 | F1-F6, 6/56 | NPRODUCTO,CONCURSO,F1-F6,BOLSA,FECHA |

Importante: en Melate R7 es un número adicional; no se incorpora a la selección de 6 números principales.

## Capacidades actuales

1. Descarga de historial en CSV desde la web mediante Selenium.
2. Carga de datos con pandas.
3. Búsqueda de combinación exacta en sorteos anteriores.
4. Cálculo de frecuencia individual de cada número.
5. Generación de grupos a partir de números frecuentes.
6. Listado de combinaciones repetidas.
7. Presentación en consola y cuadros Tkinter.

## Problemas identificados

- Revancha y Revanchita: `generar_combinaciones_probables()` llama `calcular_probabilidades_combinaciones()` con tres parámetros, pero esta última acepta dos; produce `TypeError`.
- El cálculo `producto(frecuencia_numero/total_sorteos)` asume independencia entre números extraídos sin reemplazo, y además trata el resultado como porcentaje sin convertirlo correctamente. NO es la probabilidad de ganar.
- `verificar_existencia_combinaciones()` existe pero no está integrada en la presentación de las recomendaciones: los mensajes afirman que las combinaciones nunca salieron sin comprobarlo.
- La carga está acoplada a índices de columnas; es preferible acceder por nombres (`R1`... / `F1`...).
- La lectura / actualización del archivo se hace dentro de funciones de consola. En la web se sustituirá por repositorios de lectura SQL y rutas FastAPI.
- Los CSV de Revancha y Revanchita están desactualizados respecto a la fecha de revisión. No deben describirse como históricos completos sin verificarlos y ampliarlos.

## Principios para el nuevo motor

- Un único motor parametrizado por modalidad, sin duplicar cuatro implementaciones.
- Probabilidad teórica de una combinación exacta de 5/28: `1 / C(28,5)`.
- Probabilidad teórica de una combinación exacta de 6/56: `1 / C(56,6)`.
- Distinguir explícitamente métricas DESCRIPTIVAS y probabilidad MATEMÁTICA. No prometer ventaja predictiva.
- Cada consulta a base de datos será de solo lectura. El usuario administra esquemas, tablas, cargas e índices.

## Próximos endpoints (no implementados aún)

- `GET /api/v1/competencias/{competencia}/modalidades/{modalidad}/sorteos`
- `GET /api/v1/competencias/{competencia}/modalidades/{modalidad}/frecuencias`
- `POST /api/v1/analisis/verificar-combinacion` (solo lecturas de BD; se enviará la combinación en el cuerpo)
- `POST /api/v1/analisis/generar-combinaciones` (sin promesa de acierto)

Primero se acordará el esquema de tablas que creará el usuario. Ninguno de estos endpoints está habilitado en la fase 1.
