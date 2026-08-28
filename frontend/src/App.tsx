import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

function App() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)

  useEffect(() => {
    if (map.current || !mapContainer.current) return

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      // OpenFreeMap positron (light/clean) style — free, no API key
      style: 'https://tiles.openfreemap.org/styles/positron',
      center: [118.0, -3.0], // Center of Indonesia
      zoom: 5,
    })

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right')

    return () => {
      map.current?.remove()
      map.current = null
    }
  }, [])

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="flex items-center justify-between bg-white px-6 py-3 shadow-sm">
        <h1 className="text-xl font-bold text-green-800">
          🌾 TaniScope
        </h1>
        <nav className="flex gap-2">
          {['Coffee', 'Cocoa', 'Sugarcane'].map((crop) => (
            <button
              key={crop}
              className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-green-100 hover:text-green-800"
            >
              {crop}
            </button>
          ))}
        </nav>
      </header>

      {/* Map */}
      <div ref={mapContainer} className="flex-1" />

      {/* Status bar */}
      <footer className="bg-gray-50 px-6 py-2 text-xs text-gray-500">
        TaniScope MVP — 3 crops × 3 provinces | Data: HDX, SoilGrids, WorldClim, SRTM, OSM
      </footer>
    </div>
  )
}

export default App
