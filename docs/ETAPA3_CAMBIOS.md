# Cambios Etapa 3 — LotoX

Motor básico inspirado en los scripts Python originales: utiliza conteos históricos de números principales, pero no traslada su fórmula de 'probabilidad' basada en multiplicación de frecuencias porque no es una probabilidad matemáticamente válida.

La estrategia de frecuencia utiliza pesos `apariciones + 1`. La estrategia equilibrada utiliza 50% peso uniforme + 50% de frecuencia normalizada, con suavizado. Ambas seleccionan al azar sin reemplazo y ordenan los números para presentarlos. Se generan tres combinaciones únicas por solicitud, sin insertarlas en PostgreSQL ni prometer predicción acertada.

Melate excluye la bola adicional R7 en el cómputo de frecuencias y generación. Revanchita utiliza columnas `f1` a `f6`. No hay trabajo de descarga CSV, Selenium, Tkinter ni escritura SQL.

La conexión utiliza `DATABASE_URL` solo en backend. `default_transaction_read_only=on` y `statement_timeout=8000` previenen mutaciones accidentales y consultas ilimitadas. Se recomienda limitar permisos SQL SELECT en Railway.
