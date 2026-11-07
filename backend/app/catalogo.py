"""Catálogo público de competencias; solo configuración, sin acceso a la BD."""

COMPETENCIAS = [
    {
        "id": "chispazo",
        "nombre": "Chispazo",
        "descripcion": "Explora el historial y las tendencias de Chispazo.",
        "numeros_por_sorteo": 5,
        "numero_minimo": 1,
        "numero_maximo": 28,
        "modalidades": [
            {
                "id": "chispazo",
                "nombre": "Chispazo",
                "numeros_por_sorteo": 5,
                "numero_minimo": 1,
                "numero_maximo": 28,
            }
        ],
    },
    {
        "id": "melate",
        "nombre": "Melate",
        "descripcion": "Analiza Melate, Revancha y Revanchita de manera independiente.",
        "numeros_por_sorteo": 6,
        "numero_minimo": 1,
        "numero_maximo": 56,
        "modalidades": [
            {
                "id": "melate",
                "nombre": "Melate",
                "numeros_por_sorteo": 6,
                "numero_minimo": 1,
                "numero_maximo": 56,
                "numero_adicional": "R7 (solo informativo; no pertenece a la combinación principal)",
            },
            {
                "id": "revancha",
                "nombre": "Revancha",
                "numeros_por_sorteo": 6,
                "numero_minimo": 1,
                "numero_maximo": 56,
            },
            {
                "id": "revanchita",
                "nombre": "Revanchita",
                "numeros_por_sorteo": 6,
                "numero_minimo": 1,
                "numero_maximo": 56,
            },
        ],
    },
]
