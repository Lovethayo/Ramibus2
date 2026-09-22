import { useEffect, useState } from 'react'
import { Activity, ArrowUpRight, Cloud, Globe2, Radio, RefreshCw, Satellite, ShieldAlert, Waves, X } from 'lucide-react'
import WorldGlobe from './WorldGlobe'

const sources = [
  { id: 'usgs', name: 'USGS EARTHQUAKES', type: 'earthquake', kind: 'KEYLESS', href: 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php', Icon: Waves },
  { id: 'eonet', name: 'NASA EONET', type: 'natural events', kind: 'KEYLESS', href: 'https://eonet.gsfc.nasa.gov/', Icon: Globe2 },
  { id: 'weather', name: 'OPEN-METEO', type: 'weather', kind: 'KEYLESS', href: 'https://open-meteo.com/', Icon: Cloud },
  { id: 'satellites', name: 'CELESTRAK', type: 'satellites', kind: 'KEYLESS', href: 'https://celestrak.org/', Icon: Satellite },
  { id: 'news', name: 'GDELT / RSS', type: 'news', kind: 'KEYLESS', href: 'https://www.gdeltproject.org/', Icon: Radio },
  { id: 'cctv', name: 'AUTHORIZED CCTV', type: 'public cameras', kind: 'ADAPTER GATED', href: 'https://github.com/carbon-evolution/osiris/blob/main/CONTRIBUTING.md', Icon: Activity },
  { id: 'osiris', name: 'OSIRIS ADAPTER FABRIC', type: 'CCTV + OSINT + live feeds', kind: 'RAMIBOT GATEWAY', href: '#osiris-capabilities', Icon: ShieldAlert },
]

function WorldPanel({ onClose }) {
  const [health, setHealth] = useState(null)
  const [events, setEvents] = useState([])
  const [cameras, setCameras] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('WORLD GATEWAY NOT CONNECTED')

  const refresh = async () => {
    setLoading(true)
    setMessage('')
    try {
      const [healthResponse, eventsResponse] = await Promise.all([
        fetch('/api/world/source-health'),
        fetch('/api/world/recent?limit=12'),
      ])
      if (!healthResponse.ok || !eventsResponse.ok) throw new Error('World gateway is unavailable')
      setHealth(await healthResponse.json())
      setEvents(await eventsResponse.json())
      const cameraResponse = await fetch('/api/world/cctv?limit=18')
      if (cameraResponse.ok) {
        setCameras(await cameraResponse.json())
        const refreshedHealth = await fetch('/api/world/source-health')
        if (refreshedHealth.ok) setHealth(await refreshedHealth.json())
      }
    } catch (error) {
      setHealth(null)
      setEvents([])
      setMessage(error.message || 'World gateway is unavailable')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])

  const sourceState = (id) => {
    const item = Array.isArray(health) ? health.find((entry) => entry.id === id || entry.source_id === id) : null
    return item?.status || 'GATEWAY OFFLINE'
  }

  return (
    <section className="world-panel" aria-label="World Intelligence">
      <header className="world-header">
        <div>
          <div className="world-kicker"><span className="status-dot" /> WORLD INTELLIGENCE / UNTRUSTED EVIDENCE</div>
          <h2>LIVE DATA FABRIC</h2>
          <p>Keyless-first sources routed through the existing RamiBot gateway. Nothing from a feed is executable.</p>
        </div>
        <div className="world-actions">
          <button className="world-button" onClick={refresh} disabled={loading}><RefreshCw size={13} className={loading ? 'spin' : ''} /> {loading ? 'CHECKING' : 'REFRESH'}</button>
          <button className="icon-button" onClick={onClose} aria-label="Close World Intelligence"><X size={16} /></button>
        </div>
      </header>

      <div className="world-summary">
        <div><span>EVENT PIPELINE</span><strong>{events.length ? `${events.length} CACHED` : 'NO CACHED EVENTS'}</strong></div>
        <div><span>PUBLIC CCTV</span><strong>{cameras.length ? `${cameras.length} INDEXED` : 'NOT LOADED'}</strong></div>
        <div><span>OSIRIS ADAPTERS</span><strong>{sourceState('osiris') === 'GATEWAY OFFLINE' ? 'NOT CONNECTED' : sourceState('osiris')}</strong></div>
        <div><span>TRUST BOUNDARY</span><strong>UNTRUSTED</strong></div>
      </div>

      {message && (
        <div className="world-notice"><ShieldAlert size={14} /> {message}. The panel will not invent live results or bypass source controls.</div>
      )}

      <div className="world-grid">
        {sources.map(({ id, name, type, kind, href, Icon }) => {
          const state = sourceState(id)
          const isOnline = /online|healthy|ok/i.test(state)
          return (
            <article className="source-card" key={id}>
              <div className="source-card-top"><Icon size={15} /><span className={`source-state ${isOnline ? 'online' : ''}`}><i /> {state}</span></div>
              <strong>{name}</strong>
              <span>{type} · {kind}</span>
              <a href={href} target="_blank" rel="noreferrer">OFFICIAL SOURCE <ArrowUpRight size={11} /></a>
            </article>
          )
        })}
      </div>

      <WorldGlobe cameras={cameras} loading={loading} onRefresh={refresh} />

      <section className="cctv-section" aria-label="Public live CCTV">
        <div className="cctv-heading">
          <div><span className="world-kicker"><span className="status-dot" /> PUBLIC CAMERA INDEX</span><h3>LIVE CCTV SNAPSHOTS</h3></div>
          <span>REFRESHING PUBLIC SOURCES · NOT PRIVATE CAMERAS</span>
        </div>
        {cameras.length ? (
          <div className="camera-grid">
            {cameras.map((camera) => (
              <article className="camera-card" key={camera.id}>
                <a href={camera.feed_url || camera.external_url} target="_blank" rel="noreferrer" className="camera-image-link">
                  {camera.feed_url ? <img src={camera.feed_url} alt={camera.name} loading="lazy" /> : <div className="camera-placeholder">EXTERNAL LIVE FEED</div>}
                </a>
                <div className="camera-meta"><strong>{camera.name}</strong><span>{camera.city} · {camera.source}</span></div>
                <a className="camera-open" href={camera.external_url || camera.source_url} target="_blank" rel="noreferrer">OPEN SOURCE FEED <ArrowUpRight size={10} /></a>
              </article>
            ))}
          </div>
        ) : (
          <div className="world-notice"><ShieldAlert size={14} /> No public camera index is currently cached. Refresh to retry the authorized source adapters.</div>
        )}
      </section>

      <div className="world-footer" id="osiris-capabilities"><span>WORLD + OSIRIS TOOLS</span><code>world_search · cctv_search · osiris_capabilities · osiris_source_health · osiris_query</code><span className="world-footer-note">Feed content remains untrusted evidence. Sensitive tools stay approval-gated.</span></div>
    </section>
  )
}

export default WorldPanel