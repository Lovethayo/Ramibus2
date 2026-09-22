import { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { LocateFixed, Search, ZoomIn, ZoomOut } from 'lucide-react'

const mapStyle = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [
    { id: 'background', type: 'background', paint: { 'background-color': '#05070b' } },
    { id: 'osm', type: 'raster', source: 'osm', paint: { 'raster-opacity': 0.7, 'raster-saturation': -0.75, 'raster-contrast': 0.2 } },
  ],
}

function cameraFeature(camera) {
  const latitude = Number(camera.latitude ?? camera.lat)
  const longitude = Number(camera.longitude ?? camera.lng)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null
  return {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [longitude, latitude] },
    properties: {
      id: camera.id,
      name: camera.name || 'PUBLIC CAMERA',
      city: camera.city || '',
      country: camera.country || '',
      source: camera.source || 'AUTHORIZED SOURCE',
      external_url: camera.external_url || camera.source_url || '',
      feed_url: camera.feed_url || '',
    },
  }
}

function WorldGlobe({ cameras, loading, onRefresh }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const [query, setQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [searchMessage, setSearchMessage] = useState('')
  const features = useMemo(() => cameras.map(cameraFeature).filter(Boolean), [cameras])

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return undefined
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: mapStyle,
      center: [8, 24],
      zoom: 1.45,
      minZoom: 1,
      maxZoom: 16,
      renderWorldCopies: true,
    })
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'bottom-right')
    map.on('load', () => {
      map.addSource('public-cameras', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: 'public-camera-halo',
        type: 'circle',
        source: 'public-cameras',
        paint: {
          'circle-radius': 8,
          'circle-color': '#00e5ff',
          'circle-opacity': 0.18,
          'circle-blur': 0.8,
        },
      })
      map.addLayer({
        id: 'public-camera-points',
        type: 'circle',
        source: 'public-cameras',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 1, 3, 7, 5, 13, 8],
          'circle-color': '#00e5ff',
          'circle-stroke-color': '#051017',
          'circle-stroke-width': 1,
        },
      })
      map.on('click', 'public-camera-points', (event) => {
        const feature = event.features?.[0]
        if (!feature) return
        const properties = feature.properties || {}
        const sourceUrl = properties.external_url || properties.feed_url
        new maplibregl.Popup({ closeButton: true, maxWidth: '270px' })
          .setLngLat(feature.geometry.coordinates)
          .setHTML(
            `<strong>${escapeHtml(properties.name)}</strong>` +
            `<br><span>${escapeHtml([properties.city, properties.country].filter(Boolean).join(' · '))}</span>` +
            `<br><small>${escapeHtml(properties.source)}</small>` +
            (sourceUrl ? `<br><a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">OPEN PUBLIC SOURCE</a>` : ''),
          )
          .addTo(map)
      })
      map.on('mouseenter', 'public-camera-points', () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', 'public-camera-points', () => { map.getCanvas().style.cursor = '' })
    })
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    const source = map?.getSource('public-cameras')
    if (source) source.setData({ type: 'FeatureCollection', features })
  }, [features])

  const locate = () => mapRef.current?.flyTo({ center: [8, 24], zoom: 1.45, duration: 900 })

  const searchPlace = async (event) => {
    event.preventDefault()
    const value = query.trim()
    if (!value) return
    setSearching(true)
    setSearchMessage('')
    try {
      const response = await fetch(`/api/osiris/query?capability=geosearch&q=${encodeURIComponent(value)}`)
      if (!response.ok) throw new Error('LOCATION NOT FOUND')
      const results = await response.json()
      const result = results?.[0]
      if (!result) throw new Error('LOCATION NOT FOUND')
      mapRef.current?.flyTo({ center: [Number(result.lon), Number(result.lat)], zoom: 7, duration: 1100 })
      setSearchMessage(`${result.display_name || value}`.slice(0, 88))
    } catch (error) {
      setSearchMessage(error.message || 'SEARCH UNAVAILABLE')
    } finally {
      setSearching(false)
    }
  }

  return (
    <section className="globe-section" aria-label="Global live camera globe">
      <div className="globe-heading">
        <div>
          <span className="world-kicker"><span className="status-dot" /> GLOBAL NAVIGATION / PUBLIC SOURCES</span>
          <h3>LIVE WORLD GLOBE</h3>
        </div>
        <span>{features.length ? `${features.length} CAMERA MARKERS` : 'CAMERA INDEX LOADING'} · {loading ? 'REFRESHING' : 'PAN / ZOOM / SELECT'}</span>
      </div>
      <div className="globe-toolbar">
        <form onSubmit={searchPlace} className="globe-search">
          <Search size={13} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="JUMP TO COUNTRY OR CITY" aria-label="Jump to country or city" />
          <button type="submit" disabled={searching}>{searching ? '...' : 'GO'}</button>
        </form>
        <button className="globe-tool-button" type="button" onClick={locate} title="Reset world view"><LocateFixed size={13} /> WORLD</button>
        <button className="globe-tool-button" type="button" onClick={onRefresh} disabled={loading} title="Refresh public camera sources"><ZoomIn size={13} /> REFRESH FEEDS</button>
      </div>
      {searchMessage && <div className="globe-search-message">{searchMessage}</div>}
      <div className="globe-map" ref={containerRef} />
      <div className="globe-legend"><span><i className="globe-legend-dot" /> PUBLIC / AUTHORIZED CCTV</span><span>FEED CONTENT IS UNTRUSTED EVIDENCE</span></div>
    </section>
  )
}

function escapeHtml(value) {
  return String(value || '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;',
  }[character]))
}

export default WorldGlobe