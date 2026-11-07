const apiBase = (import.meta.env?.VITE_API_URL || '').replace(/\/$/, '');

export async function consultar(path, { signal } = {}) {
  const timeout = AbortSignal.timeout(12000);
  const response = await fetch(`${apiBase}/api/v1/${path}`, {
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    const mensaje = typeof detail === 'string' ? detail
      : Array.isArray(detail) ? detail.map(item => item.msg).filter(Boolean).join(' ')
        : '';
    throw new Error(mensaje || `HTTP ${response.status}`);
  }
  return response.json();
}

// Cancelar la red no basta: una respuesta ya resuelta también puede llegar tarde.
export function crearSolicitudVigente() {
  let actual = null;
  return {
    cancelar() {
      actual?.abort();
      actual = null;
    },
    iniciar() {
      this.cancelar();
      const controlador = new AbortController();
      actual = controlador;
      return {
        signal: controlador.signal,
        vigente: () => actual === controlador && !controlador.signal.aborted,
      };
    },
  };
}
