"""Conexión de solo lectura a PostgreSQL; nunca administra esquemas ni datos."""

import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()


class DatabaseNotConfigured(Exception):
    """Falta DATABASE_URL en la configuración del backend."""


@contextmanager
def conexion_lectura():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise DatabaseNotConfigured("Falta DATABASE_URL en backend/.env")
    # Defensas complementarias: transacciones read-only y rol SELECT recomendado.
    with psycopg.connect(
        url,
        row_factory=dict_row,
        connect_timeout=6,
        options="-c default_transaction_read_only=on -c statement_timeout=8000",
    ) as conn:
        yield conn
