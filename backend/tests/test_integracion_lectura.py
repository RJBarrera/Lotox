"""Pruebas opt-in de FastAPI y PostgreSQL real, exclusivamente de lectura.

Desde backend: LOTOX_TEST_DATABASE=1 y python -m unittest discover
-s tests -p test_integracion_lectura.py -v. No necesita pytest/httpx.
"""

import json
import os
import socket
import threading
import time
import unittest
from collections import Counter
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import uvicorn

from app.db import conexion_lectura
from app.historial import MODALIDADES
from app.main import app


@unittest.skipUnless(os.getenv("LOTOX_TEST_DATABASE") == "1", "Requiere autorización explícita LOTOX_TEST_DATABASE=1")
class IntegracionLectura(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Un puerto local efímero evita interferir con servidores del usuario.
        cls.socket = socket.socket()
        cls.socket.bind(("127.0.0.1", 0))
        cls.base = f"http://127.0.0.1:{cls.socket.getsockname()[1]}/api/v1"
        cls.server = uvicorn.Server(uvicorn.Config(app, log_config=None, log_level="critical", access_log=False))
        cls.thread = threading.Thread(target=cls.server.run, kwargs={"sockets": [cls.socket]}, daemon=True)
        cls.addClassCleanup(cls.detener)
        cls.thread.start()
        limite = time.monotonic() + 10
        while not cls.server.started:
            if not cls.thread.is_alive() or time.monotonic() >= limite:
                raise RuntimeError("No arrancó el servidor local de validación.")
            time.sleep(0.05)

    @classmethod
    def detener(cls):
        cls.server.should_exit = True
        cls.thread.join(timeout=10)
        cls.socket.close()
        if cls.thread.is_alive():
            raise RuntimeError("El servidor de validación no se detuvo.")

    def consultar(self, ruta, params=None, estado=200):
        url = self.base + ruta + ("?" + urlencode(params) if params else "")
        try:
            response = urlopen(url, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            self.assertEqual(response.status, estado)
            return json.load(response)

    def test_salud_catalogo_y_solo_lectura(self):
        self.assertEqual(self.consultar("/health")["status"], "ok")
        self.assertEqual(self.consultar("/db/health")["status"], "ok")
        self.assertEqual({c["id"] for c in self.consultar("/competencias")["data"]}, {"chispazo", "melate"})
        with conexion_lectura() as conn:
            self.assertEqual(conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"], "on")

    def test_historial_resumen_calidad_y_frecuencias(self):
        for modo, cfg in MODALIDADES.items():
            with self.subTest(modalidad=modo):
                cols = cfg.columnas + ((cfg.adicional,) if cfg.adicional else ())
                with conexion_lectura() as conn:
                    filas = conn.execute(f"SELECT concurso, fecha, {', '.join(cols)} FROM {cfg.tabla} ORDER BY fecha DESC, concurso DESC").fetchall()
                self.assertTrue(filas, "Se requiere historial para validar el motor.")
                numeros = [[fila[c] for c in cfg.columnas] for fila in filas]
                self.assertEqual(len({f['concurso'] for f in filas}), len(filas))
                for fila, ns in zip(filas, numeros):
                    self.assertIsNotNone(fila['fecha'])
                    self.assertEqual(len(set(ns)), len(ns))
                    self.assertTrue(all(isinstance(n, int) and 1 <= n <= cfg.maximo for n in ns))
                    self.assertEqual(ns, sorted(ns), "La búsqueda exacta actual requiere columnas ordenadas.")
                resumen = self.consultar(f"/modalidades/{modo}/resumen")
                self.assertEqual(resumen['registros'], len(filas))
                self.assertEqual(resumen['desde'], str(min(f['fecha'] for f in filas)))
                self.assertEqual(resumen['hasta'], str(max(f['fecha'] for f in filas)))
                self.assertEqual(resumen['ultimo']['numeros'], numeros[0])
                self.assertEqual(resumen['ultimo']['adicional'], filas[0][cfg.adicional] if cfg.adicional else None)
                pagina = self.consultar(f"/modalidades/{modo}/historial", {'limite': 3, 'pagina': 2})['data']
                self.assertEqual([f['concurso'] for f in pagina], [f['concurso'] for f in filas[3:6]])
                for ventana in (0, 100, 500):
                    datos = self.consultar(f"/modalidades/{modo}/frecuencias", {'ventana': ventana})
                    muestra = numeros[:ventana] if ventana else numeros
                    conteo = Counter(n for ns in muestra for n in ns)
                    self.assertEqual(datos['sorteos_analizados'], len(muestra))
                    self.assertEqual({r['numero']: r['apariciones'] for r in datos['ranking']}, {n: conteo[n] for n in range(1, cfg.maximo + 1)})

    def test_verificacion_conocida_en_orden_inverso(self):
        for modo in MODALIDADES:
            with self.subTest(modalidad=modo):
                ultimo = self.consultar(f"/modalidades/{modo}/resumen")['ultimo']
                datos = self.consultar(f"/modalidades/{modo}/verificar", {'numeros': ','.join(map(str, reversed(ultimo['numeros'])))})
                self.assertGreaterEqual(datos['apariciones_historicas'], 1)
                self.assertIn(ultimo['concurso'], [c['concurso'] for c in datos['ultimas_coincidencias']])

    def test_generacion_por_modalidad_y_estrategia(self):
        for modo, cfg in MODALIDADES.items():
            for estrategia in ('frecuencia', 'equilibrada'):
                with self.subTest(modalidad=modo, estrategia=estrategia):
                    datos = self.consultar(f"/modalidades/{modo}/predicciones", {'cantidad': 3, 'ventana': 100, 'estrategia': estrategia})
                    self.assertEqual(datos['modalidad'], modo)
                    self.assertEqual(datos['estrategia'], estrategia)
                    self.assertEqual(datos['sorteos_analizados'], 100)
                    self.assertEqual(len(datos['combinaciones']), 3)
                    self.assertEqual(len({tuple(ns) for ns in datos['combinaciones']}), 3)
                    for ns in datos['combinaciones']:
                        self.assertEqual(len(ns), len(cfg.columnas))
                        self.assertEqual(len(set(ns)), len(ns))
                        self.assertEqual(ns, sorted(ns))
                        self.assertTrue(all(1 <= n <= cfg.maximo for n in ns))

    def test_parametros_invalidos(self):
        self.consultar('/modalidades/desconocida/resumen', estado=404)
        for numeros in ('1,2,3,4,29', '1,2,3,4,4', '1,2', 'a,2,3,4,5'):
            self.consultar('/modalidades/chispazo/verificar', {'numeros': numeros}, estado=422)
        self.consultar('/modalidades/melate/predicciones', {'estrategia': 'inexistente'}, estado=422)
        self.consultar('/modalidades/melate/predicciones', {'cantidad': 6}, estado=422)
        self.consultar('/modalidades/melate/historial', {'pagina': 0}, estado=422)


if __name__ == '__main__':
    unittest.main()
