import { test } from 'node:test';
import assert from 'node:assert/strict';
import { consultar, crearSolicitudVigente } from './api.js';

test('consulta devuelve datos y conserva el endpoint solicitado', async t => {
  t.mock.method(globalThis, 'fetch', async (url) => {
    assert.equal(url, '/api/v1/modalidades/chispazo/resumen');
    return Response.json({ modalidad: 'chispazo', registros: 12 });
  });
  assert.deepEqual(await consultar('modalidades/chispazo/resumen'), { modalidad: 'chispazo', registros: 12 });
});

test('muestra el detalle de validación y de indisponibilidad de la API', async t => {
  for (const [status, detail] of [[422, 'Se necesitan 5 números distintos.'], [503, 'No se pudo consultar PostgreSQL.']]) {
    const mock = t.mock.method(globalThis, 'fetch', async () => Response.json({ detail }, { status }));
    await assert.rejects(consultar('modalidades/chispazo/verificar'), { message: detail });
    mock.mock.restore();
  }
});

test('errores de parámetros no exponen el valor de entrada y errores HTML usan el estado HTTP', async t => {
  const mock = t.mock.method(globalThis, 'fetch', async () => Response.json({ detail: [{ msg: 'Debe ser un entero.', input: 'entrada privada' }] }, { status: 422 }));
  await assert.rejects(consultar('modalidades/chispazo/predicciones'), { message: 'Debe ser un entero.' });
  mock.mock.restore();
  t.mock.method(globalThis, 'fetch', async () => new Response('<html>Error</html>', { status: 502 }));
  await assert.rejects(consultar('health'), { message: 'HTTP 502' });
});

test('una respuesta tardía no reemplaza resultados del contexto nuevo aunque la red ignore abort', async t => {
  const pendientes = [];
  t.mock.method(globalThis, 'fetch', (_url, opciones) => new Promise(resolve => pendientes.push({ resolve, signal: opciones.signal })));
  const control = crearSolicitudVigente();
  let visible;
  const ejecutar = async modo => {
    const solicitud = control.iniciar();
    const resultado = await consultar(`modalidades/${modo}/predicciones`, { signal: solicitud.signal });
    if (solicitud.vigente()) visible = resultado;
  };
  const anterior = ejecutar('chispazo');
  control.cancelar();
  assert.equal(pendientes[0].signal.aborted, true);
  const nueva = ejecutar('melate');
  pendientes[1].resolve(Response.json({ modalidad: 'melate', combinaciones: [[1, 2, 3, 4, 5, 6]] }));
  await nueva;
  pendientes[0].resolve(Response.json({ modalidad: 'chispazo', combinaciones: [[1, 2, 3, 4, 5]] }));
  await anterior;
  assert.equal(visible.modalidad, 'melate');
});

test('cancelar invalida resultados y errores pendientes; una solicitud nueva sigue vigente', () => {
  const control = crearSolicitudVigente();
  const anterior = control.iniciar();
  control.cancelar();
  assert.equal(anterior.vigente(), false);
  const nueva = control.iniciar();
  assert.equal(nueva.vigente(), true);
  assert.equal(nueva.signal.aborted, false);
});
