import { useEffect, useState } from 'react';
import { catalogoLocal } from './competencias';

const apiBase = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

async function consultar(path) {
  const response = await fetch(`${apiBase}/api/v1/${path}`, { signal: AbortSignal.timeout(12000) });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

const CircleIcon = ({ size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.7" />
    <circle cx="12" cy="12" r="2.5" fill="currentColor" />
  </svg>
);

function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark" aria-hidden="true">L<span>×</span></span>
      <div className="brand-wordmark">
        <strong>Loto<span>X</span></strong>
        <small>LOTTERY ANALYTICS</small>
      </div>
    </div>
  );
}

function NumeroBola({ numero, extra = false }) {
  return <span className={extra ? 'resultado-bola extra' : 'resultado-bola'}>{String(numero).padStart(2, '0')}</span>;
}

function FilaNumeros({ numeros = [], adicional = null }) {
  return <div className="fila-numeros">{numeros.map(n => <NumeroBola key={n} numero={n} />)}{adicional != null && <NumeroBola extra numero={adicional} />}</div>;
}

function App() {
  const [catalogo, setCatalogo] = useState(catalogoLocal);
  const [apiEstado, setApiEstado] = useState('verificando');
  const [vista, setVista] = useState('inicio');
  const [seleccion, setSeleccion] = useState(null);
  const [modalidad, setModalidad] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [frecuencia, setFrecuencia] = useState(null);
  const [estadoDatos, setEstadoDatos] = useState('pendiente');
  const [errorDatos, setErrorDatos] = useState('');
  const [ventana, setVentana] = useState(500);
  const [estrategia, setEstrategia] = useState('equilibrada');
  const [combinaciones, setCombinaciones] = useState([]);
  const [generando, setGenerando] = useState(false);
  const [predError, setPredError] = useState('');
  const [numerosConsulta, setNumerosConsulta] = useState('');
  const [verificacion, setVerificacion] = useState(null);
  const [verificando, setVerificando] = useState(false);

  useEffect(() => {
    if (vista !== 'detalle' || !modalidad) return;
    let activo = true;
    setEstadoDatos('cargando');
    setErrorDatos('');
    setCombinaciones([]);
    setVerificacion(null);
    Promise.all([
      consultar(`modalidades/${modalidad}/resumen`),
      consultar(`modalidades/${modalidad}/historial?limite=8`),
      consultar(`modalidades/${modalidad}/frecuencias?ventana=${ventana}`),
    ]).then(([res, his, fre]) => {
      if (!activo) return;
      setResumen(res);
      setHistorial(his.data || []);
      setFrecuencia(fre);
      setEstadoDatos('listo');
    }).catch((error) => {
      if (!activo) return;
      setEstadoDatos('error');
      setErrorDatos(error.message || 'No se pudieron leer los datos de PostgreSQL.');
      setResumen(null);
      setHistorial([]);
      setFrecuencia(null);
    });
    return () => { activo = false; };
  }, [vista, modalidad, ventana]);

  const generar = async () => {
    setGenerando(true);
    setPredError('');
    setCombinaciones([]);
    try {
      const result = await consultar(`modalidades/${modalidad}/predicciones?cantidad=3&ventana=${ventana}&estrategia=${estrategia}`);
      setCombinaciones(result.combinaciones || []);
    } catch (error) {
      setPredError(`No fue posible generar combinaciones: ${error.message}`);
    } finally {
      setGenerando(false);
    }
  };

  const verificar = async (e) => {
    e.preventDefault();
    setVerificando(true);
    setVerificacion(null);
    try {
      const result = await consultar(`modalidades/${modalidad}/verificar?numeros=${encodeURIComponent(numerosConsulta)}`);
      setVerificacion({ ...result, valido: true });
    } catch (error) {
      setVerificacion({ valido: false, mensaje: `Revisa la combinación. ${error.message}` });
    } finally {
      setVerificando(false);
    }
  };

  useEffect(() => {
    let activo = true;
    Promise.all([consultar('health'), consultar('competencias')])
      .then(([salud, datos]) => {
        if (!activo) return;
        if (salud.status !== 'ok' || !Array.isArray(datos.data)) throw new Error('Respuesta inválida');
        setCatalogo(datos.data);
        setApiEstado('conectada');
      })
      .catch(() => {
        if (activo) setApiEstado('sin-conexion');
      });
    return () => { activo = false; };
  }, []);

  const entrar = (competencia) => {
    setSeleccion(competencia.id);
    setModalidad(competencia.modalidades[0].id);
    setNumerosConsulta('');
    setVista('detalle');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const volver = () => {
    setVista('inicio');
    setSeleccion(null);
    setModalidad(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const competenciaActual = catalogo.find((item) => item.id === seleccion);
  const modalidadActual = competenciaActual?.modalidades.find((item) => item.id === modalidad);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Brand />
        <div className="sidebar-section-title">PLATAFORMA</div>
        <nav aria-label="Navegación principal" className="side-nav">
          <button type="button" className={vista === 'inicio' ? 'nav-item active' : 'nav-item'} onClick={volver}>
            <span className="nav-ico">⌂</span> Inicio
          </button>
          <span className="nav-group-label">COMPETENCIAS</span>
          {catalogo.map((item) => (
            <button key={item.id} type="button" className={seleccion === item.id && vista === 'detalle' ? 'nav-item active' : 'nav-item'} onClick={() => entrar(item)}>
              <span className="nav-ico"><CircleIcon size={17} /></span> {item.nombre}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="feature-tag"><span className="tag-dot" /> MOTOR INICIAL · V0.3</span>
          <p>Datos históricos y combinaciones heurísticas.</p>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div className="mobile-brand"><Brand /></div>
          <div className="breadcrumb"><span>PLATAFORMA</span><span className="separator">/</span><strong>{vista === 'inicio' ? 'Inicio' : competenciaActual?.nombre}</strong></div>
          <div className="topbar-right">
            <span className={`status-pill ${apiEstado}`}><span className="status-dot" />{apiEstado === 'conectada' ? 'API conectada' : apiEstado === 'verificando' ? 'Verificando API' : 'API sin conexión'}</span>
            <div className="avatar">LX</div>
          </div>
        </header>

        <main className="content">
          {vista === 'inicio' ? (
            <>
              <div className="intro">
                <div><span className="eyebrow">BIENVENIDO A LOTOX</span><h1>Analiza resultados.<br /><span>Explora combinaciones.</span></h1></div>
                <div className="intro-caption">LotoX consulta PostgreSQL para analizar sorteos y generar combinaciones basadas en estadísticas históricas.</div>
              </div>

              <section className="hero-card">
                <div className="hero-copy">
                  <span className="hero-kicker"><span className="pulse-dot" /> LOTTERY INTELLIGENCE PLATFORM</span>
                  <h2>Los números cuentan<br /><em>una historia.</em></h2>
                  <p>Explora frecuencias, historial y combinaciones generadas con estrategias estadísticas implementadas en Python.</p>
                  <button type="button" className="primary-button" onClick={() => document.getElementById('competencias')?.scrollIntoView({ behavior: 'smooth' })}>Explorar competencias <span>↗</span></button>
                </div>
                <div className="hero-visual" aria-hidden="true">
                  <span className="orbit orbit-one" /><span className="orbit orbit-two" />
                  <span className="number-ball nb-one">08</span><span className="number-ball nb-two">17</span><span className="number-ball nb-three">26</span><span className="number-ball nb-four">41</span>
                  <span className="visual-label">VISUALIZACIÓN CONCEPTUAL</span>
                </div>
              </section>

              <div className="section-heading" id="competencias">
                <div><span className="eyebrow">EXPLORA EL UNIVERSO</span><h2>Competencias disponibles</h2><p>Selecciona una competencia para explorar sus modalidades y herramientas.</p></div>
                <span className="counter">02 COMPETENCIAS</span>
              </div>

              <div className="competition-grid">
                {catalogo.map((item) => (
                  <button type="button" key={item.id} className={`competition-card ${item.id}`} onClick={() => entrar(item)}>
                    <div className="competition-top"><div className="competition-symbol">{item.id === 'chispazo' ? '✺' : '✦'}</div><span className="card-arrow">↗</span></div>
                    <div className="competition-body"><div className="card-category">{item.id === 'chispazo' ? 'SORTEO INDEPENDIENTE' : 'UNIVERSO MELATE'}</div><h3>{item.nombre}</h3><p>{item.descripcion}</p></div>
                    <div className="competition-footer"><span>{item.numeros_por_sorteo} números · {item.numero_minimo}–{item.numero_maximo}</span><span>{item.modalidades.length} {item.modalidades.length === 1 ? 'modalidad' : 'modalidades'}</span></div>
                  </button>
                ))}
              </div>

              <div className="info-banner"><span className="info-icon">i</span><p><strong>Estadística ≠ ventaja matemática.</strong> Las combinaciones sugeridas son experimentos heurísticos; en sorteos justos ninguna combinación es más probable que otra.</p></div>
            </>
          ) : (
            <>
              <button type="button" className="back-button" onClick={volver}>← Todas las competencias</button>
              <section className={`detail-hero ${seleccion}`}>
                <div className="detail-icon">{seleccion === 'chispazo' ? '✺' : '✦'}</div>
                <div><span className="eyebrow">EXPLORADOR DE COMPETENCIAS</span><h1>{competenciaActual?.nombre}</h1><p>{competenciaActual?.descripcion}</p></div>
              </section>
              <div className="section-heading section-heading-small"><div><span className="eyebrow">SELECCIONA EL SORTEO</span><h2>Modalidades</h2></div></div>
              <div className="mode-tabs" role="tablist" aria-label="Modalidades">
                {competenciaActual?.modalidades.map((item) => (
                  <button key={item.id} type="button" role="tab" aria-selected={modalidad === item.id} className={modalidad === item.id ? 'mode-tab selected' : 'mode-tab'} onClick={() => { setModalidad(item.id); setNumerosConsulta(''); }}>{item.nombre}</button>
                ))}
              </div>
              <div className="detail-summary">
                <div className="summary-item"><span>MODALIDAD</span><strong>{modalidadActual?.nombre}</strong></div>
                <div className="summary-item"><span>NÚMEROS POR SORTEO</span><strong>{modalidadActual?.numeros_por_sorteo}</strong></div>
                <div className="summary-item"><span>RANGO DE NÚMEROS</span><strong>{modalidadActual?.numero_minimo} – {modalidadActual?.numero_maximo}</strong></div>
                <div className="summary-item"><span>REGISTROS EN POSTGRES</span><strong>{estadoDatos === 'listo' ? resumen?.registros?.toLocaleString('es-MX') : '—'}</strong><small>{estadoDatos === 'listo' ? `Hasta ${resumen?.hasta}` : estadoDatos === 'cargando' ? 'Consultando PostgreSQL…' : 'Sin datos conectados'}</small></div>
              </div>
              {estadoDatos === 'error' && <div className="data-alert"><strong>No fue posible consultar PostgreSQL.</strong> {errorDatos}. Verifica que DATABASE_URL esté configurada, las tablas existan y FastAPI esté en ejecución.</div>}
              {estadoDatos === 'cargando' && <p className="data-loading">Consultando resultados históricos…</p>}
              {estadoDatos === 'listo' && <>
                <section className="lotox-panel latest-draw">
                  <div className="panel-heading"><div><span className="eyebrow">DATOS HISTÓRICOS</span><h2>Último sorteo registrado</h2></div><span className="meta-chip">Concurso #{resumen?.ultimo?.concurso || '—'}</span></div>
                  {resumen?.ultimo ? <><FilaNumeros numeros={resumen.ultimo.numeros} adicional={resumen.ultimo.adicional} /><p className="muted-note">Fecha: {resumen.ultimo.fecha} · Fuente: PostgreSQL {resumen.ultimo.adicional != null ? '· Bola gris: adicional (R7)' : ''}</p></> : <p>No hay registros para esta modalidad.</p>}
                </section>

                <section className="lotox-panel">
                  <div className="panel-heading"><div><span className="eyebrow">MOTOR LOTOX · VERSIÓN INICIAL</span><h2>Generador de combinaciones</h2></div><span className="meta-chip">Experimental</span></div>
                  <p className="panel-description">Genera tres combinaciones usando una muestra ponderada de números según sus apariciones históricas. No son resultados garantizados ni predicciones con ventaja matemática.</p>
                  <div className="controls-line">
                    <label className="field-label">Estrategia
                      <select value={estrategia} onChange={e => { setEstrategia(e.target.value); setCombinaciones([]); }}>
                        <option value="equilibrada">Equilibrada (frecuencia + uniformidad)</option>
                        <option value="frecuencia">Frecuencia histórica</option>
                      </select>
                    </label>
                    <label className="field-label">Ventana de análisis
                      <select value={ventana} onChange={e => setVentana(Number(e.target.value))}>
                        <option value={100}>Últimos 100 sorteos</option>
                        <option value={500}>Últimos 500 sorteos</option>
                        <option value={1000}>Últimos 1000 sorteos</option>
                        <option value={0}>Todo el historial</option>
                      </select>
                    </label>
                    <button type="button" className="primary-button action-generate" disabled={!frecuencia?.sorteos_analizados || generando} onClick={generar}>{generando ? 'Generando…' : '✦ Generar combinaciones'}</button>
                  </div>
                  {predError && <p className="error-note">{predError}</p>}
                  {combinaciones.length > 0 && <div className="prediction-list">{combinaciones.map((nums, idx) => <div className="prediction-row" key={idx}><span className="prediction-label">PROPUESTA {idx + 1}</span><FilaNumeros numeros={nums} /></div>)}</div>}
                  <p className="muted-note">Las frecuencias pasadas no cambian la probabilidad de cada combinación en un sorteo justo.</p>
                </section>

                <div className="data-grid">
                  <section className="lotox-panel">
                    <div className="panel-heading"><div><span className="eyebrow">ANÁLISIS HISTÓRICO</span><h2>Números más frecuentes</h2></div></div>
                    <p className="muted-note">{frecuencia?.sorteos_analizados?.toLocaleString('es-MX')} sorteos analizados (números principales).</p>
                    <div className="frequency-list">
                      {frecuencia?.ranking?.slice(0, 10).map((item, i) => <div className="frequency-row" key={item.numero}>
                        <span className="frequency-index">{String(i + 1).padStart(2, '0')}</span><NumeroBola numero={item.numero} /><div className="frequency-track"><span style={{ width: `${(item.apariciones / (frecuencia.ranking[0]?.apariciones || 1)) * 100}%` }} /></div><strong>{item.apariciones}</strong>
                      </div>)}
                    </div>
                  </section>
                  <section className="lotox-panel">
                    <div className="panel-heading"><div><span className="eyebrow">EXPLORADOR</span><h2>Últimos sorteos</h2></div></div>
                    <div className="draw-list">{historial.map(sorteo => <div className="draw-row" key={sorteo.concurso}><div className="draw-info"><strong>#{sorteo.concurso}</strong><small>{sorteo.fecha}</small></div><FilaNumeros numeros={sorteo.numeros} adicional={sorteo.adicional} /></div>)}</div>
                  </section>
                </div>
                <section className="lotox-panel">
                  <div className="panel-heading"><div><span className="eyebrow">EXPLORADOR DE COMBINACIONES</span><h2>Buscar en el historial</h2></div></div>
                  <p className="panel-description">Introduce {modalidadActual?.numeros_por_sorteo} números separados por comas para comprobar si aparecieron juntos en algún sorteo.</p>
                  <form className="verify-form" onSubmit={verificar}><input aria-label="Números separados por coma" type="text" required placeholder={modalidad === 'chispazo' ? 'Ejemplo: 1, 5, 9, 17, 22' : 'Ejemplo: 1, 5, 9, 17, 22, 45'} value={numerosConsulta} onChange={e => setNumerosConsulta(e.target.value)} /><button type="submit" className="secondary-button" disabled={verificando}>{verificando ? 'Consultando…' : 'Verificar'}</button></form>
                  {verificacion && <p className={verificacion.valido ? 'result-note' : 'error-note'}>{verificacion.valido ? `Esta combinación aparece ${verificacion.apariciones_historicas} veces en el historial cargado.` : verificacion.mensaje}</p>}
                </section>
                <div className="info-banner"><span className="info-icon">i</span><p><strong>Datos reales de tu PostgreSQL.</strong> Los resultados se limitan a las fechas cargadas en tus tablas. La comprobación de combinaciones y las estadísticas no permiten conocer el próximo sorteo.</p></div>
              </>}
            </>
          )}
          <footer className="footer"><span>© LotoX · Plataforma de análisis estadístico</span><span>Los resultados anteriores no predicen sorteos futuros.</span></footer>
        </main>
      </div>
    </div>
  );
}

export default App;
