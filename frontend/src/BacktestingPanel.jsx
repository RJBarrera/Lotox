import { useEffect, useRef, useState } from 'react';
import { consultar, crearSolicitudVigente } from './api';

const nombres = { clasica: 'Método original', frecuencia: 'Frecuencia', equilibrada: 'Equilibrada' };
const decimal = valor => valor.toLocaleString('es-MX', { maximumFractionDigits: 3 });

export default function BacktestingPanel({ modalidad }) {
  const [sorteos, setSorteos] = useState(100);
  const [ventana, setVentana] = useState(500);
  const [semilla, setSemilla] = useState('42');
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState('');
  const [indice, setIndice] = useState(0);
  const solicitud = useRef(null);
  if (!solicitud.current) solicitud.current = crearSolicitudVigente();
  useEffect(() => () => solicitud.current.cancelar(), []);

  const limpiar = () => {
    solicitud.current.cancelar();
    setResultado(null);
    setCargando(false);
    setError('');
    setIndice(0);
  };
  const ejecutar = async event => {
    event.preventDefault();
    const actual = solicitud.current.iniciar();
    setCargando(true);
    setResultado(null);
    setError('');
    setIndice(0);
    try {
      const params = new URLSearchParams({ sorteos, ventana, semilla, cantidad: 3, entrenamiento_minimo: 100, repeticiones: 30 });
      const datos = await consultar(`modalidades/${modalidad}/backtesting?${params}`, { signal: actual.signal });
      if (actual.vigente()) setResultado(datos);
    } catch (err) {
      if (actual.vigente()) setError(err.message);
    } finally {
      if (actual.vigente()) setCargando(false);
    }
  };
  const detalle = resultado?.detalle[indice];
  const azar = resultado?.referencia_uniforme;
  return (
    <section className="lotox-panel" aria-labelledby="backtesting-title" aria-busy={cargando}>
      <div className="panel-heading"><div><span className="eyebrow">EVALUACIÓN HISTÓRICA</span><h2 id="backtesting-title">Backtesting del motor</h2></div><span className="meta-chip">Fuera de muestra</span></div>
      <p className="panel-description">Simula las tres estrategias antes de cada sorteo, usando solo resultados anteriores. Cada una propone tres combinaciones por sorteo. La referencia usa 30 simulaciones aleatorias uniformes con el mismo número de combinaciones.</p>
      <form className="controls-line" onSubmit={ejecutar}>
        <label className="field-label">Sorteos a evaluar
          <select value={sorteos} onChange={e => { limpiar(); setSorteos(Number(e.target.value)); }}>
            {[50, 100, 250, 500].map(n => <option key={n} value={n}>Últimos {n}</option>)}
          </select>
        </label>
        <label className="field-label">Historial anterior por sorteo
          <select value={ventana} onChange={e => { limpiar(); setVentana(Number(e.target.value)); }}>
            {[100, 500, 1000].map(n => <option key={n} value={n}>Hasta {n} anteriores</option>)}
            <option value={0}>Todo el historial anterior</option>
          </select>
        </label>
        <label className="field-label">Semilla reproducible
          <input className="backtest-seed" type="number" min="0" max="4294967295" step="1" required value={semilla} onChange={e => { limpiar(); setSemilla(e.target.value); }} />
        </label>
        <button className="primary-button action-generate" type="submit" disabled={cargando}>{cargando ? 'Evaluando sorteos…' : 'Ejecutar backtesting'}</button>
      </form>
      <p className="muted-note">Se requieren al menos 100 sorteos de entrenamiento antes del primero evaluado. Los aciertos cuentan números principales; Melate excluye R7.</p>
      {cargando && <p className="data-loading" role="status">Reconstruyendo propuestas y comparándolas con los resultados históricos…</p>}
      {error && <p className="error-note" role="alert">No fue posible completar el backtesting: {error}</p>}
      {resultado && <>
        <p className="result-note" role="status">{resultado.parametros.sorteos} sorteos evaluados · {resultado.periodo.desde} a {resultado.periodo.hasta} · {azar.combinaciones_por_replica} combinaciones por estrategia · Semilla {resultado.parametros.semilla}</p>
        <div className="backtest-table-wrap">
          <table className="backtest-table">
            <caption>Aciertos observados, no probabilidades de ganar</caption>
            <thead><tr><th scope="col">Estrategia</th><th scope="col">Media por combinación</th><th scope="col">Media del mejor resultado por sorteo</th><th scope="col">Diferencia frente al azar</th></tr></thead>
            <tbody>
              {resultado.resultados.map(r => <tr key={r.estrategia}><th scope="row">{nombres[r.estrategia]}</th><td>{decimal(r.media_aciertos)}</td><td>{decimal(r.media_mejor_por_sorteo)}</td><td>{r.diferencia_media_vs_uniforme > 0 ? '+' : ''}{decimal(r.diferencia_media_vs_uniforme)}</td></tr>)}
              <tr><th scope="row">Aleatoria uniforme (media de 30 simulaciones)</th><td>{decimal(azar.media_aciertos)}</td><td>{decimal(azar.media_mejor_por_sorteo)}</td><td>Referencia</td></tr>
            </tbody>
          </table>
        </div>
        <p className="muted-note">Medias aleatorias observadas: {decimal(azar.min_media)} a {decimal(azar.max_media)} aciertos por combinación; desviación entre simulaciones: {decimal(azar.desviacion_medias)}. Este rango no es un intervalo de confianza.</p>
        <div className="backtest-table-wrap">
          <table className="backtest-table">
            <caption>Cantidad de combinaciones por número de aciertos</caption>
            <thead><tr><th scope="col">Estrategia</th>{azar.distribucion_aciertos_media.map((_, n) => <th scope="col" key={n}>{n} aciertos</th>)}</tr></thead>
            <tbody>
              {resultado.resultados.map(r => <tr key={r.estrategia}><th scope="row">{nombres[r.estrategia]}</th>{r.distribucion_aciertos.map((n, i) => <td key={i}>{n}</td>)}</tr>)}
              <tr><th scope="row">Aleatoria (promedio por simulación)</th>{azar.distribucion_aciertos_media.map((n, i) => <td key={i}>{decimal(n)}</td>)}</tr>
            </tbody>
          </table>
        </div>
        <details className="backtest-detail">
          <summary>Revisar propuestas y aciertos por sorteo</summary>
          <label className="field-label">Sorteo evaluado
            <select value={indice} onChange={e => setIndice(Number(e.target.value))}>
              {resultado.detalle.map((d, i) => <option key={d.concurso} value={i}>#{d.concurso} · {d.fecha}</option>)}
            </select>
          </label>
          <p className="muted-note">Resultado real: {detalle.numeros.join(', ')}. Entrenamiento: {detalle.entrenamiento.sorteos} sorteos, hasta #{detalle.entrenamiento.ultimo_concurso} del {detalle.entrenamiento.hasta}.</p>
          {Object.entries({ ...detalle.estrategias, uniforme: detalle.uniforme_replica_1 }).map(([nombre, datos]) => <div key={nombre}>
            <h3>{nombres[nombre] || 'Aleatoria uniforme · simulación 1 de 30'}</h3>
            {datos.combinaciones.map((nums, i) => <p className="prediction-row" key={i}><span>{nums.map(n => String(n).padStart(2, '0')).join(' · ')}</span><strong>{datos.aciertos[i]} aciertos</strong></p>)}
          </div>)}
        </details>
        <details className="backtest-detail"><summary>Metodología y límites</summary>
          {resultado.advertencias.map(texto => <p className="muted-note" key={texto}>{texto}</p>)}
        </details>
        <p className="muted-note">Una diferencia positiva en esta muestra no demuestra ventaja predictiva. Cambiar los parámetros después de ver los resultados exige otra evaluación con datos no utilizados.</p>
      </>}
    </section>
  );
}
